#!/usr/bin/env python3
# coding: utf-8
"""
=============================================================================
Pipeline Avançada de Detecção de Regimes em BTC/USDT
=============================================================================

Implementação rigorosa baseada em Marcos López de Prado:
  - "Advances in Financial Machine Learning" (AFML, 2018)
  - "Machine Learning for Asset Managers" (MLAM, 2020)

DIFERENÇAS em relação ao pipeline básico (marcos.py):
  1. CPCV (Combinatorial Purged Cross-Validation) — obrigatório.
     Gera C(N,k) caminhos combinatórios de treino/teste, simulando
     múltiplos cenários para garantir que o resultado não é fruto do acaso.
  2. Feature Selection via MDA + CPCV — elimina features sem poder
     preditivo out-of-sample antes do modelo final.
  3. Filtro Savitzky-Golay CAUSAL em todos os indicadores de momentum
     e volatilidade — substitui médias móveis, eliminando look-ahead.
  4. Arquitetura extensível de features (BaseFeature + FeatureRegistry) —
     features tick-level (Amihud, Hasbrouck, TWAP, etc.) são stubs que
     se ativam automaticamente quando os dados estiverem disponíveis.
  5. Deflated Sharpe Ratio (DSR) — ajusta para múltiplos testes.
  6. 8 plots diagnósticos + 9 relatórios .txt em save_point_advanced/.

ANTI-LEAKAGE (checklist embutida no código):
  ✓ Dollar bar threshold calibrado nos primeiros 30 dias APENAS
  ✓ SavGol CAUSAL (pos=window-1), primeiras window-1 barras = NaN
  ✓ Fear & Greed: valor do dia ANTERIOR (lag 1 dia)
  ✓ Features rolling usam APENAS dados passados
  ✓ CPCV com purging de spans [t0,t1] sobrepostos + embargo pós-teste
  ✓ Feature selection feita via CPCV (tudo out-of-sample)
  ✓ Meta-labeling treinado APENAS no split temporal de treino
  ✓ Nenhum filtro centrado (SavGol centrado REMOVIDO)

Autor: Pipeline científica para Transfero Research.
"""

import os
import warnings
import joblib
from typing import List, Tuple, Optional, Dict, Any, Callable
from abc import ABC, abstractmethod
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # backend não-interativo para salvar PNGs
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats as sp_stats
from scipy.signal import savgol_coeffs
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

try:
    from statsmodels.tsa.stattools import adfuller

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    warnings.warn(
        "statsmodels não encontrado — teste ADF será ignorado. "
        "Instale com: pip install statsmodels>=0.13.0"
    )

# ===========================================================================
# CONSTANTES GLOBAIS — todos os hiperparâmetros centralizados aqui
# ===========================================================================
DEFAULT_CONFIG: Dict[str, Any] = {
    # Seed
    "rng_seed": 42,
    # Dados
    "data_dir": "data",
    "save_dir": "save_point_advanced",
    # Dollar bars (Cap. 2 AFML)
    "dollar_bar_calibration_days": 30,   # dias para calibrar threshold (anti-leakage)
    "dollar_bars_per_day": 20,           # ~20 barras/dia → barras grossas, máxima resolução exógena
    # FFD (Cap. 5 AFML)
    "ffd_d": 0.4,                        # grau de diferenciação fracionária
    "ffd_threshold": 1e-4,               # truncamento de pesos FFD
    # Microestrutura (Cap. 18 AFML)
    "vpin_n_buckets": 50,                # buckets para VPIN (~1 dia)
    "kyle_window": 20,                   # janela para Kyle Lambda
    "roll_window": 20,                   # janela para Roll Spread
    "lz_window": 100,                    # janela para entropia Lempel-Ziv
    # Savitzky-Golay CAUSAL
    "savgol_window": 21,                 # janela do filtro (deve ser ímpar)
    "savgol_polyorder": 3,               # ordem do polinômio local
    # RSI removed (2026-03-25): linear derivative of price, no value beyond SavGol derivatives
    # Funding Rate
    "funding_rate_zscore_window": 50,    # janela rolling para z-score
    # Momentum Residual
    "mom_residual_ols_window": 100,      # janela OLS rolling para beta
    # DXY Spread
    "dxy_beta_window": 50,              # janela rolling para beta BTC-DXY
    # Triple barrier (Cap. 3 AFML)
    "vol_lookback": 20,                  # janela EWM para volatilidade
    "pt_multiplier": 2.0,               # profit-take = pt × σ
    "sl_multiplier": 2.0,               # stop-loss = sl × σ
    "max_holding_bars": 50,             # barreira vertical (~1 dia)
    # CPCV (Cap. 12 AFML / MLAM)
    "cpcv_n_groups": 6,                  # N grupos contíguos
    "cpcv_k_test": 2,                    # k grupos como teste → C(6,2)=15 paths
    "cpcv_purge_pct": 0.01,             # 1% de purging
    "cpcv_embargo_pct": 0.01,           # 1% de embargo
    # Feature selection
    "mda_n_repeats": 5,                  # repetições da permutação MDA
    "mda_selection_threshold": 0.0,      # MDA > 0 para manter feature
    # Random Forest
    "rf_n_estimators": 500,
    "rf_max_depth": 6,
    "rf_min_samples_leaf": 50,
    # Meta-labeling
    "train_ratio": 0.80,                # split temporal 80/20
    # Trading fees (Binance USDT-M Futures)
    "fee_maker": 0.0090 / 100,          # 0.0090% — limit order
    "fee_taker": 0.0270 / 100,          # 0.0270% — market order
    # "pessimistic" = taker em ambas as pontas (padrão, conservador)
    # "optimistic"  = taker na entrada, maker na saída
    "fee_mode": "pessimistic",
}

LIMITE_DECISORIO = 0.52 # threshold para calibrar precisão/recall

# ===========================================================================
# 1. DOLLAR BARS — Cap. 2 AFML
# ===========================================================================
class DollarBarBuilder:
    """
    Converte barras de tempo (1 minuto) em Dollar Bars.

    ── Por que barras de dólar? ──────────────────────────────────────────
    Barras de tempo amostram em intervalos fixos de relógio, causando:
      • Sobre-amostragem em períodos calmos (ruído inútil).
      • Sub-amostragem em períodos voláteis (perda de informação).

    Dollar bars amostram quando o volume financeiro acumulado (preço × volume)
    atinge um limiar fixo. Cada barra carrega a mesma "quantidade de informação"
    medida em dólares — retornos se aproximam de IID (AFML, Teorema 2.1).

    ── Implementação vetorizada ──────────────────────────────────────────
    O(N) cumsum + O(K log N) searchsorted, onde K ≪ N.
    """

    def __init__(self, calibration_days: int = 30, bars_per_day: int = 50):
        self.threshold: Optional[float] = None
        self.calibration_days = calibration_days
        self.bars_per_day = bars_per_day

    def calibrate_threshold(self, df: pd.DataFrame) -> float:
        """
        Calibra o limiar usando os primeiros N dias APENAS (anti-leakage).
        threshold = mediana(dollar_volume_diário) / bars_per_day
        """
        tmp = df.copy()
        tmp["date"] = pd.to_datetime(tmp["timestamp"]).dt.date
        tmp["dollar_vol"] = (
            (tmp["high"] + tmp["low"] + tmp["close"]) / 3.0 * tmp["volume"]
        )
        daily = tmp.groupby("date")["dollar_vol"].sum()
        daily_cal = daily.iloc[: self.calibration_days]
        self.threshold = daily_cal.median() / self.bars_per_day
        return self.threshold

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte 1-min bars → Dollar Bars.

        Retorna DataFrame com colunas:
        [timestamp, open, high, low, close, volume, dollar_volume, vwap, tick_count]
        """
        if self.threshold is None:
            self.calibrate_threshold(df)

        typical_price = (
            df["high"].values + df["low"].values + df["close"].values
        ) / 3.0
        volume = df["volume"].values
        dollar_vol = typical_price * volume
        cum_dollar = np.cumsum(dollar_vol)

        n_bars_max = int(cum_dollar[-1] / self.threshold) + 1
        thresholds = np.arange(1, n_bars_max + 1) * self.threshold
        boundary_indices = np.searchsorted(cum_dollar, thresholds, side="right")
        boundary_indices = np.unique(boundary_indices)
        boundary_indices = boundary_indices[boundary_indices < len(df)]
        boundary_indices = boundary_indices[boundary_indices > 0]

        bar_id = np.zeros(len(df), dtype=np.int64)
        prev = 0
        for i, bnd in enumerate(boundary_indices):
            bar_id[prev:bnd] = i
            prev = bnd
        bar_id[prev:] = -1

        tmp = pd.DataFrame({
            "bar_id": bar_id,
            "timestamp": df["timestamp"].values,
            "open": df["open"].values,
            "high": df["high"].values,
            "low": df["low"].values,
            "close": df["close"].values,
            "volume": volume,
            "dollar_vol": dollar_vol,
        })
        tmp = tmp[tmp["bar_id"] >= 0]

        bars = tmp.groupby("bar_id").agg(
            timestamp=("timestamp", "first"),
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            dollar_volume=("dollar_vol", "sum"),
            tick_count=("bar_id", "count"),
        )
        bars["vwap"] = bars["dollar_volume"] / bars["volume"].replace(0, np.nan)
        bars = bars.reset_index(drop=True)
        return bars


# ===========================================================================
# 2. ARQUITETURA DE FEATURES — BaseFeature + Subclasses
# ===========================================================================
class BaseFeature(ABC):
    """
    Classe base abstrata para features extensíveis.

    Cada feature encapsula:
      - name: identificador único (usado como nome da coluna)
      - required_columns: colunas que DEVEM existir no DataFrame de entrada
      - compute(): lógica de cálculo, retorna pd.Series alinhada ao index

    Para adicionar uma feature nova (ex: dados tick-level futuros):
      1. Crie uma subclasse de BaseFeature
      2. Defina required_columns com as colunas necessárias
      3. Implemente compute()
      4. Registre no FeatureRegistry

    Se as colunas necessárias não existirem no DataFrame, a feature é
    silenciosamente ignorada — permitindo que o pipeline rode com dados
    parciais (ex: apenas OHLCV + Fear & Greed).
    """

    name: str = ""
    required_columns: List[str] = []

    def is_available(self, df: pd.DataFrame) -> bool:
        """Verifica se todas as colunas necessárias existem no DataFrame."""
        return all(col in df.columns for col in self.required_columns)

    @abstractmethod
    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        """Calcula a feature e retorna uma Series alinhada ao df.index."""
        ...


class MultiFeature(BaseFeature):
    """
    Variante que retorna MÚLTIPLAS colunas (ex: ret_5, ret_20, vol_20).
    O método compute_multi() retorna um dict de {nome: Series}.
    """

    @abstractmethod
    def compute_multi(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> Dict[str, pd.Series]:
        """Retorna dict de {feature_name: Series}."""
        ...

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        # Não usado diretamente — FeatureRegistry chama compute_multi()
        raise NotImplementedError("Use compute_multi() para MultiFeature")


# ---------------------------------------------------------------------------
# 2a. FFD — Diferenciação Fracionária (Cap. 5 AFML)
# ---------------------------------------------------------------------------
class FFDFeature(BaseFeature):
    """
    Preço fracionariamente diferenciado (FFD, Fixed-Width Window).

    ── Teoria ──────────────────────────────────────────────────────────
    A diferenciação inteira (d=1) remove TODA a memória: retornos log
    "esquecem" suportes e resistências. A diferenciação fracionária
    (0 < d < 1) aplica o operador (1-B)^d, preservando correlação com
    os níveis originais enquanto atinge estacionaridade.

    Com d=0.4, o resultado tipicamente:
      • Passa no teste ADF (p < 0.05)
      • Mantém correlação > 0.9 com os preços originais
    """

    name = "ffd_close"
    required_columns = ["close"]

    @staticmethod
    def _get_weights(d: float, threshold: float) -> np.ndarray:
        """
        Pesos FFD: w_0=1, w_k = -w_{k-1} × (d-k+1)/k.
        Trunca quando |w_k| < threshold.
        """
        weights = [1.0]
        k = 1
        while True:
            w_k = -weights[-1] * (d - k + 1) / k
            if abs(w_k) < threshold:
                break
            weights.append(w_k)
            k += 1
        return np.array(weights[::-1])

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        d = config.get("ffd_d", 0.4)
        threshold = config.get("ffd_threshold", 1e-4)
        weights = self._get_weights(d, threshold)
        width = len(weights)
        values = df["close"].values.astype(np.float64)
        n = len(values)

        result = np.full(n, np.nan)
        for i in range(width - 1, n):
            window = values[i - width + 1: i + 1]
            result[i] = np.dot(weights, window)

        ffd_series = pd.Series(result, index=df.index, name=self.name)

        # Validação ADF
        if HAS_STATSMODELS:
            clean = ffd_series.dropna()
            if len(clean) > 100:
                adf_stat, adf_pvalue, *_ = adfuller(clean.values, maxlag=1)
                status = "ESTACIONÁRIA" if adf_pvalue < 0.05 else "NÃO ESTACIONÁRIA"
                print(
                    f"    [FFD] d={d:.2f}, janela={width}, "
                    f"ADF stat={adf_stat:.4f}, p={adf_pvalue:.6f} ({status})"
                )
        return ffd_series


# ---------------------------------------------------------------------------
# 2b. VPIN — Volume-Synchronized Probability of Informed Trading (Cap. 18)
# ---------------------------------------------------------------------------
class VPINFeature(BaseFeature):
    """
    VPIN mede a "toxicidade" do fluxo de ordens.

    Quando compradores informados dominam, VPIN sobe — sinalizando risco
    de crash ou movimento abrupto ANTES que aconteça. Historicamente,
    VPIN alto precedeu flash crashes em BTC e ETH.

    ── Algoritmo (Bulk Volume Classification) ────────────────────────
    1. Classificar volume como buy/sell sem dados de tick:
       Z = (close - open) / σ, buy_pct = Φ(Z)
    2. Preencher buckets de volume fixo sequencialmente
    3. VPIN = média(|V_buy - V_sell| / V_bucket) sobre últimos N buckets
    """

    name = "vpin"
    required_columns = ["close", "open", "volume"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        n_buckets = config.get("vpin_n_buckets", 50)
        close = df["close"].values.astype(np.float64)
        open_ = df["open"].values.astype(np.float64)
        volume = df["volume"].values.astype(np.float64)

        dp = close - open_
        sigma = np.nanstd(dp)
        if sigma < 1e-12:
            sigma = 1.0
        z = dp / sigma
        buy_pct = sp_stats.norm.cdf(z)
        buy_vol = volume * buy_pct
        sell_vol = volume * (1.0 - buy_pct)

        total_vol = np.nansum(volume)
        bucket_size = total_vol / max(n_buckets * 10, 1)

        n_bars = len(df)
        vpin_values = np.full(n_bars, np.nan)
        bucket_buy = 0.0
        bucket_sell = 0.0
        bucket_total = 0.0
        imb_list: List[float] = []

        for i in range(n_bars):
            rb, rs = buy_vol[i], sell_vol[i]
            while rb + rs > 1e-12:
                space = bucket_size - bucket_total
                fill = min(rb + rs, space)
                if rb + rs > 1e-12:
                    ratio = rb / (rb + rs)
                else:
                    ratio = 0.5
                fb = fill * ratio
                fs = fill * (1 - ratio)
                bucket_buy += fb
                bucket_sell += fs
                bucket_total += fill
                rb -= fb
                rs -= fs
                if bucket_total >= bucket_size - 1e-12:
                    imb_list.append(abs(bucket_buy - bucket_sell) / bucket_size)
                    bucket_buy = 0.0
                    bucket_sell = 0.0
                    bucket_total = 0.0

            if len(imb_list) >= n_buckets:
                vpin_values[i] = np.mean(imb_list[-n_buckets:])

        return pd.Series(vpin_values, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2c. Kyle Lambda — Impacto de Preço (Cap. 18 AFML)
# ---------------------------------------------------------------------------
class KyleLambdaFeature(BaseFeature):
    """
    Lambda de Kyle — medida de iliquidez.

    Kyle (1985): Δp = λ × signed_volume + ε
    λ alto → cada unidade de volume move mais o preço → mercado ilíquido.
    Em momentos de stress, λ explode — indicador antecedente de slippage.

    Implementação: regressão rolling OLS de |Δp| sobre |signed_volume|.
    """

    name = "kyle_lambda"
    required_columns = ["close", "open", "volume"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        w = config.get("kyle_window", 20)
        close = df["close"].values.astype(np.float64)
        open_ = df["open"].values.astype(np.float64)
        volume = df["volume"].values.astype(np.float64)

        dp = np.abs(close - np.roll(close, 1))
        dp[0] = np.nan
        sign = np.sign(close - open_)
        signed_vol = np.abs(volume * sign)

        n = len(df)
        kyle = np.full(n, np.nan)
        for i in range(w, n):
            y = dp[i - w + 1: i + 1]
            x = signed_vol[i - w + 1: i + 1]
            mask = ~(np.isnan(y) | np.isnan(x))
            if mask.sum() < w // 2:
                continue
            y_c, x_c = y[mask], x[mask]
            if np.std(x_c) < 1e-12:
                continue
            kyle[i] = np.cov(y_c, x_c)[0, 1] / np.var(x_c)

        return pd.Series(kyle, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2d. Roll Spread — Spread Efetivo Estimado (Cap. 18 AFML)
# ---------------------------------------------------------------------------
class RollSpreadFeature(BaseFeature):
    """
    Estimador de Roll (1984) para o spread bid-ask.

    spread = 2 × √(-cov(Δp_t, Δp_{t-1}))  quando cov < 0
           = 0                               quando cov ≥ 0

    O bounce entre bid e ask cria autocorrelação negativa nos retornos.
    Quanto maior o spread, mais negativa a covariância.
    """

    name = "roll_spread"
    required_columns = ["close"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        w = config.get("roll_window", 20)
        close = df["close"].values.astype(np.float64)
        dp = np.diff(close, prepend=np.nan)

        n = len(df)
        roll = np.full(n, np.nan)
        for i in range(w + 1, n):
            dp_t = dp[i - w + 1: i + 1]
            dp_t1 = dp[i - w: i]
            mask = ~(np.isnan(dp_t) | np.isnan(dp_t1))
            if mask.sum() < w // 2:
                continue
            cov_val = np.cov(dp_t[mask], dp_t1[mask])[0, 1]
            roll[i] = 2.0 * np.sqrt(-cov_val) if cov_val < 0 else 0.0

        return pd.Series(roll, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2e. Entropia Lempel-Ziv (Cap. 18 AFML)
# ---------------------------------------------------------------------------
class LempelZivFeature(BaseFeature):
    """
    Complexidade LZ76 do fluxo de ordens.

    • Entropia ALTA → retornos imprevisíveis (mercado eficiente)
    • Entropia BAIXA → padrões repetitivos → tendência forte ou manipulação

    Binariza retornos (1=positivo, 0=negativo) e aplica LZ76 em janela rolling.
    """

    name = "lz_entropy"
    required_columns = ["close"]

    @staticmethod
    def _lz_complexity(binary_string: str) -> float:
        """Complexidade LZ76 normalizada por n/log2(n)."""
        n = len(binary_string)
        if n == 0:
            return 0.0
        i = 0
        complexity = 1
        prefix_len = 1
        while prefix_len + i < n:
            l_max = 0
            for j in range(i):
                l = 0
                while (
                    prefix_len + i + l < n
                    and binary_string[j + l] == binary_string[prefix_len + i + l]
                ):
                    l += 1
                    if j + l >= prefix_len + i:
                        break
                l_max = max(l_max, l)
            if prefix_len + i + l_max >= n:
                break
            i += max(l_max, 1)
            if l_max == 0:
                complexity += 1
                prefix_len += i
                i = 0
        norm = n / np.log2(max(n, 2))
        return complexity / norm

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        w = config.get("lz_window", 100)
        close = df["close"].values.astype(np.float64)
        ret = np.diff(close, prepend=np.nan)
        binary = np.where(ret > 0, "1", "0")

        n = len(df)
        lz = np.full(n, np.nan)
        for i in range(w, n):
            window_str = "".join(binary[i - w + 1: i + 1])
            lz[i] = self._lz_complexity(window_str)

        return pd.Series(lz, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2f. RSI — Relative Strength Index
# ---------------------------------------------------------------------------
class RSIFeature(BaseFeature):
    """
    RSI de Wilder — mede persistência direcional.

    RSI = 100 - 100 / (1 + RS)
    RS = EWM(ganhos) / EWM(perdas)

    Complementa momentum (ret_5, ret_20) por medir a RAZÃO entre dias
    de alta e baixa, não apenas o retorno acumulado.
    """

    name = "rsi"
    required_columns = ["close"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        period = config.get("rsi_period", 14)
        close = df["close"].astype(np.float64)
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(span=period, min_periods=period).mean()
        avg_loss = loss.ewm(span=period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - 100.0 / (1.0 + rs)
        return pd.Series(rsi.values, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2g. Fear & Greed — Sentimento Macro (Exógena)
# ---------------------------------------------------------------------------
class FearGreedFeature(MultiFeature):
    """
    Fear & Greed Index — variação diária + z-scores em múltiplas janelas.

    Produz 4 features:
      • fear_greed_chg:       diferença diária do índice (diff)
      • fear_greed_zscore_5:  z-score rolling 5 dias (regime de curto prazo)
      • fear_greed_zscore_20: z-score rolling 20 dias (regime de médio prazo)
      • fear_greed_zscore_50: z-score rolling 50 dias (regime de longo prazo)

    O diff captura MUDANÇAS no sentimento, os z-scores capturam o NÍVEL
    relativo ao passado recente — informações complementares.

    Anti-leakage: lag de 1 dia (o índice é publicado ao final do dia).
    Requer que fng_df seja passado via config["_fng_df"] pelo FeatureRegistry.
    """

    name = "fear_greed"
    required_columns = ["timestamp"]  # precisa de timestamp para merge

    def compute_multi(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> Dict[str, pd.Series]:
        fng_df = config.get("_fng_df", None)
        nan_series = pd.Series(np.nan, index=df.index)
        if fng_df is None or len(fng_df) == 0:
            return {
                "fear_greed_chg": nan_series,
                "fear_greed_zscore_5": nan_series,
                "fear_greed_zscore_20": nan_series,
                "fear_greed_zscore_50": nan_series,
            }

        # --- Preparar série diária ---
        fng = fng_df.copy()
        fng["timestamp"] = pd.to_datetime(fng["timestamp"], format="ISO8601")
        if fng["timestamp"].dt.tz is None:
            fng["timestamp"] = fng["timestamp"].dt.tz_localize("UTC")
        fng = fng.sort_values("timestamp").drop_duplicates("timestamp")
        fng["date"] = fng["timestamp"].dt.date

        # Diff e z-scores computados na escala DIÁRIA (1 valor/dia)
        fng["fear_greed_chg"] = fng["fear_greed"].diff()
        for w in [5, 20, 50]:
            roll_mean = fng["fear_greed"].rolling(w, min_periods=w).mean()
            roll_std = fng["fear_greed"].rolling(w, min_periods=w).std()
            fng[f"fear_greed_zscore_{w}"] = (
                (fng["fear_greed"] - roll_mean) / roll_std.replace(0, np.nan)
            )

        # --- Mapear para dollar bars com lag 1 dia (anti-leakage) ---
        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("UTC")
        date_prev = (ts - pd.Timedelta(days=1)).dt.date

        results = {}
        for col in ["fear_greed_chg", "fear_greed_zscore_5",
                     "fear_greed_zscore_20", "fear_greed_zscore_50"]:
            col_map = fng.set_index("date")[col].to_dict()
            mapped = date_prev.map(col_map).ffill()
            results[col] = pd.Series(mapped.values, index=df.index, name=col)

        return results


# ---------------------------------------------------------------------------
# 2h. SavGol Momentum & Volatilidade — SUBSTITUI médias móveis
# ---------------------------------------------------------------------------
class SavGolMomentumFeature(MultiFeature):
    """
    SavGol derivative-based features: velocity, acceleration, curvature.

    Uses analytical derivatives from the SavGol polynomial (deriv=1,2)
    instead of pct_change(N), which was shown to produce artifact SR on
    random walks (T8 null model test, 2026-03-25).

    ── Why derivatives instead of pct_change? ────────────────────────
    pct_change(20) on SavGol-smoothed prices produces SR~0.19 on pure
    random walks. The SavGol polynomial's analytical derivative captures
    the *geometry* of the local price curve, not just direction.

    Produces 5 features:
      • sg_velocity_51: velocity at scale 51 (re-added for interaction test)
      • sg_acceleration_5: acceleration at scale 5 (2nd derivative, short-scale)
      • volatility_10, volatility_20, volatility_50: realized vol in 3 scales

    SavGol derivatives (sg_velocity, sg_acceleration, sg_curvature,
    sg_accel_51) removed 2026-03-25: confirmed ARTIFACT by
    feature_null_model.py (SR_real ≈ SR_rw for all derivatives).

    sg_velocity_51 re-added 2026-03-26 for empirical A/B test:
    ARTIFACT marginally (p_rw=0.325, p_shuf=0.360), but may provide
    useful context via interaction with genuine features. See genuinas_vs_artefatos.md.

    sg_acceleration_5 added 2026-03-26: short-scale 2nd derivative to
    capture local curvature (regime transitions). Scale 5 chosen to
    minimize correlation with sg_velocity_51 (scale 51). Normalized by
    price and vol_10. Let correlation filter + MDA decide if it adds value.
    """

    name = "savgol_momentum"
    required_columns = ["close", "volume"]

    def compute_multi(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> Dict[str, pd.Series]:
        from utils.savgol import savgol_causal, savgol_causal_deriv

        sg_window = config.get("savgol_window", 21)
        sg_poly = config.get("savgol_polyorder", 3)

        close_raw = df["close"].values.astype(np.float64)

        # Smoothed close for volatility calculation
        close_sg = savgol_causal(close_raw, sg_window, sg_poly)
        close_series = pd.Series(close_sg, index=df.index)
        ret = close_series.pct_change()

        # SavGol derivatives (sg_velocity, sg_acceleration, sg_curvature,
        # sg_accel_51) removed 2026-03-25: confirmed ARTIFACT.
        # sg_velocity_51 re-added 2026-03-26 for interaction A/B test.

        results = {}

        # sg_velocity_51: z-scored velocity at scale 51
        # ARTIFACT marginally (p_rw=0.325) but kept for empirical test
        velocity_51 = savgol_causal_deriv(close_raw, 51, sg_poly, deriv=1)
        price_safe = np.where(close_raw > 1e-12, close_raw, np.nan)
        vel_51_norm = velocity_51 / price_safe
        vol_50 = ret.rolling(50, min_periods=50).std().values
        vol_50_safe = np.where(vol_50 > 1e-12, vol_50, np.nan)
        results["sg_velocity_51"] = pd.Series(
            vel_51_norm / vol_50_safe, index=df.index, name="sg_velocity_51")

        # sg_acceleration_5: analytical 2nd derivative at scale 5
        # Short-scale acceleration: low correlation with sg_velocity_51
        # (different scale + different derivative order)
        accel_5 = savgol_causal_deriv(close_raw, 5, sg_poly, deriv=2)
        accel_5_norm = accel_5 / price_safe
        vol_10 = ret.rolling(10, min_periods=10).std().values
        vol_10_safe = np.where(vol_10 > 1e-12, vol_10, np.nan)
        results["sg_acceleration_5"] = pd.Series(
            accel_5_norm / vol_10_safe, index=df.index, name="sg_acceleration_5")

        # Volatility at 3 scales (not artifacts — depend on return distribution)
        for w in [10, 20, 50]:
            v = ret.rolling(w, min_periods=w).std()
            results[f"volatility_{w}"] = pd.Series(v.values, index=df.index, name=f"volatility_{w}")

        return results


# ---------------------------------------------------------------------------
# 2i-2l. STUBS para Features Tick-Level (ativam quando dados disponíveis)
# ---------------------------------------------------------------------------
class AmihudLambdaFeature(BaseFeature):
    """
    Lambda de Amihud — complementa Kyle Lambda.

    Mede o impacto do dólar transacionado no log-preço:
      ILLIQ = (1/N) × Σ |r_t| / dollar_volume_t

    REQUER dados tick-level com colunas:
      - tick_return: retorno tick-a-tick
      - tick_dollar_volume: volume em dólares tick-a-tick

    Quando esses dados estiverem disponíveis, basta adicioná-los ao
    DataFrame antes de chamar o FeatureRegistry.
    """

    name = "amihud_lambda"
    required_columns = ["tick_return", "tick_dollar_volume"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        window = config.get("amihud_window", 20)
        abs_ret = df["tick_return"].abs()
        dvol = df["tick_dollar_volume"].replace(0, np.nan)
        illiq = (abs_ret / dvol).rolling(window, min_periods=window).mean()
        return pd.Series(illiq.values, index=df.index, name=self.name)


class HasbrouckLambdaFeature(BaseFeature):
    """
    Lambda de Hasbrouck — custo efetivo de execução.

    Mede a relação entre variação de preço e raiz do volume:
      Δp = λ_H × sign(trade) × √(volume) + ε

    REQUER dados tick-level com colunas:
      - tick_price_change: variação de preço tick-a-tick
      - tick_trade_sign: +1 (buy) ou -1 (sell)
      - tick_volume: volume do tick
    """

    name = "hasbrouck_lambda"
    required_columns = ["tick_price_change", "tick_trade_sign", "tick_volume"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        window = config.get("hasbrouck_window", 20)
        dp = df["tick_price_change"].values.astype(np.float64)
        sign_vol = (
            df["tick_trade_sign"].values * np.sqrt(df["tick_volume"].values)
        )
        n = len(df)
        result = np.full(n, np.nan)
        for i in range(window, n):
            y = dp[i - window + 1: i + 1]
            x = sign_vol[i - window + 1: i + 1]
            mask = ~(np.isnan(y) | np.isnan(x))
            if mask.sum() < window // 2:
                continue
            y_c, x_c = y[mask], x[mask]
            if np.std(x_c) < 1e-12:
                continue
            result[i] = np.cov(y_c, x_c)[0, 1] / np.var(x_c)
        return pd.Series(result, index=df.index, name=self.name)


class OrderSizeDistFeature(BaseFeature):
    """
    Distribuição de tamanho de ordens — detecta GUI traders vs algoritmos.

    Monitora a frequência de ordens com "tamanhos redondos" (1.0, 10, 50 BTC).
    Traders humanos tendem a usar tamanhos redondos; algoritmos randomizam.

    REQUER dados tick-level com coluna:
      - tick_order_size: tamanho de cada ordem individual
    """

    name = "round_order_ratio"
    required_columns = ["tick_order_size"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        window = config.get("order_dist_window", 50)
        sizes = df["tick_order_size"].values.astype(np.float64)
        is_round = (np.abs(sizes * 10 - np.round(sizes * 10)) < 0.01).astype(float)
        ratio = pd.Series(is_round).rolling(window, min_periods=window).mean()
        return pd.Series(ratio.values, index=df.index, name=self.name)


class TWAPSignatureFeature(BaseFeature):
    """
    Assinatura de algoritmos TWAP.

    Identifica execuções em intervalos de tempo fixos (ex: início de cada
    minuto) que indicam fluxos institucionais de grande escala.

    REQUER dados tick-level com colunas:
      - tick_timestamp: timestamp de cada tick
      - tick_volume: volume de cada tick
    """

    name = "twap_signature"
    required_columns = ["tick_timestamp", "tick_volume"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        window = config.get("twap_window", 60)
        ts = pd.to_datetime(df["tick_timestamp"])
        is_start = ts.dt.second < 5
        vol = df["tick_volume"].values.astype(np.float64)
        start_vol = np.where(is_start, vol, 0.0)
        ratio = (
            pd.Series(start_vol).rolling(window, min_periods=window).sum()
            / pd.Series(vol).rolling(window, min_periods=window).sum().replace(0, np.nan)
        )
        return pd.Series(ratio.values, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2m. FUNDING RATE Z-SCORE — Posicionamento no mercado derivativo
# ---------------------------------------------------------------------------
class FundingRateFeature(BaseFeature):
    """
    Z-score do Funding Rate — desequilíbrio de posicionamento derivativo.

    O funding rate é o preço que longs pagam a shorts (ou vice-versa)
    em contratos perpétuos. Mede diretamente o desequilíbrio de
    posicionamento do mercado:

      • Funding positivo alto → muitos longs alavancados → mercado
        "esticado" → vulnerável a cascata de liquidações
      • Funding negativo extremo → muitos shorts → short squeeze potencial

    Z-score normaliza sobre janela rolling (default 50 barras):
      z_t = (FR_t − μ_FR) / σ_FR

    Fonte: data/funding_rate.csv via config["_funding_rate_df"].
    Anti-leakage: usa período anterior (ts − 8h, floor to 8h boundary).
    Se CSV não existe → silenciosamente retorna NaN (será pulado).
    """

    name = "funding_rate_zscore"
    required_columns = ["timestamp"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        fr_df = config.get("_funding_rate_df", None)
        if fr_df is None or len(fr_df) == 0:
            return pd.Series(np.nan, index=df.index, name=self.name)

        fr = fr_df.copy()
        fr["timestamp"] = pd.to_datetime(fr["timestamp"], format="ISO8601")
        if fr["timestamp"].dt.tz is None:
            fr["timestamp"] = fr["timestamp"].dt.tz_localize("UTC")
        fr["date_hour"] = fr["timestamp"].dt.floor("8h")
        fr_map = fr.set_index("date_hour")["funding_rate"].to_dict()

        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("UTC")
        # Anti-leakage: usar período anterior
        date_hour_prev = (ts - pd.Timedelta(hours=8)).dt.floor("8h")
        raw_fr = date_hour_prev.map(fr_map).ffill()

        window = config.get("funding_rate_zscore_window", 50)
        raw_series = pd.Series(raw_fr.values, index=df.index, dtype=float)
        mean_r = raw_series.rolling(window, min_periods=window).mean()
        std_r = raw_series.rolling(window, min_periods=window).std()
        zscore = (raw_series - mean_r) / std_r.replace(0, np.nan)

        return pd.Series(zscore.values, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2n. T-STATISTIC — Signal-to-Noise Ratio do Momentum
# ---------------------------------------------------------------------------
class TStatFeature(MultiFeature):
    """
    T-statistic do momentum em múltiplas janelas.

    Mede se o momentum observado é estatisticamente significativo:
      tstat_n = mean(ret_n) / (std(ret_n) / √n)

    Interpretação:
      • |tstat| > 2.0 → momentum é "real" com 95% de confiança
      • |tstat| ≈ 0   → retornos são indistinguíveis de ruído

    Produz 3 features: tstat_10, tstat_20, tstat_50.
    Calculado diretamente do close — sem dependência externa.
    """

    name = "tstat_momentum"
    required_columns = ["close"]

    def compute_multi(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> Dict[str, pd.Series]:
        close = pd.Series(df["close"].values.astype(np.float64), index=df.index)
        ret = close.pct_change()

        results = {}
        for n in [10, 20, 50]:
            mean_n = ret.rolling(n, min_periods=n).mean()
            std_n = ret.rolling(n, min_periods=n).std()
            tstat = mean_n / (std_n / np.sqrt(n))
            results[f"tstat_{n}"] = pd.Series(
                tstat.values, index=df.index, name=f"tstat_{n}"
            )

        return results


# ---------------------------------------------------------------------------
# 2o. MOMENTUM RESIDUAL — Informação ortogonal entre horizontes
# ---------------------------------------------------------------------------
class MomentumResidualFeature(BaseFeature):
    """
    Scale divergence — captures orthogonal information between SavGol scales.

    Produz 1 feature:
      scale_divergence = sg_velocity_51 - beta * sg_velocity_21

    When short-scale and long-scale velocity disagree, regime is changing.
    Replaces the old pct_change-based residual (falsified by T8).
    """

    name = "scale_divergence"
    required_columns = ["close"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        from utils.savgol import savgol_causal_deriv

        close_raw = df["close"].values.astype(np.float64)
        sg_poly = config.get("savgol_polyorder", 3)

        vel_21 = savgol_causal_deriv(close_raw, 21, sg_poly, deriv=1)
        vel_51 = savgol_causal_deriv(close_raw, 51, sg_poly, deriv=1)

        # Normalize by price
        price_safe = np.where(close_raw > 1e-12, close_raw, np.nan)
        v21 = pd.Series(vel_21 / price_safe, index=df.index)
        v51 = pd.Series(vel_51 / price_safe, index=df.index)

        window = config.get("mom_residual_ols_window", 100)
        cov_rolling = v51.rolling(window, min_periods=window).cov(v21)
        var_rolling = v21.rolling(window, min_periods=window).var()
        beta = (cov_rolling / var_rolling.replace(0, np.nan)).clip(-10, 10)

        divergence = v51 - beta * v21
        return pd.Series(divergence.values, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2p. ETF VOLUME Z-SCORE — Fluxo institucional (opcional, pós-2024)
# ---------------------------------------------------------------------------
class ETFVolumeFeature(BaseFeature):
    """
    Z-score do volume de ETFs de Bitcoin (IBIT etc.).

    Proxy de fluxo institucional TradFi → crypto:
      ETF compra → authorized participant compra BTC spot → pressão
      compradora → momentum sustentável.

    Z-score sobre 20 dias rolling:
      z_t = (V_t − μ_V) / σ_V

    Disponível apenas pós-Jan/2024 (IBIT lançado em 11/01/2024).
    Fonte: data/etf_btc_volume.csv via config["_etf_volume_df"].
    Anti-leakage: lag de 1 dia (volume publicado após fechamento).
    """

    name = "etf_volume_zscore"
    required_columns = ["timestamp"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        etf_df = config.get("_etf_volume_df", None)
        if etf_df is None or len(etf_df) == 0:
            return pd.Series(np.nan, index=df.index, name=self.name)

        etf = etf_df.copy()
        etf["timestamp"] = pd.to_datetime(etf["timestamp"], format="ISO8601")
        if etf["timestamp"].dt.tz is None:
            etf["timestamp"] = etf["timestamp"].dt.tz_localize("UTC")
        etf["date"] = etf["timestamp"].dt.date
        etf_map = etf.set_index("date")["volume"].to_dict()

        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("UTC")
        date_prev = (ts - pd.Timedelta(days=1)).dt.date
        raw_vol = date_prev.map(etf_map).ffill()

        raw_series = pd.Series(raw_vol.values, index=df.index, dtype=float)
        mean_20 = raw_series.rolling(20, min_periods=20).mean()
        std_20 = raw_series.rolling(20, min_periods=20).std()
        zscore = (raw_series - mean_20) / std_20.replace(0, np.nan)

        return pd.Series(zscore.values, index=df.index, name=self.name)


# ---------------------------------------------------------------------------
# 2q. VIX — Índice de medo TradFi (opcional)
# ---------------------------------------------------------------------------
class VIXFeature(BaseFeature):
    """
    Variação do VIX — mudança na volatilidade implícita do S&P 500.

    Em vez do nível absoluto, usa a variação percentual diária do VIX.
    A variação captura CHOQUES de volatilidade — um VIX subindo de 15→25
    (+67%) é mais informativo que saber que o VIX está em 25.

    Fonte: data/vix.csv via config["_vix_df"].
    Anti-leakage: lag de 1 dia.
    """

    name = "vix_chg"
    required_columns = ["timestamp"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        vix_df = config.get("_vix_df", None)
        if vix_df is None or len(vix_df) == 0:
            return pd.Series(np.nan, index=df.index, name=self.name)

        vix = vix_df.copy()
        vix["timestamp"] = pd.to_datetime(vix["timestamp"], format="ISO8601")
        if vix["timestamp"].dt.tz is None:
            vix["timestamp"] = vix["timestamp"].dt.tz_localize("UTC")
        vix = vix.sort_values("timestamp")
        # Variação percentual diária do VIX
        vix["vix_chg"] = vix["close"].pct_change()
        vix["date"] = vix["timestamp"].dt.date
        vix_map = vix.set_index("date")["vix_chg"].to_dict()

        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("UTC")
        date_prev = (ts - pd.Timedelta(days=1)).dt.date
        values = date_prev.map(vix_map).ffill()

        return pd.Series(values.values, index=df.index, name=self.name, dtype=float)


# ---------------------------------------------------------------------------
# 2r. DXY SPREAD — Desacoplamento BTC vs Dólar (opcional)
# ---------------------------------------------------------------------------
class DXYSpreadFeature(BaseFeature):
    """
    Spread BTC−DXY — detecta desacoplamento entre BTC e força do dólar.

    btc_dxy_spread = ret_BTC − β × ret_DXY

    Onde β é rolling OLS (default 50 barras):
      β = cov(ret_BTC, ret_DXY) / var(ret_DXY)

    Quando spread é positivo, BTC sobe independente do dólar →
    regime de desacoplamento (momentum próprio do crypto).

    Fonte: data/dxy.csv via config["_dxy_df"].
    Anti-leakage: lag 1 dia + usa retornos (estacionário).
    """

    name = "btc_dxy_spread"
    required_columns = ["close", "timestamp"]

    def compute(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        dxy_df = config.get("_dxy_df", None)
        if dxy_df is None or len(dxy_df) == 0:
            return pd.Series(np.nan, index=df.index, name=self.name)

        dxy = dxy_df.copy()
        dxy["timestamp"] = pd.to_datetime(dxy["timestamp"], format="ISO8601")
        if dxy["timestamp"].dt.tz is None:
            dxy["timestamp"] = dxy["timestamp"].dt.tz_localize("UTC")
        dxy["date"] = dxy["timestamp"].dt.date
        dxy = dxy.sort_values("timestamp")
        dxy["dxy_ret"] = dxy["close"].pct_change()
        dxy_map = dxy.set_index("date")["dxy_ret"].to_dict()

        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("UTC")
        date_prev = (ts - pd.Timedelta(days=1)).dt.date
        dxy_ret = pd.Series(
            date_prev.map(dxy_map).ffill().values, index=df.index, dtype=float
        )

        btc_ret = pd.Series(
            df["close"].values.astype(np.float64), index=df.index
        ).pct_change()

        window = config.get("dxy_beta_window", 50)
        cov_r = btc_ret.rolling(window, min_periods=window).cov(dxy_ret)
        var_r = dxy_ret.rolling(window, min_periods=window).var()
        beta = (cov_r / var_r.replace(0, np.nan)).clip(-10, 10)

        spread = btc_ret - beta * dxy_ret
        return pd.Series(spread.values, index=df.index, name=self.name)


# ===========================================================================
# 3. FEATURE REGISTRY — Orquestra features disponíveis
# ===========================================================================
class FeatureRegistry:
    """
    Descobre e orquestra features disponíveis no DataFrame.

    Registra todas as features (OHLCV + tick-level stubs), mas computa
    apenas aquelas cujas colunas necessárias existem no DataFrame.
    Features indisponíveis são silenciosamente puladas com aviso.
    """

    def __init__(self):
        self._features: List[BaseFeature] = []

    def register(self, feature: BaseFeature) -> None:
        self._features.append(feature)

    def register_defaults(self) -> None:
        """Registra todas as features padrão (OHLCV + stubs tick-level)."""
        # Features OHLCV (sempre disponíveis)
        self.register(FFDFeature())
        self.register(VPINFeature())
        self.register(KyleLambdaFeature())
        self.register(RollSpreadFeature())
        self.register(LempelZivFeature())
        # RSI removed: linear derivative of price, RF extracts nothing beyond
        # what SavGol derivatives and microstructure features already provide.
        self.register(FearGreedFeature())
        self.register(SavGolMomentumFeature())
        # Features de mercado derivativo
        self.register(FundingRateFeature())
        # Features de momentum avançado
        self.register(TStatFeature())
        # MomentumResidualFeature (scale_divergence) removed 2026-03-25:
        # confirmed ARTIFACT by feature_null_model.py (p_rw=0.150, p_shuf=0.185)
        # Features externas opcionais (silenciosamente ignoradas se CSV ausente)
        self.register(ETFVolumeFeature())
        self.register(VIXFeature())
        self.register(DXYSpreadFeature())
        # Features tick-level (stubs — ativam quando dados disponíveis)
        self.register(AmihudLambdaFeature())
        self.register(HasbrouckLambdaFeature())
        self.register(OrderSizeDistFeature())
        self.register(TWAPSignatureFeature())

    def compute_all(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Computa todas as features disponíveis.

        Retorna (df_com_features, lista_de_nomes_de_features).
        Features cujas colunas não existem são ignoradas com aviso.
        """
        df = df.copy()
        feature_names: List[str] = []

        for feat in self._features:
            if not feat.is_available(df):
                print(f"    [SKIP] {feat.name}: colunas ausentes {feat.required_columns}")
                continue

            if isinstance(feat, MultiFeature):
                multi_result = feat.compute_multi(df, config)
                accepted = []
                for name, series in multi_result.items():
                    if series.isna().all():
                        print(f"    [SKIP] {name}: todos NaN (dados ausentes)")
                        continue
                    df[name] = series
                    feature_names.append(name)
                    accepted.append(name)
                if accepted:
                    print(f"    [OK] {feat.name} -> {accepted}")
            else:
                series = feat.compute(df, config)
                if series.isna().all():
                    print(f"    [SKIP] {feat.name}: todos NaN (dados ausentes)")
                    continue
                df[feat.name] = series
                feature_names.append(feat.name)
                print(f"    [OK] {feat.name}")

        return df, feature_names


# ===========================================================================
# 4. TRIPLE-BARRIER METHOD — Cap. 3 AFML
# ===========================================================================
class TripleBarrierLabeler:
    """
    Rotulagem Triple-Barrier para classificação de eventos financeiros.

    Três cenários para cada posição:
      • PROFIT-TAKE:  upper = close × (1 + pt × σ)  → label = +1
      • STOP-LOSS:    lower = close × (1 - sl × σ)  → label = -1
      • TEMPO EXPIRADO: t + max_bars                  → label =  0

    As barreiras horizontais são DINÂMICAS: escalam com a volatilidade EWM.
    O par (t0, t1) é fundamental para o CPCV (purging de spans sobrepostos).
    """

    def __init__(self, config: Dict[str, Any]):
        self.vol_lookback = config.get("vol_lookback", 20)
        self.pt_multiplier = config.get("pt_multiplier", 2.0)
        self.sl_multiplier = config.get("sl_multiplier", 2.0)
        self.max_holding = config.get("max_holding_bars", 50)

    def _daily_vol(self, close: pd.Series) -> pd.Series:
        """Volatilidade via EWM std dos retornos logarítmicos."""
        log_ret = np.log(close / close.shift(1))
        return log_ret.ewm(span=self.vol_lookback, min_periods=self.vol_lookback).std()

    def apply_barriers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica Triple-Barrier a cada dollar bar.

        Retorna DataFrame com colunas adicionais:
          - label: +1 (PT), -1 (SL), 0 (vertical)
          - t0: índice de entrada
          - t1: índice de toque da barreira
        """
        close = df["close"].values.astype(np.float64)
        high = df["high"].values.astype(np.float64)
        low = df["low"].values.astype(np.float64)
        vol = self._daily_vol(pd.Series(close)).values
        n = len(df)

        labels = np.full(n, np.nan)
        t0_arr = np.full(n, -1, dtype=np.int64)
        t1_arr = np.full(n, -1, dtype=np.int64)

        for i in range(n):
            if np.isnan(vol[i]) or vol[i] < 1e-12:
                continue
            entry = close[i]
            upper = entry * (1.0 + self.pt_multiplier * vol[i])
            lower = entry * (1.0 - self.sl_multiplier * vol[i])
            max_j = min(i + self.max_holding, n)

            touched = False
            for j in range(i + 1, max_j):
                if high[j] >= upper:
                    labels[i], t0_arr[i], t1_arr[i] = 1, i, j
                    touched = True
                    break
                if low[j] <= lower:
                    labels[i], t0_arr[i], t1_arr[i] = -1, i, j
                    touched = True
                    break
            if not touched and max_j > i + 1:
                labels[i], t0_arr[i], t1_arr[i] = 0, i, max_j - 1

        df = df.copy()
        df["label"] = labels
        df["t0"] = t0_arr
        df["t1"] = t1_arr
        df = df.dropna(subset=["label"]).reset_index(drop=True)
        df["label"] = df["label"].astype(int)
        df["t0"] = df["t0"].astype(int)
        df["t1"] = df["t1"].astype(int)

        counts = df["label"].value_counts().to_dict()
        print(f"    Distribuição de rótulos: {counts}")
        return df


# ===========================================================================
# 5. CPCV — Combinatorial Purged Cross-Validation (Cap. 12 AFML / MLAM)
# ===========================================================================
class CPCV:
    """
    Combinatorial Purged Cross-Validation.

    ── Por que CPCV e não Purged K-Fold? ─────────────────────────────────
    O Purged K-Fold usa apenas N splits lineares. O CPCV gera C(N, k)
    combinações de grupos de treino/teste, simulando MÚLTIPLOS cenários
    de backtest. Isso:
      1. Produz uma DISTRIBUIÇÃO de métricas (não apenas um ponto)
      2. Permite calcular o Deflated Sharpe Ratio (DSR)
      3. Garante que a descoberta não é fruto do acaso

    ── Algoritmo ─────────────────────────────────────────────────────────
    1. Dividir dados em N grupos contíguos
    2. Gerar C(N, k) combinações de k grupos como teste
    3. Para cada combinação: treinar no complemento, purge + embargo
    4. Agregar resultados: distribuição de SR, acc, F1
    5. Cada amostra aparece em C(N-1, k-1) test sets → aggregar predições

    Com N=6, k=2: C(6,2)=15 paths, cada amostra em C(5,1)=5 test sets.
    """

    def __init__(self, config: Dict[str, Any]):
        self.n_groups = config.get("cpcv_n_groups", 6)
        self.k_test = config.get("cpcv_k_test", 2)
        self.purge_pct = config.get("cpcv_purge_pct", 0.01)
        self.embargo_pct = config.get("cpcv_embargo_pct", 0.01)

        from math import comb
        self.n_paths = comb(self.n_groups, self.k_test)

    def split(
        self,
        n_samples: int,
        t0: np.ndarray,
        t1: np.ndarray,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Gera todos os C(N,k) splits com purging + embargo.

        Parâmetros
        ----------
        n_samples : número total de amostras
        t0, t1 : spans do triple-barrier (para purging)

        Retorna
        -------
        Lista de (train_indices, test_indices), uma por combinação.
        """
        indices = np.arange(n_samples)
        embargo_n = int(n_samples * self.embargo_pct)

        # 1. Definir fronteiras dos N grupos contíguos
        group_size = n_samples // self.n_groups
        group_boundaries: List[Tuple[int, int]] = []
        for g in range(self.n_groups):
            start = g * group_size
            end = (g + 1) * group_size if g < self.n_groups - 1 else n_samples
            group_boundaries.append((start, end))

        # 2. Gerar todas C(N,k) combinações
        splits: List[Tuple[np.ndarray, np.ndarray]] = []
        for test_groups in combinations(range(self.n_groups), self.k_test):
            # Índices de teste = união dos grupos selecionados
            test_idx_list = []
            for g in test_groups:
                s, e = group_boundaries[g]
                test_idx_list.append(indices[s:e])
            test_idx = np.concatenate(test_idx_list)
            test_set = set(test_idx.tolist())

            # Máscara de treino
            train_mask = np.ones(n_samples, dtype=bool)
            # Remover grupos de teste
            for g in test_groups:
                s, e = group_boundaries[g]
                train_mask[s:e] = False

            # PURGE: remover do treino amostras com span sobreposto ao teste.
            # Importante: verificar overlap PER TEST GROUP (não globalmente),
            # senão grupos não-adjacentes (ex: 0 e 5) criam um span enorme
            # que purga quase todo o dataset.
            for g in test_groups:
                gs, ge = group_boundaries[g]
                block_t0_min = t0[gs:ge].min()
                block_t1_max = t1[gs:ge].max()
                overlap = (t0 < block_t1_max) & (t1 > block_t0_min)
                for i in range(n_samples):
                    if overlap[i] and i not in test_set:
                        train_mask[i] = False

            # EMBARGO: remover amostras logo após cada bloco de teste
            for g in test_groups:
                _, e = group_boundaries[g]
                emb_end = min(e + embargo_n, n_samples)
                train_mask[e:emb_end] = False

            train_idx = indices[train_mask]
            splits.append((train_idx, test_idx))

        return splits

    def cross_validate(
        self,
        model_factory: Callable[[], RandomForestClassifier],
        X: np.ndarray,
        y: np.ndarray,
        t0: np.ndarray,
        t1: np.ndarray,
        close: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Executa CPCV completo: treina em cada split, coleta métricas.

        Retorna dicionário com:
          - path_accuracies, path_f1s, path_sharpes: listas por path
          - oos_predictions: predições OOS agregadas (majority vote)
          - oos_indices: índices das amostras com predição OOS
          - mean/std de accuracy, f1, sharpe
        """
        splits = self.split(len(X), t0, t1)

        path_accs: List[float] = []
        path_f1s: List[float] = []
        path_sharpes: List[float] = []
        path_models: List[RandomForestClassifier] = []

        # Para agregar predições OOS (cada amostra em múltiplos test sets)
        oos_preds_collection: Dict[int, List[int]] = {}

        for k, (train_idx, test_idx) in enumerate(splits):
            model = model_factory()
            X_tr, y_tr = X[train_idx], y[train_idx]
            X_te, y_te = X[test_idx], y[test_idx]

            model.fit(X_tr, y_tr)
            y_pred = model.predict(X_te)
            path_models.append(model)

            acc = accuracy_score(y_te, y_pred)
            f1 = f1_score(y_te, y_pred, average="weighted", zero_division=0)

            # Sharpe do path
            close_te = close[test_idx]
            actual_ret = np.diff(close_te, prepend=close_te[0]) / np.maximum(
                close_te, 1e-12
            )
            strat_ret = ModelEvaluator.compute_strategy_returns(
                y_pred, actual_ret,
                fee_maker=DEFAULT_CONFIG["fee_maker"],
                fee_taker=DEFAULT_CONFIG["fee_taker"],
                fee_mode=DEFAULT_CONFIG["fee_mode"],
            )
            sr = (
                np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)
                if len(strat_ret) > 1
                else 0.0
            )

            path_accs.append(acc)
            path_f1s.append(f1)
            path_sharpes.append(sr)

            # Coletar predições OOS
            for idx, pred in zip(test_idx, y_pred):
                if idx not in oos_preds_collection:
                    oos_preds_collection[idx] = []
                oos_preds_collection[idx].append(int(pred))

            print(
                f"    Path {k + 1}/{self.n_paths}: "
                f"acc={acc:.4f}, f1={f1:.4f}, SR={sr:.4f}, "
                f"train={len(train_idx)}, test={len(test_idx)}"
            )

        # Agregar predições OOS via majority vote
        oos_indices = sorted(oos_preds_collection.keys())
        oos_predictions = []
        for i in oos_indices:
            preds = oos_preds_collection[i]
            # Majority vote: valor mais frequente
            counts_map: Dict[int, int] = {}
            for p in preds:
                counts_map[p] = counts_map.get(p, 0) + 1
            majority = max(counts_map, key=lambda k: counts_map[k])
            oos_predictions.append(majority)
        oos_predictions = np.array(oos_predictions)
        oos_true = y[oos_indices]

        results = {
            "path_accuracies": path_accs,
            "path_f1s": path_f1s,
            "path_sharpes": path_sharpes,
            "path_models": path_models,
            "splits": splits,
            "oos_predictions": oos_predictions,
            "oos_true": oos_true,
            "oos_indices": np.array(oos_indices),
            "mean_accuracy": float(np.mean(path_accs)),
            "std_accuracy": float(np.std(path_accs)),
            "mean_f1": float(np.mean(path_f1s)),
            "std_f1": float(np.std(path_f1s)),
            "mean_sharpe": float(np.mean(path_sharpes)),
            "std_sharpe": float(np.std(path_sharpes)),
        }

        print(
            f"\n    CPCV Agregado ({self.n_paths} paths): "
            f"acc={results['mean_accuracy']:.4f}+/-{results['std_accuracy']:.4f}, "
            f"f1={results['mean_f1']:.4f}+/-{results['std_f1']:.4f}, "
            f"SR={results['mean_sharpe']:.4f}+/-{results['std_sharpe']:.4f}"
        )
        return results


# ===========================================================================
# 6. FEATURE SELECTION — MDA + CPCV
# ===========================================================================
class MDAFeatureSelector:
    """
    Seleção de features via MDA (Mean Decrease Accuracy) com CPCV.

    ── Algoritmo ─────────────────────────────────────────────────────────
    1. Roda CPCV preliminar com TODAS as features
    2. Em cada split, calcula MDA por feature (permutação n_repeats vezes)
    3. Agrega MDA across todos os splits → média e std por feature
    4. Mantém features com mda_mean > threshold (default: 0)

    ── Anti-leakage ──────────────────────────────────────────────────────
    Feature selection usa CPCV internamente → tudo out-of-sample.
    """

    def __init__(self, config: Dict[str, Any]):
        self.n_repeats = config.get("mda_n_repeats", 5)
        self.threshold = config.get("mda_selection_threshold", 0.0)
        self.rng_seed = config.get("rng_seed", 42)

    def _mda_single_split(
        self,
        model: RandomForestClassifier,
        X_test: np.ndarray,
        y_test: np.ndarray,
        n_features: int,
    ) -> np.ndarray:
        """Calcula MDA para cada feature em um único split."""
        rng = np.random.RandomState(self.rng_seed)
        baseline_acc = accuracy_score(y_test, model.predict(X_test))
        mda = np.zeros(n_features)

        for j in range(n_features):
            drops = []
            for _ in range(self.n_repeats):
                X_perm = X_test.copy()
                X_perm[:, j] = rng.permutation(X_perm[:, j])
                acc_perm = accuracy_score(y_test, model.predict(X_perm))
                drops.append(baseline_acc - acc_perm)
            mda[j] = np.mean(drops)

        return mda

    def select(
        self,
        cpcv: CPCV,
        model_factory: Callable[[], RandomForestClassifier],
        X: np.ndarray,
        y: np.ndarray,
        t0: np.ndarray,
        t1: np.ndarray,
        feature_names: List[str],
    ) -> Tuple[List[str], pd.DataFrame]:
        """
        Executa feature selection via MDA + CPCV.

        Retorna (features_selecionadas, relatorio_mda_df).
        """
        splits = cpcv.split(len(X), t0, t1)
        n_features = len(feature_names)

        all_mda = np.zeros((len(splits), n_features))

        for k, (train_idx, test_idx) in enumerate(splits):
            model = model_factory()
            model.fit(X[train_idx], y[train_idx])
            all_mda[k] = self._mda_single_split(
                model, X[test_idx], y[test_idx], n_features
            )
            print(
                f"    Feature Selection — Path {k + 1}/{len(splits)}: "
                f"top = {feature_names[np.argmax(all_mda[k])]} "
                f"(MDA={all_mda[k].max():.6f})"
            )

        mda_mean = all_mda.mean(axis=0)
        mda_std = all_mda.std(axis=0)
        mda_lower = mda_mean - mda_std  # informativo (salvo no relatório)

        report = pd.DataFrame({
            "feature": feature_names,
            "mda_mean": mda_mean,
            "mda_std": mda_std,
            "mda_lower_ci": mda_lower,
            "selected": mda_mean > self.threshold,  # critério: média MDA > 0
        }).sort_values("mda_mean", ascending=False).reset_index(drop=True)

        selected = report[report["selected"]]["feature"].tolist()

        # -- Momentum: manter apenas o melhor curto e o melhor longo -------
        short_ret = [f for f in selected if f in ("ret_5", "ret_10", "ret_20")]
        long_ret = [f for f in selected if f in ("ret_50", "ret_150")]
        ret_to_drop = set()
        if len(short_ret) > 1:
            # Manter o de maior MDA, dropar o resto
            best = max(short_ret, key=lambda f: report.loc[report["feature"] == f, "mda_mean"].values[0])
            ret_to_drop.update(set(short_ret) - {best})
        if len(long_ret) > 1:
            best = max(long_ret, key=lambda f: report.loc[report["feature"] == f, "mda_mean"].values[0])
            ret_to_drop.update(set(long_ret) - {best})
        if ret_to_drop:
            selected = [f for f in selected if f not in ret_to_drop]
            print(f"    [RET FILTER] Momentum redundante removido: {sorted(ret_to_drop)}")
            report.loc[report["feature"].isin(ret_to_drop), "selected"] = False

        print(f"\n    Feature Selection Resultado:")
        print(f"    {'Feature':<20s} {'MDA Mean':>10s} {'MDA Std':>10s} {'Selecionada':>12s}")
        print(f"    {'-' * 54}")
        for _, row in report.iterrows():
            sel = "SIM" if row["selected"] else "NAO"
            print(
                f"    {row['feature']:<20s} "
                f"{row['mda_mean']:>10.6f} "
                f"{row['mda_std']:>10.6f} "
                f"{sel:>12s}"
            )
        print(f"\n    Features selecionadas: {len(selected)}/{n_features}")

        return selected, report


# ===========================================================================
# 7. META-LABELING — Cap. 3.6 AFML
# ===========================================================================
class MetaLabeler:
    """
    Meta-Labeling: filtragem de falsos positivos em dois estágios.

    Estágio 1 (Primário): prediz direção (+1 ou -1). Recall alto, precision baixa.
    Estágio 2 (Meta): "Devo confiar na predição?" → meta_label in {0, 1}.
      - Dois meta-models treinados em paralelo: RF e Logistic Regression.
      - Sample weights proporcionais a |retorno por barra| (erros caros pesam mais).
      - O vencedor (maior precision média) é selecionado automaticamente.

    Resultado final:
      - meta_prob > LIMITE_DECISORIO → mantém a predição primária
      - meta_prob <= LIMITE_DECISORIO → não apostar (label = 0)
    """

    def __init__(self, config: Dict[str, Any]):
        rf_params = dict(
            n_estimators=config.get("rf_n_estimators", 500),
            max_depth=config.get("rf_max_depth", 6),
            min_samples_leaf=config.get("rf_min_samples_leaf", 50),
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=config.get("rng_seed", 42),
        )
        self.primary_model = RandomForestClassifier(**rf_params)
        self.meta_rf = RandomForestClassifier(**rf_params)
        self.meta_lr = LogisticRegression(
            C=0.1,
            class_weight="balanced",
            max_iter=1000,
            random_state=config.get("rng_seed", 42),
        )
        self.meta_model = None
        self.meta_model_name = None
        self._trained = False

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        close_train: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Treina primário + dois meta-models (RF e LR) com sample weights."""
        # Primário: apenas amostras com label != 0
        mask = y_train != 0
        X_dir, y_dir = X_train[mask], y_train[mask]
        self.primary_model.fit(X_dir, y_dir)
        acc_prim = accuracy_score(y_dir, self.primary_model.predict(X_dir))
        print(f"    Primario: in-sample acc={acc_prim:.4f}, n={len(y_dir)}")

        # Meta-labels: 1 se primário acertou, 0 se errou
        primary_preds = self.primary_model.predict(X_train)
        meta_y = (primary_preds == y_train).astype(int)
        dist = dict(zip(*np.unique(meta_y, return_counts=True)))

        # Sample weights: |retorno por barra| normalizado
        sample_weights = None
        if close_train is not None:
            actual_ret = np.diff(close_train, prepend=close_train[0]) / np.maximum(
                close_train, 1e-12
            )
            sample_weights = np.abs(actual_ret)
            p05, p95 = np.percentile(sample_weights, [5, 95])
            sample_weights = np.clip(sample_weights, p05, p95)
            w_mean = np.mean(sample_weights)
            if w_mean > 0:
                sample_weights = sample_weights / w_mean
            print(f"    Sample weights: |ret| clipped [P05-P95], normalizado, "
                  f"mean=1.00, std={np.std(sample_weights):.4f}")
        else:
            print("    Sample weights: None (close_train nao fornecido)")

        # Treinar ambos meta-models
        fit_report: Dict[str, Any] = {"meta_y_dist": dist}
        for name, model in [("RF", self.meta_rf), ("LR", self.meta_lr)]:
            model.fit(X_train, meta_y, sample_weight=sample_weights)
            preds = model.predict(X_train)
            acc = accuracy_score(meta_y, preds)
            # Precision no acerto (classe 1): quão bom é o filtro
            mask_pred_1 = preds == 1
            prec_1 = float(np.mean(meta_y[mask_pred_1])) if mask_pred_1.sum() > 0 else 0.0
            fit_report[name] = {"accuracy": acc, "precision_1": prec_1}
            print(f"    Meta {name}: in-sample acc={acc:.4f}, "
                  f"precision(1)={prec_1:.4f}, dist={dist}")

        # Sempre usar LR: probabilidades calibradas por construção
        self.meta_model = self.meta_lr
        self.meta_model_name = "LR"

        #print(f"    >>> Meta-model selecionado: {self.meta_model_name} "
        #      f"(precision RF={prec_rf:.4f}, LR={prec_lr:.4f})")
        fit_report["winner"] = self.meta_model_name
        self._trained = True
        return fit_report

    def _predict_with(
        self, model, X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predição usando um meta-model específico."""
        primary_pred = self.primary_model.predict(X)
        meta_prob = model.predict_proba(X)
        idx_1 = list(model.classes_).index(1)
        meta_confidence = meta_prob[:, idx_1]
        final = np.where(meta_confidence > LIMITE_DECISORIO, primary_pred, 0)
        return final, meta_confidence, primary_pred

    def predict(
        self, X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predição combinada usando o meta-model vencedor."""
        if not self._trained:
            raise RuntimeError("Chame fit() antes de predict().")
        # Fallback para modelos legacy (pre-dual meta)
        if not hasattr(self, "meta_rf"):
            primary_pred = self.primary_model.predict(X)
            meta_prob = self.meta_model.predict_proba(X)
            idx_1 = list(self.meta_model.classes_).index(1)
            meta_confidence = meta_prob[:, idx_1]
            final = np.where(meta_confidence > LIMITE_DECISORIO, primary_pred, 0)
            return final, meta_confidence, primary_pred
        return self._predict_with(self.meta_model, X)

    def predict_both(
        self, X: np.ndarray
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """Predição com ambos meta-models (RF e LR) para comparação."""
        if not self._trained:
            raise RuntimeError("Chame fit() antes de predict_both().")
        primary_pred = self.primary_model.predict(X)
        results: Dict[str, Dict[str, np.ndarray]] = {}
        for name, model in [("RF", self.meta_rf), ("LR", self.meta_lr)]:
            meta_prob = model.predict_proba(X)
            idx_1 = list(model.classes_).index(1)
            meta_confidence = meta_prob[:, idx_1]
            final = np.where(meta_confidence > LIMITE_DECISORIO, primary_pred, 0)
            results[name] = {
                "final": final,
                "meta_confidence": meta_confidence,
                "primary_pred": primary_pred,
            }
        return results


# ===========================================================================
# 8. MODEL EVALUATOR — MDA, PSR, DSR
# ===========================================================================
class ModelEvaluator:
    """
    Avaliação completa seguindo as diretrizes de López de Prado.

    • MDA com intervalos de confiança (from CPCV splits)
    • PSR — Probabilistic Sharpe Ratio (Cap. 14 AFML)
    • DSR — Deflated Sharpe Ratio (ajuste para múltiplos testes)
    """

    @staticmethod
    def probabilistic_sharpe_ratio(
        returns: np.ndarray, sr_benchmark: float = 0.0
    ) -> float:
        """
        PSR = Phi[(SR_hat - SR*) x sqrt(T-1) / sqrt(1 - gamma3*SR_hat + (gamma4-1)/4*SR_hat^2)]

        PSR > 0.95 → estatisticamente significativo a 95%.
        """
        returns = returns[~np.isnan(returns)]
        T = len(returns)
        if T < 3:
            return 0.0
        sr_hat = np.mean(returns) / max(np.std(returns, ddof=1), 1e-12)
        skew = sp_stats.skew(returns)
        kurt = sp_stats.kurtosis(returns)
        denom = 1.0 - skew * sr_hat + (kurt - 1.0) / 4.0 * sr_hat ** 2
        if denom <= 0:
            denom = 1e-12
        psr = sp_stats.norm.cdf(
            (sr_hat - sr_benchmark) * np.sqrt(T - 1) / np.sqrt(denom)
        )
        return float(psr)

    @staticmethod
    def deflated_sharpe_ratio(
        returns: np.ndarray, n_trials: int
    ) -> float:
        """
        Deflated Sharpe Ratio — ajusta PSR para múltiplos testes.
        (Bailey & López de Prado, 2014)

        SR*_0 = sqrt(V[SR_hat]) * {sqrt(2*ln(K)) * (1 - gamma/ln(K))
                                    + gamma / sqrt(2*ln(K))}

        onde V[SR_hat] = (1 - gamma3*SR + (gamma4-1)/4*SR^2) / (T-1)
        e K = número de trials, gamma = 0.5772 (Euler-Mascheroni).

        DSR = PSR(SR_observado, SR*_0)
        """
        if n_trials < 2:
            return ModelEvaluator.probabilistic_sharpe_ratio(returns, 0.0)

        returns = returns[~np.isnan(returns)]
        T = len(returns)
        if T < 3:
            return 0.0

        sr_hat = np.mean(returns) / max(np.std(returns, ddof=1), 1e-12)
        skew = sp_stats.skew(returns)
        kurt = sp_stats.kurtosis(returns)

        # Variância do estimador SR (Bailey & López de Prado, 2014)
        v_sr = (1.0 - skew * sr_hat + (kurt - 1.0) / 4.0 * sr_hat ** 2) / (T - 1)

        gamma_euler = 0.5772156649
        log_k = max(np.log(n_trials), 1e-6)

        # E[max(SR)] sob H0 — escalado por sqrt(V[SR_hat])
        sr_expected = np.sqrt(max(v_sr, 0.0)) * (
            np.sqrt(2.0 * log_k) * (1.0 - gamma_euler / log_k)
            + gamma_euler / np.sqrt(2.0 * log_k)
        )
        return ModelEvaluator.probabilistic_sharpe_ratio(returns, sr_expected)

    @staticmethod
    def compute_strategy_returns(
        predictions: np.ndarray,
        actual_returns: np.ndarray,
        fee_maker: float = 0.0,
        fee_taker: float = 0.0,
        fee_mode: str = "pessimistic",
    ) -> np.ndarray:
        """
        Retorno da estratégia: pred × actual_return − custos de transação.

        Fees são cobradas a cada MUDANÇA de posição:
          - fee_mode="pessimistic" (padrão): taker em ambas as pontas.
            Conservador — assume market order sempre. Se o alpha sobrevive
            aqui, qualquer economia com limit orders é upside gratuito.
          - fee_mode="optimistic": taker na entrada, maker na saída.
            Assume que saídas são sempre via limit order (irrealista em
            stop-loss ou regime changes com mercado rápido).
        """
        raw = predictions * actual_returns
        if fee_maker == 0.0 and fee_taker == 0.0:
            return raw

        if fee_mode == "pessimistic":
            fee_entry = fee_taker
            fee_exit = fee_taker
        else:  # optimistic
            fee_entry = fee_taker
            fee_exit = fee_maker

        costs = np.zeros_like(raw)
        prev = 0.0
        for i in range(len(predictions)):
            cur = predictions[i]
            if cur != prev:
                if prev != 0:
                    costs[i] += fee_exit    # fechar posição anterior
                if cur != 0:
                    costs[i] += fee_entry   # abrir nova posição
            prev = cur
        return raw - costs

    @staticmethod
    def mda_from_cpcv(
        cpcv_results: Dict[str, Any],
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        n_repeats: int = 5,
        rng_seed: int = 42,
    ) -> pd.DataFrame:
        """
        Calcula MDA usando os modelos e splits do CPCV.

        Retorna DataFrame com mda_mean, mda_std por feature,
        baseado em TODOS os C(N,k) splits (intervalos de confiança robustos).
        """
        rng = np.random.RandomState(rng_seed)
        splits = cpcv_results["splits"]
        models = cpcv_results["path_models"]
        n_features = len(feature_names)

        all_mda = np.zeros((len(splits), n_features))

        for k, ((_, test_idx), model) in enumerate(zip(splits, models)):
            X_te, y_te = X[test_idx], y[test_idx]
            baseline_acc = accuracy_score(y_te, model.predict(X_te))

            for j in range(n_features):
                drops = []
                for _ in range(n_repeats):
                    X_perm = X_te.copy()
                    X_perm[:, j] = rng.permutation(X_perm[:, j])
                    acc_perm = accuracy_score(y_te, model.predict(X_perm))
                    drops.append(baseline_acc - acc_perm)
                all_mda[k, j] = np.mean(drops)

        mda_df = pd.DataFrame({
            "feature": feature_names,
            "mda_mean": all_mda.mean(axis=0),
            "mda_std": all_mda.std(axis=0),
        }).sort_values("mda_mean", ascending=False).reset_index(drop=True)

        return mda_df


# ===========================================================================
# 9. ADVANCED VISUALIZER — 8 plots diagnósticos
# ===========================================================================
class AdvancedVisualizer:
    """Gera 8 plots diagnósticos e salva como PNG em save_dir."""

    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def _save(self, fig: plt.Figure, name: str) -> None:
        path = os.path.join(self.save_dir, name)
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"    Plot salvo: {path}")

    # 1. Dollar bars sampling
    def plot_dollar_bars_sampling(self, dollar_bars: pd.DataFrame) -> None:
        """Distribuição de ticks por dollar bar + constância do dollar volume."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        axes[0].hist(dollar_bars["tick_count"], bins=50, edgecolor="black", alpha=0.7)
        axes[0].set_xlabel("Ticks por Dollar Bar")
        axes[0].set_ylabel("Frequencia")
        axes[0].set_title("Distribuicao de ticks por Dollar Bar")
        med = dollar_bars["tick_count"].median()
        axes[0].axvline(med, color="red", ls="--", label=f"Mediana={med:.0f}")
        axes[0].legend()

        axes[1].plot(dollar_bars["dollar_volume"].values, lw=0.5, alpha=0.7)
        axes[1].set_xlabel("Indice da Dollar Bar")
        axes[1].set_ylabel("Dollar Volume")
        axes[1].set_title("Dollar Volume por Barra (deve ser ~constante)")

        plt.tight_layout()
        self._save(fig, "dollar_bars_sampling.png")

    # 2. Feature importance MDA
    def plot_feature_importance_mda(self, mda_df: pd.DataFrame) -> None:
        """Bar chart horizontal de MDA com barras de erro (CI do CPCV)."""
        fig, ax = plt.subplots(figsize=(10, max(6, len(mda_df) * 0.5)))
        names = mda_df["feature"].values
        means = mda_df["mda_mean"].values
        stds = mda_df["mda_std"].values

        y_pos = np.arange(len(names))
        colors = ["#2ecc71" if m > 0 else "#e74c3c" for m in means]
        ax.barh(y_pos, means, xerr=stds, align="center", alpha=0.8,
                capsize=3, color=colors)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.invert_yaxis()
        ax.set_xlabel("Mean Decrease Accuracy (MDA)")
        ax.set_title("Feature Importance — MDA via CPCV (AFML Cap. 8)")
        ax.axvline(0, color="gray", ls="--", lw=0.8)
        plt.tight_layout()
        self._save(fig, "feature_importance_mda.png")

    # 3. Triple barrier labels
    def plot_triple_barrier_labels(self, df: pd.DataFrame) -> None:
        """Preço com rótulos do triple-barrier coloridos."""
        fig, ax = plt.subplots(figsize=(14, 6))
        colors = {1: "green", -1: "red", 0: "gray"}
        labels_map = {1: "Profit-Take (+1)", -1: "Stop-Loss (-1)", 0: "Vertical (0)"}

        ax.plot(df["close"].values, color="black", lw=0.5, alpha=0.6, label="Close")
        for lbl, c in colors.items():
            mask = df["label"] == lbl
            if mask.any():
                ax.scatter(
                    np.where(mask)[0], df.loc[mask, "close"].values,
                    c=c, s=3, alpha=0.5, label=labels_map[lbl],
                )
        ax.set_xlabel("Indice da Dollar Bar")
        ax.set_ylabel("Preco BTC (USD)")
        ax.set_title("Triple-Barrier Labels sobre Dollar Bars")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "triple_barrier_labels.png")

    # 4. CPCV Sharpe distribution
    def plot_cpcv_sharpe_distribution(
        self, sharpes: List[float], psr: float, dsr: float
    ) -> None:
        """Histograma dos C(N,k) Sharpe Ratios com PSR e DSR anotados."""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(sharpes, bins=max(5, len(sharpes) // 2), edgecolor="black",
                alpha=0.7, color="#3498db")
        ax.axvline(np.mean(sharpes), color="red", ls="--", lw=2,
                   label=f"Media={np.mean(sharpes):.4f}")
        ax.axvline(0, color="gray", ls=":", lw=1)

        txt = f"PSR = {psr:.4f}\nDSR = {dsr:.4f}\nn_paths = {len(sharpes)}"
        ax.text(0.98, 0.95, txt, transform=ax.transAxes, fontsize=11,
                verticalalignment="top", horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

        ax.set_xlabel("Sharpe Ratio")
        ax.set_ylabel("Frequencia")
        ax.set_title("Distribuicao de Sharpe Ratios — CPCV Paths")
        ax.legend()
        plt.tight_layout()
        self._save(fig, "cpcv_sharpe_distribution.png")

    # 5. CPCV accuracy/F1 distribution
    def plot_cpcv_accuracy_distribution(
        self, accs: List[float], f1s: List[float]
    ) -> None:
        """Box plot de accuracy e F1 across CPCV paths."""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        bp1 = axes[0].boxplot(accs, patch_artist=True)
        bp1["boxes"][0].set_facecolor("#3498db")
        axes[0].set_ylabel("Accuracy")
        axes[0].set_title(f"CPCV Accuracy (u={np.mean(accs):.4f}+/-{np.std(accs):.4f})")
        axes[0].set_xticklabels(["CPCV Paths"])

        bp2 = axes[1].boxplot(f1s, patch_artist=True)
        bp2["boxes"][0].set_facecolor("#2ecc71")
        axes[1].set_ylabel("F1 Score (weighted)")
        axes[1].set_title(f"CPCV F1 (u={np.mean(f1s):.4f}+/-{np.std(f1s):.4f})")
        axes[1].set_xticklabels(["CPCV Paths"])

        plt.tight_layout()
        self._save(fig, "cpcv_accuracy_distribution.png")

    # 6. Cumulative returns
    def plot_cumulative_returns(
        self,
        strategy_returns: np.ndarray,
        benchmark_returns: np.ndarray,
        psr: float,
        dsr: float,
    ) -> None:
        """Retorno acumulado estratégia vs benchmark com PSR/DSR."""
        fig, ax = plt.subplots(figsize=(14, 6))
        cum_strat = np.cumsum(strategy_returns)
        cum_bench = np.cumsum(benchmark_returns)

        ax.plot(cum_strat, label="Estrategia (Meta-Label)", lw=1.2, color="blue")
        ax.plot(cum_bench, label="Benchmark (Buy & Hold)", lw=1.0,
                color="gray", alpha=0.7)
        ax.fill_between(range(len(cum_strat)), cum_strat, alpha=0.1, color="blue")

        txt = f"PSR = {psr:.4f}\nDSR = {dsr:.4f}"
        ax.text(0.02, 0.95, txt, transform=ax.transAxes, fontsize=12,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

        ax.set_xlabel("Indice da Barra (teste)")
        ax.set_ylabel("Retorno Acumulado")
        ax.set_title("Retorno Acumulado: Estrategia vs Benchmark")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "cumulative_returns.png")

    # 6b. Portfolio equity — retorno composto real
    def plot_portfolio_equity(
        self,
        strategy_returns: np.ndarray,
        close_prices: np.ndarray,
        timestamps: np.ndarray,
        psr: float,
        dsr: float,
        sharpe: float,
    ) -> None:
        """
        Rentabilidade REAL da estratégia vs BTC buy & hold (retorno composto).

        Diferente do cumulative_returns.png (soma aritmética), este plot usa
        np.cumprod(1 + r) — representando o crescimento real de $1 investido.
        """
        timestamps = pd.to_datetime(timestamps)

        # Equity da estratégia: produto acumulado (1+r_1)(1+r_2)...
        equity_strat = np.cumprod(1.0 + strategy_returns)
        # BTC buy & hold: preço normalizado pelo preço inicial
        equity_btc = close_prices / close_prices[0]

        # Max drawdown da estratégia
        running_max = np.maximum.accumulate(equity_strat)
        drawdowns = (equity_strat - running_max) / running_max
        max_dd = drawdowns.min()

        # Retornos totais
        ret_strat = (equity_strat[-1] - 1.0) * 100
        ret_btc = (equity_btc[-1] - 1.0) * 100

        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(timestamps, equity_strat, label="Estrategia (Meta-Label)",
                lw=1.5, color="blue")
        ax.plot(timestamps, equity_btc, label="BTC Buy & Hold",
                lw=1.2, color="orange", alpha=0.8)
        ax.axhline(1.0, color="gray", ls=":", lw=0.8, alpha=0.5)
        ax.fill_between(timestamps, equity_strat, 1.0, alpha=0.08, color="blue")

        # Anotações
        txt = (
            f"Estrategia: {ret_strat:+.2f}%\n"
            f"BTC B&H:    {ret_btc:+.2f}%\n"
            f"Max DD:     {max_dd * 100:.2f}%\n"
            f"SR: {sharpe:.4f}\n"
            f"PSR: {psr:.4f}  DSR: {dsr:.4f}"
        )
        ax.text(0.02, 0.95, txt, transform=ax.transAxes, fontsize=10,
                verticalalignment="top", family="monospace",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        ax.set_xlabel("Data")
        ax.set_ylabel("Valor do Portfolio (1.0 = capital inicial)")
        ax.set_title("Rentabilidade Real: Estrategia vs BTC/USDT (conjunto de teste)")
        ax.legend(fontsize=9, loc="lower right")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "portfolio_equity.png")

    # 7. Confusion matrix
    def plot_confusion_matrix(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> None:
        """Heatmap da confusion matrix OOS."""
        labels = sorted(set(y_true) | set(y_pred))
        cm = confusion_matrix(y_true, y_pred, labels=labels)

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
        ax.figure.colorbar(im, ax=ax)

        ax.set(
            xticks=np.arange(cm.shape[1]),
            yticks=np.arange(cm.shape[0]),
            xticklabels=labels,
            yticklabels=labels,
            xlabel="Predicao",
            ylabel="Real",
            title="Confusion Matrix — OOS Agregado (CPCV)",
        )

        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(
                    j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                )
        plt.tight_layout()
        self._save(fig, "confusion_matrix.png")

    # 8. Zoom 2 dias — classificações train/test sobre o preço
    def plot_2day_zoom(
        self,
        df_labeled: pd.DataFrame,
        final_preds: np.ndarray,
        primary_preds: np.ndarray,
        y_true: np.ndarray,
        test_start_idx: int,
        train_preds: np.ndarray,
        train_true: np.ndarray,
    ) -> None:
        """
        Plot de recorte curto (~2 dias) com classificações do modelo.

        Mostra preço + marcadores de predição (train e test) + labels reais
        para verificação visual da qualidade do modelo.
        """
        # ~100 dollar bars ~ 2 dias com 50 bars/dia
        bars_2days = 100
        # Centralizar na transição train→test
        zoom_start = max(0, test_start_idx - bars_2days // 2)
        zoom_end = min(len(df_labeled), zoom_start + bars_2days)

        close_zoom = df_labeled["close"].values[zoom_start:zoom_end]

        # Timestamps para eixo x
        timestamps = pd.to_datetime(df_labeled["timestamp"].values[zoom_start:zoom_end])

        fig, ax = plt.subplots(figsize=(16, 8))

        # Background: train vs test
        boundary_local = min(test_start_idx - zoom_start, len(timestamps) - 1)
        boundary_local = max(0, boundary_local)
        if boundary_local > 0 and boundary_local < len(timestamps):
            ax.axvspan(
                timestamps.min(), timestamps[boundary_local],
                alpha=0.08, color="green", label="Regiao de Treino"
            )
            ax.axvspan(
                timestamps[boundary_local], timestamps.max(),
                alpha=0.08, color="blue", label="Regiao de Teste"
            )

        # Preço
        ax.plot(timestamps, close_zoom, color="black", lw=1.5, alpha=0.8, label="Close")

        color_map = {1: "green", -1: "red", 0: "gray"}

        # Classificações TREINO
        for i_local in range(min(boundary_local, len(close_zoom))):
            i_global = zoom_start + i_local
            if i_global < len(train_preds):
                pred = train_preds[i_global]
                true_l = train_true[i_global]
                c = color_map.get(int(pred), "gray")
                ax.scatter(timestamps[i_local], close_zoom[i_local],
                           c=c, s=30, alpha=0.6, zorder=5,
                           edgecolors="black", linewidths=0.3)
                tc = color_map.get(int(true_l), "gray")
                ax.scatter(timestamps[i_local], close_zoom[i_local] * 0.999,
                           c=tc, s=10, alpha=0.8, zorder=4, marker="v")

        # Classificações TESTE
        for i_local in range(max(boundary_local, 0), len(close_zoom)):
            i_test = zoom_start + i_local - test_start_idx
            if 0 <= i_test < len(final_preds):
                pred = final_preds[i_test]
                true_l = y_true[i_test]
                prim = primary_preds[i_test]

                c = color_map.get(int(pred), "gray")
                ax.scatter(timestamps[i_local], close_zoom[i_local],
                           c=c, s=40, alpha=0.8, zorder=5,
                           edgecolors="black", linewidths=0.5)
                tc = color_map.get(int(true_l), "gray")
                ax.scatter(timestamps[i_local], close_zoom[i_local] * 0.999,
                           c=tc, s=12, alpha=0.9, zorder=4, marker="v")
                # Círculo se meta-model filtrou
                if prim != 0 and pred == 0:
                    ax.scatter(timestamps[i_local], close_zoom[i_local],
                               facecolors="none", edgecolors="orange",
                               s=120, linewidths=2, zorder=6)

        # Legenda
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker="o", color="w", markerfacecolor="green",
                   markersize=8, label="Pred: Long (+1)"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="red",
                   markersize=8, label="Pred: Short (-1)"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="gray",
                   markersize=8, label="Pred: Fora (0)"),
            Line2D([0], [0], marker="v", color="w", markerfacecolor="black",
                   markersize=6, label="Label Real"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="none",
                   markeredgecolor="orange", markersize=10, markeredgewidth=2,
                   label="Filtrado pelo Meta-Model"),
        ]
        ax.legend(handles=legend_elements, fontsize=8, loc="upper left")

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        fig.autofmt_xdate()
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Preco BTC (USD)")

        date_start = timestamps.min().strftime("%Y-%m-%d") if len(timestamps) > 0 else "?"
        date_end = timestamps.max().strftime("%Y-%m-%d") if len(timestamps) > 0 else "?"
        ax.set_title(f"Zoom ~2 Dias — Classificacoes Train/Test ({date_start} a {date_end})")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "2day_zoom_classification.png")

    # 9. Concentration analysis — top-N trades
    def plot_return_concentration(
        self,
        strat_returns: np.ndarray,
        predictions: np.ndarray,
    ) -> None:
        """
        Analisa concentracao do retorno: quanto vem dos top-N trades.

        Responde a pergunta de Marcos: "se >80% do retorno vem de 5 trades,
        o resultado e anedotico."
        """
        # Retornos apenas de trades ativos
        active_mask = predictions != 0
        active_rets = strat_returns[active_mask]
        if len(active_rets) == 0:
            print("    [SKIP] Concentracao: nenhum trade ativo.")
            return

        total_ret = np.sum(active_rets)
        if abs(total_ret) < 1e-12:
            print("    [SKIP] Concentracao: retorno total ~0.")
            return

        # Positivos e negativos separados
        gains = active_rets[active_rets > 0]
        losses = active_rets[active_rets < 0]

        sorted_abs = np.sort(np.abs(active_rets))[::-1]
        cum_pct = np.cumsum(sorted_abs) / np.sum(sorted_abs) * 100

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Panel 1: Cumulative concentration curve
        ax = axes[0]
        n_trades = len(sorted_abs)
        x_range = np.arange(1, n_trades + 1)
        ax.plot(x_range, cum_pct, "b-", lw=2)
        ax.axhline(80, color="red", ls="--", lw=1, alpha=0.7, label="80%")
        ax.axhline(50, color="orange", ls="--", lw=1, alpha=0.7, label="50%")

        # Mark key points
        for pct_target in [50, 80]:
            idx = np.searchsorted(cum_pct, pct_target)
            if idx < n_trades:
                ax.scatter(idx + 1, cum_pct[idx], s=80, zorder=5, color="red" if pct_target == 80 else "orange")
                ax.annotate(f"Top {idx + 1} = {cum_pct[idx]:.1f}%",
                            xy=(idx + 1, cum_pct[idx]),
                            xytext=(idx + 1 + n_trades * 0.05, cum_pct[idx] - 5),
                            fontsize=9, fontweight="bold")

        ax.set_xlabel("Numero de trades (ordenado por |retorno|)")
        ax.set_ylabel("% do retorno absoluto acumulado")
        ax.set_title("Concentracao do Retorno")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # Panel 2: Top-10 individual trades
        ax2 = axes[1]
        top_n = min(20, n_trades)
        top_rets = active_rets[np.argsort(np.abs(active_rets))[::-1][:top_n]]
        colors = ["#2ecc71" if r > 0 else "#e74c3c" for r in top_rets]
        bars = ax2.bar(range(top_n), top_rets * 100, color=colors, alpha=0.8)
        ax2.set_xlabel("Rank (por |retorno|)")
        ax2.set_ylabel("Retorno (%)")
        ax2.set_title(f"Top {top_n} Trades por Magnitude")
        ax2.axhline(0, color="gray", ls="-", lw=0.5)
        ax2.grid(True, alpha=0.3, axis="y")

        # Summary text
        n_top5_pct = cum_pct[min(4, n_trades - 1)]
        n_top10_pct = cum_pct[min(9, n_trades - 1)]
        fig.suptitle(
            f"Analise de Concentracao — {n_trades} trades ativos | "
            f"Top 5 = {n_top5_pct:.1f}% | Top 10 = {n_top10_pct:.1f}% | "
            f"Gains: {len(gains)} | Losses: {len(losses)}",
            fontsize=11, fontweight="bold",
        )
        plt.tight_layout()
        self._save(fig, "return_concentration.png")

        # TXT report
        conc_txt = "RETURN CONCENTRATION ANALYSIS\n" + "=" * 60 + "\n\n"
        conc_txt += f"  Trades ativos: {n_trades}\n"
        conc_txt += f"  Retorno total (soma): {total_ret * 100:.4f}%\n"
        conc_txt += f"  Gains: {len(gains)} ({len(gains)/n_trades*100:.1f}%)\n"
        conc_txt += f"  Losses: {len(losses)} ({len(losses)/n_trades*100:.1f}%)\n\n"
        for k in [1, 3, 5, 10, 20, 50]:
            if k <= n_trades:
                conc_txt += f"  Top {k:>3d} trades: {cum_pct[k-1]:>6.1f}% do retorno absoluto\n"
        path = os.path.join(self.save_dir, "return_concentration.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(conc_txt)
        print(f"    Report salvo: {path}")

    # 10. Threshold grid — DSR/SR across LIMITE_DECISORIO values (RF vs LR)
    def plot_threshold_grid(
        self,
        meta_confidence_dict: Dict[str, np.ndarray],
        primary_preds: np.ndarray,
        actual_returns: np.ndarray,
        y_true: np.ndarray,
        thresholds: list,
        n_trials: int,
        fee_maker: float,
        fee_taker: float,
        fee_mode: str,
    ) -> None:
        """
        Grid de thresholds para o meta-label — RF vs LR side-by-side.

        meta_confidence_dict: {"RF": arr, "LR": arr}
        """
        # Compute metrics for each model and threshold
        all_results: Dict[str, list] = {}
        for model_name, meta_confidence in meta_confidence_dict.items():
            results = []
            for th in thresholds:
                preds = np.where(meta_confidence > th, primary_preds, 0)
                n_active = int(np.sum(preds != 0))
                strat_ret = ModelEvaluator.compute_strategy_returns(
                    preds, actual_returns,
                    fee_maker=fee_maker, fee_taker=fee_taker, fee_mode=fee_mode,
                )
                sr = np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)
                psr = ModelEvaluator.probabilistic_sharpe_ratio(strat_ret)
                dsr = ModelEvaluator.deflated_sharpe_ratio(strat_ret, n_trials)
                acc = accuracy_score(y_true, preds)
                skew = sp_stats.skew(strat_ret[~np.isnan(strat_ret)])
                cum_ret = np.sum(strat_ret) * 100
                results.append({
                    "threshold": th, "sr": sr, "psr": psr, "dsr": dsr,
                    "accuracy": acc, "n_active": n_active, "skewness": skew,
                    "cum_ret_pct": cum_ret,
                })
            all_results[model_name] = results

        ths = thresholds
        model_names = list(all_results.keys())
        styles = {"RF": ("o-", "#2980b9"), "LR": ("s--", "#e67e22")}

        fig, axes = plt.subplots(2, 3, figsize=(16, 10))

        # DSR
        ax = axes[0, 0]
        for mn in model_names:
            fmt, color = styles.get(mn, ("o-", "gray"))
            ax.plot(ths, [r["dsr"] for r in all_results[mn]],
                    fmt, lw=2, markersize=7, color=color, label=mn)
        ax.axhline(0.95, color="green", ls="--", lw=1, alpha=0.7, label="DSR=0.95")
        ax.set_ylabel("DSR")
        ax.set_title("Deflated Sharpe Ratio")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # SR
        ax = axes[0, 1]
        for mn in model_names:
            fmt, color = styles.get(mn, ("o-", "gray"))
            ax.plot(ths, [r["sr"] for r in all_results[mn]],
                    fmt, lw=2, markersize=7, color=color, label=mn)
        ax.axhline(0, color="gray", ls="--", lw=0.8)
        ax.set_ylabel("Sharpe Ratio")
        ax.set_title("Sharpe Ratio")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # N trades (bars side-by-side)
        ax = axes[0, 2]
        bar_w = 0.004
        for i, mn in enumerate(model_names):
            _, color = styles.get(mn, ("o-", "gray"))
            offset = (i - 0.5) * bar_w
            ax.bar([t + offset for t in ths],
                   [r["n_active"] for r in all_results[mn]],
                   width=bar_w, color=color, alpha=0.8, label=mn)
        ax.set_ylabel("N trades ativos")
        ax.set_title("Numero de Trades")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

        # Skewness
        ax = axes[1, 0]
        for mn in model_names:
            fmt, color = styles.get(mn, ("o-", "gray"))
            ax.plot(ths, [r["skewness"] for r in all_results[mn]],
                    fmt, lw=2, markersize=7, color=color, label=mn)
        ax.axhline(0, color="gray", ls="--", lw=0.8)
        ax.set_xlabel("LIMITE_DECISORIO")
        ax.set_ylabel("Skewness")
        ax.set_title("Skewness dos Retornos")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Cumulative return
        ax = axes[1, 1]
        for mn in model_names:
            fmt, color = styles.get(mn, ("o-", "gray"))
            ax.plot(ths, [r["cum_ret_pct"] for r in all_results[mn]],
                    fmt, lw=2, markersize=7, color=color, label=mn)
        ax.axhline(0, color="gray", ls="--", lw=0.8)
        ax.set_xlabel("LIMITE_DECISORIO")
        ax.set_ylabel("Retorno Acumulado (%)")
        ax.set_title("Retorno Total")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # PSR
        ax = axes[1, 2]
        for mn in model_names:
            fmt, color = styles.get(mn, ("o-", "gray"))
            ax.plot(ths, [r["psr"] for r in all_results[mn]],
                    fmt, lw=2, markersize=7, color=color, label=mn)
        ax.axhline(0.95, color="green", ls="--", lw=1, alpha=0.7, label="PSR=0.95")
        ax.set_xlabel("LIMITE_DECISORIO")
        ax.set_ylabel("PSR")
        ax.set_title("Probabilistic Sharpe Ratio")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        fig.suptitle(
            f"Threshold Grid — RF vs LR (N={len(y_true)} barras)",
            fontsize=13, fontweight="bold",
        )
        plt.tight_layout()
        self._save(fig, "threshold_grid.png")

        # TXT report — one table per model
        grid_txt = "THRESHOLD GRID REPORT (RF vs LR)\n" + "=" * 60 + "\n"
        for mn in model_names:
            grid_txt += f"\n  [{mn}]\n"
            grid_txt += f"{'Threshold':>10s} {'SR':>8s} {'PSR':>8s} {'DSR':>8s} "
            grid_txt += f"{'Accuracy':>10s} {'N_active':>10s} {'Skew':>8s} {'CumRet%':>10s}\n"
            grid_txt += "  " + "-" * 74 + "\n"
            for r in all_results[mn]:
                grid_txt += (
                    f"{r['threshold']:>10.2f} {r['sr']:>8.4f} {r['psr']:>8.4f} "
                    f"{r['dsr']:>8.4f} {r['accuracy']:>10.4f} {r['n_active']:>10d} "
                    f"{r['skewness']:>8.2f} {r['cum_ret_pct']:>10.2f}\n"
                )
        path = os.path.join(self.save_dir, "threshold_grid.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(grid_txt)
        print(f"    Report salvo: {path}")

    # 11. Return distribution — histogram + skewness
    def plot_return_distribution(
        self,
        strat_returns: np.ndarray,
        predictions: np.ndarray,
    ) -> None:
        """Histograma da distribuicao de retornos com metricas de forma."""
        all_rets = strat_returns[~np.isnan(strat_returns)]
        active_mask = predictions != 0
        active_rets = strat_returns[active_mask & ~np.isnan(strat_returns)]

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        for ax, rets, title in [
            (axes[0], all_rets, "Todos os Retornos (incl. abstencoes=0)"),
            (axes[1], active_rets, "Apenas Trades Ativos"),
        ]:
            if len(rets) == 0:
                ax.set_title(f"{title}\n(sem dados)")
                continue

            skew = sp_stats.skew(rets)
            kurt = sp_stats.kurtosis(rets)
            mean_r = np.mean(rets)
            std_r = np.std(rets, ddof=1)

            # Clip extremes for visualization (keep 99.5% of data)
            p_low, p_high = np.percentile(rets, [0.25, 99.75])
            rets_clip = rets[(rets >= p_low) & (rets <= p_high)]

            ax.hist(rets_clip, bins=80, density=True, alpha=0.7,
                    color="#3498db", edgecolor="white", linewidth=0.3)

            # Overlay normal for reference
            x_norm = np.linspace(p_low, p_high, 200)
            from scipy.stats import norm
            ax.plot(x_norm, norm.pdf(x_norm, mean_r, std_r),
                    "r--", lw=1.5, alpha=0.7, label="Normal")

            # Vertical line at mean
            ax.axvline(mean_r, color="green", ls="-", lw=1.5, alpha=0.8, label=f"Mean={mean_r:.6f}")
            ax.axvline(0, color="gray", ls="--", lw=0.8)

            # Stats box
            stats_text = (
                f"N = {len(rets)}\n"
                f"Mean = {mean_r:.6f}\n"
                f"Std = {std_r:.6f}\n"
                f"Skew = {skew:.2f}\n"
                f"Kurt = {kurt:.1f}\n"
                f"SR = {mean_r/max(std_r, 1e-12):.4f}"
            )
            ax.text(0.97, 0.97, stats_text, transform=ax.transAxes,
                    fontsize=9, verticalalignment="top", horizontalalignment="right",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor="wheat", alpha=0.8),
                    fontfamily="monospace")

            ax.set_xlabel("Retorno por barra")
            ax.set_ylabel("Densidade")
            ax.set_title(title)
            ax.legend(fontsize=8, loc="upper left")
            ax.grid(True, alpha=0.3)

        fig.suptitle("Distribuicao de Retornos da Estrategia", fontsize=13, fontweight="bold")
        plt.tight_layout()
        self._save(fig, "return_distribution.png")


# ===========================================================================
# 10. ADVANCED PIPELINE — Orquestrador Principal
# ===========================================================================
class AdvancedPipeline:
    """
    Pipeline avançada de detecção de regimes em BTC/USDT.

    Fluxo:
      1. Carregar dados (OHLCV + Fear & Greed)
      2. Dollar Bars (threshold nos primeiros 30 dias)
      3. Features (FeatureRegistry — computa só as disponíveis)
      4. Triple-Barrier Labeling
      5. Feature Selection (MDA + CPCV)
      6. CPCV Final (C(N,k) paths, features selecionadas)
      7. Meta-Labeling (split temporal 80/20)
      8. Avaliação (MDA, PSR, DSR, classification report)
      9. 8 plots diagnósticos
      10. Salvar todos os .txt reports
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.save_dir = self.config["save_dir"]

    @staticmethod
    def _load_optional_csv(
        data_dir: str, filename: str, label: str
    ) -> Optional[pd.DataFrame]:
        """Carrega CSV opcional; retorna None se nao existir."""
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["timestamp"])
            print(f"    {label} carregado: {df.shape}")
            return df
        print(f"    [AVISO] {label} nao encontrado (opcional)")
        return None

    def _load_data(self) -> tuple:
        """Carrega dados dos CSVs. Auto-fetch se btcusdt_1m.csv ausente."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, self.config["data_dir"])

        btc_path = os.path.join(data_dir, "btcusdt_1m.csv")

        # Auto-fetch: se BTC nao existe, tentar baixar
        if not os.path.exists(btc_path):
            print("    [AVISO] btcusdt_1m.csv nao encontrado. Tentando baixar...")
            try:
                from fetch_binance_data import BinanceDataFetcher
                import asyncio
                import platform
                if platform.system() == "Windows":
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                fetcher = BinanceDataFetcher(data_dir=data_dir)
                asyncio.run(fetcher.fetch_all())
            except Exception as e:
                raise FileNotFoundError(
                    f"Dados nao encontrados e download falhou: {e}"
                )

        btc_df = pd.read_csv(btc_path, parse_dates=["timestamp"])
        print(f"    BTC 1-min carregado: {btc_df.shape}")

        # CSVs opcionais
        fng_df = self._load_optional_csv(data_dir, "fear_greed.csv", "Fear & Greed")
        funding_rate_df = self._load_optional_csv(data_dir, "funding_rate.csv", "Funding Rate")
        etf_volume_df = self._load_optional_csv(data_dir, "etf_btc_volume.csv", "ETF BTC Volume")
        vix_df = self._load_optional_csv(data_dir, "vix.csv", "VIX")
        dxy_df = self._load_optional_csv(data_dir, "dxy.csv", "DXY")

        return btc_df, fng_df, funding_rate_df, etf_volume_df, vix_df, dxy_df

    def _save_txt(self, filename: str, content: str) -> None:
        """Salva conteúdo texto em arquivo .txt no save_dir."""
        path = os.path.join(self.save_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"    Relatorio salvo: {path}")

    def _rf_factory(self) -> RandomForestClassifier:
        """Cria nova instância de Random Forest com config padrão."""
        return RandomForestClassifier(
            n_estimators=self.config["rf_n_estimators"],
            max_depth=self.config["rf_max_depth"],
            min_samples_leaf=self.config["rf_min_samples_leaf"],
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=self.config["rng_seed"],
        )

    def run(self) -> Dict[str, Any]:
        """Executa o pipeline completo."""
        np.random.seed(self.config["rng_seed"])
        script_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(script_dir, self.save_dir)
        os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir
        viz = AdvancedVisualizer(save_dir)

        # == 1. CARREGAR DADOS ================================================
        print("\n" + "=" * 70)
        print("  ETAPA 1: Carregando dados")
        print("=" * 70)
        btc_df, fng_df, funding_rate_df, etf_volume_df, vix_df, dxy_df = self._load_data()

        # == 2. DOLLAR BARS ===================================================
        print("\n" + "=" * 70)
        print("  ETAPA 2: Dollar Bars (AFML Cap. 2)")
        print("=" * 70)
        bar_builder = DollarBarBuilder(
            calibration_days=self.config["dollar_bar_calibration_days"],
            bars_per_day=self.config["dollar_bars_per_day"],
        )
        threshold = bar_builder.calibrate_threshold(btc_df)
        print(f"    Threshold calibrado (30 primeiros dias): ${threshold:,.0f}")
        dollar_bars = bar_builder.transform(btc_df)
        print(f"    Dollar Bars geradas: {len(dollar_bars)}")
        print(
            f"    Ticks/barra — mediana={dollar_bars['tick_count'].median():.0f}, "
            f"min={dollar_bars['tick_count'].min()}, max={dollar_bars['tick_count'].max()}"
        )
        viz.plot_dollar_bars_sampling(dollar_bars)

        # == 3. FEATURE ENGINEERING ===========================================
        print("\n" + "=" * 70)
        print("  ETAPA 3: Feature Engineering (FeatureRegistry)")
        print("=" * 70)
        registry = FeatureRegistry()
        registry.register_defaults()

        feat_config = {
            **self.config,
            "_fng_df": fng_df,
            "_funding_rate_df": funding_rate_df,
            #"_etf_volume_df": etf_volume_df,
            "_vix_df": vix_df,
            "_dxy_df": dxy_df,
        }
        df_feat, feature_names = registry.compute_all(dollar_bars, feat_config)

        # Dropar warmup NaNs
        df_feat = df_feat.dropna(subset=feature_names).reset_index(drop=True)
        print(f"    Features calculadas: {len(feature_names)} colunas, {len(df_feat)} barras")
        print(f"    Features: {feature_names}")

        # -- Filtro de correlação: remover features com |corr| > 0.95 --------
        corr_threshold = self.config.get("corr_drop_threshold", 0.85)
        if len(feature_names) > 1:
            corr_matrix = df_feat[feature_names].corr().abs()
            upper = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape, dtype=bool), k=1)
            )
            to_drop = set()
            for col in upper.columns:
                high_corr = upper.index[upper[col] > corr_threshold].tolist()
                if high_corr:
                    # Entre col e cada feature altamente correlacionada,
                    # dropar a de menor variância
                    for hc in high_corr:
                        if hc in to_drop:
                            continue
                        var_col = df_feat[col].var()
                        var_hc = df_feat[hc].var()
                        drop_feat = hc if var_col >= var_hc else col
                        to_drop.add(drop_feat)
            if to_drop:
                feature_names = [f for f in feature_names if f not in to_drop]
                print(f"    [CORR FILTER] Removidas por |corr| > {corr_threshold}: {sorted(to_drop)}")
                print(f"    Features restantes: {len(feature_names)} -> {feature_names}")

        # == 4. TRIPLE-BARRIER LABELING =======================================
        print("\n" + "=" * 70)
        print("  ETAPA 4: Triple-Barrier Labeling (AFML Cap. 3)")
        print("=" * 70)
        labeler = TripleBarrierLabeler(self.config)
        df_labeled = labeler.apply_barriers(df_feat)
        viz.plot_triple_barrier_labels(df_labeled)

        X_all = df_labeled[feature_names].values
        y_all = df_labeled["label"].values
        t0_all = df_labeled["t0"].values
        t1_all = df_labeled["t1"].values
        close_all = df_labeled["close"].values.astype(np.float64)

        # == 5. FEATURE SELECTION (MDA + CPCV) ================================
        print("\n" + "=" * 70)
        print("  ETAPA 5: Feature Selection (MDA + CPCV)")
        print("=" * 70)
        cpcv = CPCV(self.config)
        selector = MDAFeatureSelector(self.config)
        selected_features, selection_report = selector.select(
            cpcv, self._rf_factory, X_all, y_all, t0_all, t1_all, feature_names
        )

        # Salvar relatório de feature selection
        sel_txt = "FEATURE SELECTION REPORT (MDA + CPCV)\n"
        sel_txt += "=" * 60 + "\n\n"
        sel_txt += selection_report.to_string(index=False)
        sel_txt += f"\n\nFeatures selecionadas: {selected_features}"
        sel_txt += f"\nFeatures removidas: {[f for f in feature_names if f not in selected_features]}"
        self._save_txt("feature_selection_report.txt", sel_txt)

        # Fallback: manter ao menos 3 features
        if len(selected_features) < 2:
            print("    [AVISO] Menos de 2 features selecionadas! Usando top 3 por MDA.")
            selected_features = selection_report["feature"].head(3).tolist()

        feat_indices = [feature_names.index(f) for f in selected_features]
        X_selected = X_all[:, feat_indices]

        # == 6. CPCV FINAL ====================================================
        print("\n" + "=" * 70)
        print(f"  ETAPA 6: CPCV Final ({cpcv.n_paths} paths, {len(selected_features)} features)")
        print("=" * 70)
        cpcv_results = cpcv.cross_validate(
            self._rf_factory, X_selected, y_all, t0_all, t1_all, close_all
        )

        # PSR e DSR sobre retornos OOS agregados
        oos_idx = cpcv_results["oos_indices"]
        oos_preds = cpcv_results["oos_predictions"]
        oos_close = close_all[oos_idx]
        oos_actual_ret = np.diff(oos_close, prepend=oos_close[0]) / np.maximum(
            oos_close, 1e-12
        )
        oos_strat_ret = ModelEvaluator.compute_strategy_returns(
            oos_preds, oos_actual_ret,
            fee_maker=self.config["fee_maker"],
            fee_taker=self.config["fee_taker"],
            fee_mode=self.config["fee_mode"],
        )
        sr_oos = np.mean(oos_strat_ret) / max(np.std(oos_strat_ret, ddof=1), 1e-12)
        psr = ModelEvaluator.probabilistic_sharpe_ratio(oos_strat_ret)
        dsr = ModelEvaluator.deflated_sharpe_ratio(oos_strat_ret, cpcv.n_paths)

        print(f"\n    OOS Agregado: SR={sr_oos:.4f}, PSR={psr:.4f}, DSR={dsr:.4f}")

        # MDA final
        print("\n    Calculando MDA final com modelos do CPCV...")
        mda_final = ModelEvaluator.mda_from_cpcv(
            cpcv_results, X_selected, y_all, selected_features,
            n_repeats=self.config["mda_n_repeats"],
            rng_seed=self.config["rng_seed"],
        )

        # Plots CPCV
        viz.plot_cpcv_sharpe_distribution(
            cpcv_results["path_sharpes"], psr, dsr
        )
        viz.plot_cpcv_accuracy_distribution(
            cpcv_results["path_accuracies"], cpcv_results["path_f1s"]
        )
        viz.plot_feature_importance_mda(mda_final)
        viz.plot_confusion_matrix(
            cpcv_results["oos_true"], cpcv_results["oos_predictions"]
        )

        # == 7. META-LABELING =================================================
        print("\n" + "=" * 70)
        print("  ETAPA 7: Meta-Labeling (AFML Cap. 3.6)")
        print("=" * 70)
        n = len(df_labeled)
        split_idx = int(n * self.config["train_ratio"])
        X_train = X_selected[:split_idx]
        X_test = X_selected[split_idx:]
        y_train = y_all[:split_idx]
        y_test = y_all[split_idx:]

        close_train = close_all[:split_idx]
        meta = MetaLabeler(self.config)
        fit_report = meta.fit(X_train, y_train, close_train=close_train)
        final_preds, meta_probs, primary_preds = meta.predict(X_test)

        # Predições de ambos meta-models (para comparação)
        both_results = meta.predict_both(X_test)

        # Predições no treino (para o plot de zoom)
        train_final, _, train_primary = meta.predict(X_train)

        # == 8. AVALIACAO =====================================================
        print("\n" + "=" * 70)
        print("  ETAPA 8: Avaliacao Final")
        print("=" * 70)

        close_test = close_all[split_idx:]
        actual_ret_test = np.diff(close_test, prepend=close_test[0]) / np.maximum(
            close_test, 1e-12
        )
        strat_ret_test = ModelEvaluator.compute_strategy_returns(
            final_preds, actual_ret_test,
            fee_maker=self.config["fee_maker"],
            fee_taker=self.config["fee_taker"],
            fee_mode=self.config["fee_mode"],
        )
        sr_test = np.mean(strat_ret_test) / max(np.std(strat_ret_test, ddof=1), 1e-12)
        psr_test = ModelEvaluator.probabilistic_sharpe_ratio(strat_ret_test)
        dsr_test = ModelEvaluator.deflated_sharpe_ratio(strat_ret_test, cpcv.n_paths)

        meta_f1 = f1_score(y_test, final_preds, average="weighted", zero_division=0)
        meta_acc = accuracy_score(y_test, final_preds)
        cls_report = classification_report(y_test, final_preds, zero_division=0)

        print(f"    Meta-Label Accuracy ({meta.meta_model_name}): {meta_acc:.4f}")
        print(f"    Meta-Label F1: {meta_f1:.4f}")
        print(f"    Sharpe Ratio (teste): {sr_test:.4f}")
        print(f"    PSR: {psr_test:.4f}")
        print(f"    DSR: {dsr_test:.4f}")
        print(f"\n{cls_report}")

        # Comparação RF vs LR
        comparison_results: Dict[str, Dict[str, Any]] = {}
        for name in ["RF", "LR"]:
            res = both_results[name]
            s_ret = ModelEvaluator.compute_strategy_returns(
                res["final"], actual_ret_test,
                fee_maker=self.config["fee_maker"],
                fee_taker=self.config["fee_taker"],
                fee_mode=self.config["fee_mode"],
            )
            s_sr = np.mean(s_ret) / max(np.std(s_ret, ddof=1), 1e-12)
            s_psr = ModelEvaluator.probabilistic_sharpe_ratio(s_ret)
            s_dsr = ModelEvaluator.deflated_sharpe_ratio(s_ret, cpcv.n_paths)
            s_acc = accuracy_score(y_test, res["final"])
            s_f1 = f1_score(y_test, res["final"], average="weighted", zero_division=0)
            s_cls = classification_report(
                y_test, res["final"], output_dict=True, zero_division=0
            )
            s_rets_clean = s_ret[~np.isnan(s_ret)]
            s_skew = float(sp_stats.skew(s_rets_clean))
            s_kurt = float(sp_stats.kurtosis(s_rets_clean))
            n_active = int(np.sum(res["final"] != 0))
            conf = res["meta_confidence"]
            comparison_results[name] = {
                "sr": s_sr, "psr": s_psr, "dsr": s_dsr,
                "accuracy": s_acc, "f1": s_f1,
                "precision_m1": s_cls.get("-1", {}).get("precision", 0.0),
                "precision_p1": s_cls.get("1", {}).get("precision", 0.0),
                "recall_m1": s_cls.get("-1", {}).get("recall", 0.0),
                "recall_p1": s_cls.get("1", {}).get("recall", 0.0),
                "skewness": s_skew, "kurtosis": s_kurt,
                "n_active": n_active,
                "cum_ret_pct": float(np.sum(s_ret)) * 100,
                "strat_ret": s_ret,
                "conf_mean": float(np.mean(conf)),
                "conf_std": float(np.std(conf)),
                "conf_min": float(np.min(conf)),
                "conf_p25": float(np.percentile(conf, 25)),
                "conf_p50": float(np.percentile(conf, 50)),
                "conf_p75": float(np.percentile(conf, 75)),
                "conf_max": float(np.max(conf)),
            }
            tag = " <<<" if name == meta.meta_model_name else ""
            print(f"    [{name}] SR={s_sr:.4f}, DSR={s_dsr:.4f}, "
                  f"Prec(-1)={comparison_results[name]['precision_m1']:.2f}, "
                  f"Prec(+1)={comparison_results[name]['precision_p1']:.2f}, "
                  f"N={n_active}{tag}")

        # == 9. VISUALIZACOES =================================================
        print("\n" + "=" * 70)
        print("  ETAPA 9: Gerando visualizacoes")
        print("=" * 70)

        viz.plot_cumulative_returns(
            strat_ret_test, actual_ret_test, psr_test, dsr_test
        )

        timestamps_test = df_labeled["timestamp"].values[split_idx:]
        viz.plot_portfolio_equity(
            strat_ret_test, close_test, timestamps_test,
            psr_test, dsr_test, sr_test,
        )

        viz.plot_2day_zoom(
            df_labeled=df_labeled,
            final_preds=final_preds,
            primary_preds=primary_preds,
            y_true=y_test,
            test_start_idx=split_idx,
            train_preds=train_final,
            train_true=y_train,
        )

        viz.plot_return_concentration(strat_ret_test, final_preds)

        viz.plot_return_distribution(strat_ret_test, final_preds)

        # Threshold grid — RF vs LR side-by-side
        threshold_grid = [0.50, 0.52, 0.53, 0.55, 0.57, 0.60, 0.62, 0.65, 0.7]
        meta_conf_dict = {
            name: both_results[name]["meta_confidence"]
            for name in ["RF", "LR"]
        }
        viz.plot_threshold_grid(
            meta_confidence_dict=meta_conf_dict,
            primary_preds=primary_preds,
            actual_returns=actual_ret_test,
            y_true=y_test,
            thresholds=threshold_grid,
            n_trials=cpcv.n_paths,
            fee_maker=self.config["fee_maker"],
            fee_taker=self.config["fee_taker"],
            fee_mode=self.config["fee_mode"],
        )

        # == 10. RELATORIOS TXT ===============================================
        print("\n" + "=" * 70)
        print("  ETAPA 10: Salvando relatorios")
        print("=" * 70)

        # Config
        config_txt = "CONFIGURACAO DO PIPELINE\n" + "=" * 60 + "\n\n"
        for k, v in self.config.items():
            if not k.startswith("_"):
                config_txt += f"  {k}: {v}\n"
        self._save_txt("config.txt", config_txt)

        # Pipeline summary
        summary = "PIPELINE SUMMARY\n" + "=" * 60 + "\n\n"
        summary += f"  Dollar Bars: {len(dollar_bars)}\n"
        summary += f"  Dollar Bar Threshold: ${threshold:,.0f}\n"
        summary += f"  Features totais: {len(feature_names)}\n"
        summary += f"  Features selecionadas: {len(selected_features)} -> {selected_features}\n"
        summary += f"  Barras rotuladas: {len(df_labeled)}\n"
        summary += f"  Distribuicao labels: {dict(zip(*np.unique(y_all, return_counts=True)))}\n"
        summary += f"  Train/Test split: {split_idx}/{n - split_idx}\n"
        summary += f"\n  CPCV ({cpcv.n_paths} paths):\n"
        summary += f"    Accuracy: {cpcv_results['mean_accuracy']:.4f} +/- {cpcv_results['std_accuracy']:.4f}\n"
        summary += f"    F1:       {cpcv_results['mean_f1']:.4f} +/- {cpcv_results['std_f1']:.4f}\n"
        summary += f"    Sharpe:   {cpcv_results['mean_sharpe']:.4f} +/- {cpcv_results['std_sharpe']:.4f}\n"
        summary += f"\n  Meta-Labeling (teste, modelo={meta.meta_model_name}):\n"
        summary += f"    Accuracy: {meta_acc:.4f}\n"
        summary += f"    F1:       {meta_f1:.4f}\n"
        summary += f"    Sharpe:   {sr_test:.4f}\n"
        summary += f"    PSR:      {psr_test:.4f}\n"
        summary += f"    DSR:      {dsr_test:.4f}\n"
        self._save_txt("pipeline_summary.txt", summary)

        # CPCV results
        cpcv_txt = "CPCV RESULTS — ALL PATHS\n" + "=" * 60 + "\n\n"
        cpcv_txt += f"{'Path':>6s} {'Accuracy':>10s} {'F1':>10s} {'Sharpe':>10s}\n"
        cpcv_txt += "-" * 38 + "\n"
        for i in range(cpcv.n_paths):
            cpcv_txt += (
                f"{i + 1:>6d} "
                f"{cpcv_results['path_accuracies'][i]:>10.4f} "
                f"{cpcv_results['path_f1s'][i]:>10.4f} "
                f"{cpcv_results['path_sharpes'][i]:>10.4f}\n"
            )
        cpcv_txt += "-" * 38 + "\n"
        cpcv_txt += (
            f"{'Mean':>6s} "
            f"{cpcv_results['mean_accuracy']:>10.4f} "
            f"{cpcv_results['mean_f1']:>10.4f} "
            f"{cpcv_results['mean_sharpe']:>10.4f}\n"
        )
        cpcv_txt += (
            f"{'Std':>6s} "
            f"{cpcv_results['std_accuracy']:>10.4f} "
            f"{cpcv_results['std_f1']:>10.4f} "
            f"{cpcv_results['std_sharpe']:>10.4f}\n"
        )
        self._save_txt("cpcv_results.txt", cpcv_txt)

        # CPCV Sharpe distribution
        sharpes = cpcv_results["path_sharpes"]
        sharpe_txt = "CPCV SHARPE DISTRIBUTION\n" + "=" * 60 + "\n\n"
        sharpe_txt += f"  N paths: {len(sharpes)}\n"
        sharpe_txt += f"  Mean:    {np.mean(sharpes):.6f}\n"
        sharpe_txt += f"  Std:     {np.std(sharpes):.6f}\n"
        sharpe_txt += f"  Min:     {np.min(sharpes):.6f}\n"
        sharpe_txt += f"  Max:     {np.max(sharpes):.6f}\n"
        sharpe_txt += f"  Median:  {np.median(sharpes):.6f}\n"
        for p in [5, 25, 50, 75, 95]:
            sharpe_txt += f"  P{p:02d}:     {np.percentile(sharpes, p):.6f}\n"
        sharpe_txt += f"\n  PSR (OOS agregado): {psr:.4f}\n"
        sharpe_txt += f"  DSR (OOS agregado): {dsr:.4f}\n"
        self._save_txt("cpcv_sharpe_distribution.txt", sharpe_txt)

        # Classification report
        self._save_txt("classification_report.txt",
                       "CLASSIFICATION REPORT (Meta-Label, Teste)\n"
                       + "=" * 60 + "\n\n" + cls_report)

        # Confusion matrix
        cm = confusion_matrix(y_test, final_preds)
        cm_txt = "CONFUSION MATRIX (Meta-Label, Teste)\n" + "=" * 60 + "\n\n"
        cm_txt += str(cm) + "\n"
        cm_txt += f"\nLabels: {sorted(set(y_test) | set(final_preds))}\n"
        self._save_txt("confusion_matrix.txt", cm_txt)

        # MDA importance
        mda_txt = "MDA FEATURE IMPORTANCE (CPCV)\n" + "=" * 60 + "\n\n"
        mda_txt += mda_final.to_string(index=False)
        self._save_txt("mda_importance.txt", mda_txt)

        # PSR/DSR report
        psr_txt = "PSR / DSR REPORT\n" + "=" * 60 + "\n\n"
        psr_txt += f"  Sharpe Ratio (teste meta-label): {sr_test:.6f}\n"
        psr_txt += f"  PSR (teste): {psr_test:.6f}\n"
        psr_txt += f"  DSR (teste, {cpcv.n_paths} trials): {dsr_test:.6f}\n"
        psr_txt += f"\n  Sharpe Ratio (OOS CPCV agregado): {sr_oos:.6f}\n"
        psr_txt += f"  PSR (OOS CPCV): {psr:.6f}\n"
        psr_txt += f"  DSR (OOS CPCV): {dsr:.6f}\n"
        test_rets = strat_ret_test[~np.isnan(strat_ret_test)]
        psr_txt += f"\n  Skewness: {sp_stats.skew(test_rets):.6f}\n"
        psr_txt += f"  Kurtosis (excess): {sp_stats.kurtosis(test_rets):.6f}\n"
        psr_txt += f"  N observacoes: {len(test_rets)}\n"
        self._save_txt("psr_dsr_report.txt", psr_txt)

        # Meta-labeler comparison: RF vs LR
        cmp_txt = "META-LABELER COMPARISON: RF vs Logistic Regression\n"
        cmp_txt += "=" * 60 + "\n\n"
        cmp_txt += f"  Sample Weights: {'Yes (|bar_return|, normalized)' if close_train is not None else 'No'}\n"
        cmp_txt += f"  Winner: {meta.meta_model_name}\n"
        cmp_txt += f"  LIMITE_DECISORIO: {LIMITE_DECISORIO}\n"
        # In-sample from fit_report
        cmp_txt += "\n  IN-SAMPLE:\n"
        cmp_txt += f"  {'':>20s} {'RF':>10s} {'LR':>10s}\n"
        cmp_txt += f"  {'Accuracy':>20s} {fit_report['RF']['accuracy']:>10.4f} {fit_report['LR']['accuracy']:>10.4f}\n"
        cmp_txt += f"  {'Precision(1)':>20s} {fit_report['RF']['precision_1']:>10.4f} {fit_report['LR']['precision_1']:>10.4f}\n"
        cmp_txt += f"  {'Meta dist':>20s} {str(fit_report['meta_y_dist']):>20s}\n"
        # Test set comparison
        cmp_txt += f"\n  TEST SET:\n"
        cmp_txt += f"  {'':>20s} {'RF':>10s} {'LR':>10s}\n"
        cmp_txt += "  " + "-" * 42 + "\n"
        for key, label in [
            ("accuracy", "Accuracy"), ("f1", "F1"),
            ("precision_m1", "Precision -1"), ("precision_p1", "Precision +1"),
            ("recall_m1", "Recall -1"), ("recall_p1", "Recall +1"),
            ("sr", "SR"), ("psr", "PSR"), ("dsr", "DSR"),
            ("skewness", "Skewness"), ("kurtosis", "Kurtosis"),
            ("n_active", "N_active"), ("cum_ret_pct", "CumRet%"),
        ]:
            rf_v = comparison_results["RF"][key]
            lr_v = comparison_results["LR"][key]
            if key == "n_active":
                cmp_txt += f"  {label:>20s} {rf_v:>10d} {lr_v:>10d}\n"
            else:
                cmp_txt += f"  {label:>20s} {rf_v:>10.4f} {lr_v:>10.4f}\n"
        # Confidence distribution
        cmp_txt += f"\n  CONFIDENCE DISTRIBUTION:\n"
        cmp_txt += f"  {'':>20s} {'RF':>10s} {'LR':>10s}\n"
        cmp_txt += "  " + "-" * 42 + "\n"
        for key, label in [
            ("conf_mean", "Mean"), ("conf_std", "Std"),
            ("conf_min", "Min"), ("conf_p25", "P25"),
            ("conf_p50", "P50"), ("conf_p75", "P75"),
            ("conf_max", "Max"),
        ]:
            rf_v = comparison_results["RF"][key]
            lr_v = comparison_results["LR"][key]
            cmp_txt += f"  {label:>20s} {rf_v:>10.4f} {lr_v:>10.4f}\n"
        self._save_txt("meta_comparison.txt", cmp_txt)

        # == EXPORTAR MODELO TREINADO =========================================
        artifacts = {
            "config": self.config,
            "threshold": threshold,
            "selected_features": selected_features,
            "feature_names": feature_names,
            "meta_labeler": meta,
        }
        model_path = os.path.join(save_dir, "trained_model.joblib")
        joblib.dump(artifacts, model_path)
        print(f"    Modelo salvo: {model_path}")

        # == RESULTADO FINAL ==================================================
        print("\n" + "=" * 70)
        print("  PIPELINE CONCLUIDA")
        print("=" * 70)
        print(f"    Resultados salvos em: {save_dir}")
        print(f"    8 plots PNG + 9 relatorios TXT + modelo .joblib")

        return {
            "dollar_bars": len(dollar_bars),
            "features_total": len(feature_names),
            "features_selected": selected_features,
            "labeled_bars": len(df_labeled),
            "cpcv_paths": cpcv.n_paths,
            "cpcv_mean_accuracy": cpcv_results["mean_accuracy"],
            "cpcv_mean_f1": cpcv_results["mean_f1"],
            "cpcv_mean_sharpe": cpcv_results["mean_sharpe"],
            "meta_accuracy": meta_acc,
            "meta_f1": meta_f1,
            "sharpe_test": sr_test,
            "psr_test": psr_test,
            "dsr_test": dsr_test,
        }


# ===========================================================================
# MAIN
# ===========================================================================
def main() -> None:
    """
    Ponto de entrada standalone.

    Executa a pipeline avançada com configuração padrão e salva todos
    os resultados em save_point_advanced/.
    """
    print("=" * 70)
    print("  PIPELINE AVANCADA — Deteccao de Regimes BTC/USDT")
    print("  Baseado em Lopez de Prado (AFML 2018 + MLAM 2020)")
    print("  CPCV obrigatorio | SavGol causal | Feature Selection | DSR")
    print("=" * 70)

    pipeline = AdvancedPipeline()
    results = pipeline.run()

    print("\n" + "=" * 70)
    print("  RESUMO FINAL")
    print("=" * 70)
    for k, v in results.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.4f}")
        else:
            print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
