#!/usr/bin/env python3
# coding: utf-8
"""
=============================================================================
Pipeline de ML para Classificação de Criptoativos — Metodologia Marcos López
de Prado ("Advances in Financial Machine Learning", 2018).
=============================================================================

Implementa:
  1. Dollar Bars (barras de dólar) — amostragem information-driven (Cap. 2)
  2. Diferenciação Fracionária FFD — estacionaridade com memória (Cap. 5)
  3. Features de microestrutura: VPIN, Kyle λ, Roll Spread, LZ Entropy (Cap. 18)
  4. Triple-Barrier Method — rotulagem dinâmica baseada em volatilidade (Cap. 3)
  5. Meta-Labeling — filtragem de falsos positivos (Cap. 3.6)
  6. Purged K-Fold CV com Embargo — validação sem leakage (Cap. 7)
  7. MDA Feature Importance — importância por permutação (Cap. 8)
  8. Probabilistic Sharpe Ratio — significância estatística (Cap. 14)

Autor: Pipeline gerado seguindo as "Leis de Marcos".
"""

import os
import warnings
from typing import List, Tuple, Optional, Callable, Dict

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # backend não-interativo para salvar PNGs
import matplotlib.pyplot as plt
from scipy import stats as sp_stats
from scipy.signal import savgol_filter, savgol_coeffs
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# Tenta importar statsmodels para teste ADF; se não disponível, avisa
try:
    from statsmodels.tsa.stattools import adfuller

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    warnings.warn(
        "statsmodels não encontrado — teste ADF será ignorado. "
        "Instale com: pip install statsmodels>=0.13.0"
    )

# ---------------------------------------------------------------------------
# Constantes globais
# ---------------------------------------------------------------------------
RNG_SEED: int = 42
DATA_DIR: str = "data"
SAVE_DIR: str = "save_point_marcos"
TRAIN_RATIO: float = 0.80

# Dollar bars
DOLLAR_BAR_CALIBRATION_DAYS: int = 30
DOLLAR_BARS_PER_DAY: int = 50  # threshold = median_daily_dollar_vol / N

# Feature engineering
FFD_D: float = 0.4  # grau de diferenciação fracionária
FFD_THRESHOLD: float = 1e-4  # truncamento de pesos FFD
VPIN_N_BUCKETS: int = 50  # buckets para VPIN (~1 dia de dollar bars)
KYLE_WINDOW: int = 20  # janela para Lambda de Kyle
ROLL_WINDOW: int = 20  # janela para Roll Spread
LZ_WINDOW: int = 100  # janela para entropia Lempel-Ziv

# Triple barrier
VOL_LOOKBACK: int = 20  # janela EWM para volatilidade diária
PT_MULTIPLIER: float = 2.0  # barreira de profit-taking = pt * vol
SL_MULTIPLIER: float = 2.0  # barreira de stop-loss = sl * vol
MAX_HOLDING_BARS: int = 50  # barreira vertical (~1 dia de dollar bars)

# Purged K-Fold
N_FOLDS: int = 5
PURGE_PCT: float = 0.01
EMBARGO_PCT: float = 0.01

# Random Forest
RF_N_ESTIMATORS: int = 500
RF_MAX_DEPTH: int = 6
RF_MIN_SAMPLES_LEAF: int = 50

# Savitzky-Golay (experimental)
SAVGOL_WINDOW: int = 21  # janela do filtro (deve ser ímpar)
SAVGOL_POLYORDER: int = 3  # ordem do polinômio local

# RSI (experimental)
RSI_PERIOD: int = 14  # período clássico de Wilder


# ==========================================================================
# 1. DOLLAR BARS — Cap. 2 AFML
# ==========================================================================
class DollarBarBuilder:
    """
    Converte barras de tempo (1 minuto) em Dollar Bars.

    ── Por que barras de dólar? ──────────────────────────────────────────
    Barras de tempo (1m, 5m, 1h) amostram em intervalos fixos de relógio,
    gerando:
      • Sobre-amostragem em períodos de baixa atividade (ruído).
      • Sub-amostragem em períodos de alta atividade (perda de informação).

    Dollar bars amostram quando o volume financeiro acumulado (preço × volume)
    atinge um limiar fixo.  Isso recupera propriedades IID nos retornos
    porque cada barra representa a mesma "quantidade de informação" medida
    em dólares transacionados — conforme demonstrado empiricamente por
    López de Prado (AFML, Capítulo 2, Teorema 2.1).

    ── Implementação vetorizada ──────────────────────────────────────────
    Em vez de iterar linha a linha (~1M de linhas), calculamos:
      1. dollar_i = typical_price_i × volume_i  (vetorizado)
      2. cum_dollar = cumsum(dollar_i)
      3. Encontramos os índices de corte com np.searchsorted no vetor de
         limiares [threshold, 2*threshold, 3*threshold, ...].
      4. Agregamos OHLCV por grupo (bar_id) usando groupby.

    Complexidade: O(N) para cumsum + O(K log N) para searchsorted, onde
    K = número de barras (~36k) e N = número de ticks (~1M).
    """

    def __init__(
        self,
        threshold: Optional[float] = None,
        calibration_days: int = DOLLAR_BAR_CALIBRATION_DAYS,
        bars_per_day: int = DOLLAR_BARS_PER_DAY,
    ):
        self.threshold = threshold
        self.calibration_days = calibration_days
        self.bars_per_day = bars_per_day

    # ------------------------------------------------------------------
    def calibrate_threshold(self, df: pd.DataFrame) -> float:
        """
        Calibra o limiar de dollar volume usando os primeiros N dias.

        threshold = median(dollar_volume_diário) / bars_per_day

        Isso produz aprox. `bars_per_day` barras por dia de negociação,
        resultando em um dataset de tamanho adequado para ML.
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        # typical_price como proxy de preço médio da barra
        df["dollar_vol"] = (
            (df["high"] + df["low"] + df["close"]) / 3.0 * df["volume"]
        )
        daily = df.groupby("date")["dollar_vol"].sum()
        # Usar apenas os primeiros N dias para calibração (evita look-ahead)
        daily_cal = daily.iloc[: self.calibration_days]
        median_daily = daily_cal.median()
        self.threshold = median_daily / self.bars_per_day
        return self.threshold

    # ------------------------------------------------------------------
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma barras de 1 minuto em Dollar Bars.

        Parâmetros
        ----------
        df : DataFrame com colunas [timestamp, open, high, low, close, volume]

        Retorna
        -------
        DataFrame de Dollar Bars com colunas:
            [timestamp, open, high, low, close, volume, dollar_volume,
             vwap, tick_count]
        """
        if self.threshold is None:
            self.calibrate_threshold(df)

        # 1) Calcular dollar volume por tick (vetorizado)
        typical_price = (
            df["high"].values + df["low"].values + df["close"].values
        ) / 3.0
        volume = df["volume"].values
        dollar_vol = typical_price * volume

        # 2) Soma acumulada
        cum_dollar = np.cumsum(dollar_vol)

        # 3) Encontrar fronteiras das barras via searchsorted
        n_bars_max = int(cum_dollar[-1] / self.threshold) + 1
        thresholds = np.arange(1, n_bars_max + 1) * self.threshold
        # Índices onde cada limiar é atingido (lado direito = inclusive)
        boundary_indices = np.searchsorted(cum_dollar, thresholds, side="right")
        # Remover duplicatas e índices fora do range
        boundary_indices = np.unique(boundary_indices)
        boundary_indices = boundary_indices[boundary_indices < len(df)]
        boundary_indices = boundary_indices[boundary_indices > 0]

        # 4) Criar bar_id para cada tick
        bar_id = np.zeros(len(df), dtype=np.int64)
        prev = 0
        for i, bnd in enumerate(boundary_indices):
            bar_id[prev:bnd] = i
            prev = bnd
        # Ticks restantes (última barra incompleta) — descartados
        bar_id[prev:] = -1  # marcamos como -1 para remover

        # Montar DataFrame temporário para agregação
        tmp = pd.DataFrame(
            {
                "bar_id": bar_id,
                "timestamp": df["timestamp"].values,
                "open": df["open"].values,
                "high": df["high"].values,
                "low": df["low"].values,
                "close": df["close"].values,
                "volume": volume,
                "dollar_vol": dollar_vol,
            }
        )
        tmp = tmp[tmp["bar_id"] >= 0]  # remover barra incompleta

        # 5) Agregar por bar_id
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

        # VWAP = dollar_volume / volume
        bars["vwap"] = bars["dollar_volume"] / bars["volume"].replace(0, np.nan)
        bars = bars.reset_index(drop=True)
        return bars


# ==========================================================================
# 2. FEATURE ENGINE — Cap. 5 e 18 AFML
# ==========================================================================
class FeatureEngine:
    """
    Calcula features avançadas sobre Dollar Bars seguindo AFML.

    Features implementadas:
      • FFD Close (d=0.4) — preço fracionariamente diferenciado
      • VPIN — probabilidade de informed trading sincronizada por volume
      • Kyle Lambda — impacto de preço por unidade de volume
      • Roll Spread — spread efetivo estimado
      • Lempel-Ziv Entropy — complexidade do fluxo de ordens
      • Fear & Greed — sentimento macro (feature exógena)
      • Volatilidade e momentum tradicionais
    """

    def __init__(
        self,
        ffd_d: float = FFD_D,
        ffd_threshold: float = FFD_THRESHOLD,
        vpin_n_buckets: int = VPIN_N_BUCKETS,
        kyle_window: int = KYLE_WINDOW,
        roll_window: int = ROLL_WINDOW,
        lz_window: int = LZ_WINDOW,
        use_savgol: bool = False,
        use_savgol_causal: bool = False,
        savgol_window: int = SAVGOL_WINDOW,
        savgol_polyorder: int = SAVGOL_POLYORDER,
        use_rsi: bool = False,
        rsi_period: int = RSI_PERIOD,
    ):
        self.ffd_d = ffd_d
        self.ffd_threshold = ffd_threshold
        self.vpin_n_buckets = vpin_n_buckets
        self.kyle_window = kyle_window
        self.roll_window = roll_window
        self.lz_window = lz_window
        self.use_savgol = use_savgol
        self.use_savgol_causal = use_savgol_causal
        self.savgol_window = savgol_window
        self.savgol_polyorder = savgol_polyorder
        self.use_rsi = use_rsi
        self.rsi_period = rsi_period

    # ------------------------------------------------------------------
    # 2a. Diferenciação Fracionária (FFD) — Cap. 5
    # ------------------------------------------------------------------
    @staticmethod
    def _get_ffd_weights(d: float, threshold: float) -> np.ndarray:
        """
        Calcula os pesos para FFD (Fixed-Width Window Fractional Differentiation).

        ── Teoria ──────────────────────────────────────────────────────────
        A diferenciação inteira (d=1) remove TODA a memória da série:
        retornos log são estacionários mas "esquecem" suportes/resistências.

        A diferenciação fracionária com d < 1 aplica o operador:
            (1 - B)^d = Σ_{k=0}^{∞} w_k B^k
        onde B é o operador de backshift e os pesos seguem:
            w_0 = 1
            w_k = -w_{k-1} × (d - k + 1) / k

        Truncamos quando |w_k| < threshold, dando uma janela finita.
        Com d=0.4 e threshold=1e-4, a janela é tipicamente ~50-100 termos.

        O resultado preserva correlação com os níveis originais (o modelo
        "lembra" de suportes e resistências) enquanto atinge estacionaridade
        (ADF p-value < 0.05).
        """
        weights = [1.0]
        k = 1
        while True:
            w_k = -weights[-1] * (d - k + 1) / k
            if abs(w_k) < threshold:
                break
            weights.append(w_k)
            k += 1
        return np.array(weights[::-1])  # invertido para convolução

    def fractional_diff(self, series: pd.Series) -> pd.Series:
        """
        Aplica FFD à série de preços.

        Retorna série fracionariamente diferenciada, com NaN nas primeiras
        (window_size - 1) posições (warmup).
        """
        weights = self._get_ffd_weights(self.ffd_d, self.ffd_threshold)
        width = len(weights)
        values = series.values.astype(np.float64)
        n = len(values)

        result = np.full(n, np.nan)
        for i in range(width - 1, n):
            window = values[i - width + 1 : i + 1]
            result[i] = np.dot(weights, window)

        ffd_series = pd.Series(result, index=series.index, name="ffd_close")

        # Validação ADF (se statsmodels disponível)
        if HAS_STATSMODELS:
            clean = ffd_series.dropna()
            if len(clean) > 100:
                adf_stat, adf_pvalue, *_ = adfuller(clean.values, maxlag=1)
                print(
                    f"  [FFD] d={self.ffd_d:.2f}, janela={width}, "
                    f"ADF stat={adf_stat:.4f}, p-value={adf_pvalue:.6f} "
                    f"({'ESTACIONÁRIA' if adf_pvalue < 0.05 else 'NÃO ESTACIONÁRIA'})"
                )
        return ffd_series

    # ------------------------------------------------------------------
    # 2b. VPIN — Cap. 18
    # ------------------------------------------------------------------
    def compute_vpin(self, df: pd.DataFrame) -> pd.Series:
        """
        Volume-Synchronized Probability of Informed Trading.

        ── Teoria ──────────────────────────────────────────────────────────
        VPIN mede a "toxicidade" do fluxo de ordens: quando compradores
        informados dominam, o VPIN sobe — sinalizando risco de crash ou
        movimento abrupto ANTES que aconteça.

        Para criptoativos como BTC, VPIN alto precedeu historicamente
        flash crashes e liquidações em cascata.

        ── Algoritmo (Bulk Volume Classification) ──────────────────────────
        1. Classificar volume de cada barra como buy/sell sem dados de tick:
           Z = (close - open) / std(close - open)
           buy_pct = Φ(Z)  (CDF normal)
           buy_vol = volume × buy_pct
           sell_vol = volume × (1 - buy_pct)

        2. Preencher buckets de volume fixo V_B sequencialmente.

        3. VPIN = média(|V_buy_i - V_sell_i| / V_B) sobre últimos N buckets.
        """
        close = df["close"].values.astype(np.float64)
        open_ = df["open"].values.astype(np.float64)
        volume = df["volume"].values.astype(np.float64)

        # Classificação de volume (Bulk Volume Classification)
        dp = close - open_
        sigma = np.nanstd(dp)
        if sigma < 1e-12:
            sigma = 1.0
        z = dp / sigma
        buy_pct = sp_stats.norm.cdf(z)
        buy_vol = volume * buy_pct
        sell_vol = volume * (1.0 - buy_pct)

        # Tamanho do bucket = volume total / n_buckets
        total_vol = np.nansum(volume)
        bucket_size = total_vol / max(self.vpin_n_buckets * 10, 1)

        # Preencher buckets
        bucket_buy = 0.0
        bucket_sell = 0.0
        bucket_total = 0.0
        imbalances: List[float] = []

        for i in range(len(volume)):
            remaining_buy = buy_vol[i]
            remaining_sell = sell_vol[i]

            while remaining_buy + remaining_sell > 1e-12:
                space = bucket_size - bucket_total
                fill = min(remaining_buy + remaining_sell, space)
                if remaining_buy + remaining_sell > 1e-12:
                    ratio = remaining_buy / (remaining_buy + remaining_sell)
                else:
                    ratio = 0.5
                fill_buy = fill * ratio
                fill_sell = fill * (1 - ratio)

                bucket_buy += fill_buy
                bucket_sell += fill_sell
                bucket_total += fill
                remaining_buy -= fill_buy
                remaining_sell -= fill_sell

                if bucket_total >= bucket_size - 1e-12:
                    imbalances.append(abs(bucket_buy - bucket_sell) / bucket_size)
                    bucket_buy = 0.0
                    bucket_sell = 0.0
                    bucket_total = 0.0

        # Mapear VPIN de volta aos índices das barras
        # Cada barra recebe o VPIN calculado até aquele ponto
        n_bars = len(df)
        vpin_values = np.full(n_bars, np.nan)
        n_buckets = self.vpin_n_buckets

        # Recalcular incrementalmente para mapeamento correto
        bucket_buy2 = 0.0
        bucket_sell2 = 0.0
        bucket_total2 = 0.0
        imb_list: List[float] = []

        for i in range(n_bars):
            rb = buy_vol[i]
            rs = sell_vol[i]
            while rb + rs > 1e-12:
                space = bucket_size - bucket_total2
                fill = min(rb + rs, space)
                if rb + rs > 1e-12:
                    ratio = rb / (rb + rs)
                else:
                    ratio = 0.5
                fb = fill * ratio
                fs = fill * (1 - ratio)
                bucket_buy2 += fb
                bucket_sell2 += fs
                bucket_total2 += fill
                rb -= fb
                rs -= fs
                if bucket_total2 >= bucket_size - 1e-12:
                    imb_list.append(abs(bucket_buy2 - bucket_sell2) / bucket_size)
                    bucket_buy2 = 0.0
                    bucket_sell2 = 0.0
                    bucket_total2 = 0.0

            if len(imb_list) >= n_buckets:
                vpin_values[i] = np.mean(imb_list[-n_buckets:])

        return pd.Series(vpin_values, index=df.index, name="vpin")

    # ------------------------------------------------------------------
    # 2c. Kyle Lambda — Cap. 18
    # ------------------------------------------------------------------
    def compute_kyle_lambda(self, df: pd.DataFrame) -> pd.Series:
        """
        Lambda de Kyle — medida de impacto de preço (iliquidez).

        ── Teoria ──────────────────────────────────────────────────────────
        Kyle (1985) modela a relação linear entre fluxo de ordens e preço:
            Δp = λ × signed_volume + ε

        λ alto → cada unidade de volume move mais o preço → mercado ilíquido.
        Para ETH e BTC em momentos de stress, λ explode — tornando-o um
        indicador antecedente de slippage extremo.

        ── Implementação ───────────────────────────────────────────────────
        Regressão rolling de |Δp| sobre |signed_volume|:
          signed_vol_i = volume_i × sign(close_i - open_i)
          λ = coef. angular via OLS em janela de `kyle_window` barras.
        """
        close = df["close"].values.astype(np.float64)
        open_ = df["open"].values.astype(np.float64)
        volume = df["volume"].values.astype(np.float64)

        dp = np.abs(close - np.roll(close, 1))
        dp[0] = np.nan
        sign = np.sign(close - open_)
        signed_vol = np.abs(volume * sign)

        n = len(df)
        w = self.kyle_window
        kyle = np.full(n, np.nan)

        for i in range(w, n):
            y = dp[i - w + 1 : i + 1]
            x = signed_vol[i - w + 1 : i + 1]
            mask = ~(np.isnan(y) | np.isnan(x))
            if mask.sum() < w // 2:
                continue
            y_c, x_c = y[mask], x[mask]
            if np.std(x_c) < 1e-12:
                continue
            # OLS: λ = cov(y, x) / var(x)
            kyle[i] = np.cov(y_c, x_c)[0, 1] / np.var(x_c)

        return pd.Series(kyle, index=df.index, name="kyle_lambda")

    # ------------------------------------------------------------------
    # 2d. Roll Spread — Cap. 18
    # ------------------------------------------------------------------
    def compute_roll_spread(self, df: pd.DataFrame) -> pd.Series:
        """
        Estimador de Roll para o spread efetivo.

        ── Teoria ──────────────────────────────────────────────────────────
        Roll (1984) mostra que o spread bid-ask pode ser estimado a partir
        da auto-covariância dos retornos:
            spread = 2 × √(-cov(Δp_t, Δp_{t-1}))  quando cov < 0
                   = 0                               quando cov ≥ 0

        A intuição: o bounce entre bid e ask cria autocorrelação negativa
        nos retornos. Quanto maior o spread, mais negativa a covariância.
        """
        close = df["close"].values.astype(np.float64)
        dp = np.diff(close, prepend=np.nan)

        n = len(df)
        w = self.roll_window
        roll = np.full(n, np.nan)

        for i in range(w + 1, n):
            dp_t = dp[i - w + 1 : i + 1]
            dp_t1 = dp[i - w : i]
            mask = ~(np.isnan(dp_t) | np.isnan(dp_t1))
            if mask.sum() < w // 2:
                continue
            cov_val = np.cov(dp_t[mask], dp_t1[mask])[0, 1]
            if cov_val < 0:
                roll[i] = 2.0 * np.sqrt(-cov_val)
            else:
                roll[i] = 0.0

        return pd.Series(roll, index=df.index, name="roll_spread")

    # ------------------------------------------------------------------
    # 2e. Lempel-Ziv Entropy — Cap. 18
    # ------------------------------------------------------------------
    @staticmethod
    def _lempel_ziv_complexity(binary_string: str) -> float:
        """
        Calcula a complexidade Lempel-Ziv (LZ76) de uma string binária.

        Conta o número de substrings distintas encontradas ao percorrer a
        sequência da esquerda para a direita.  Normaliza por n/log2(n)
        para que o resultado fique em [0, 1+].
        """
        n = len(binary_string)
        if n == 0:
            return 0.0
        i = 0
        complexity = 1
        prefix_len = 1
        while prefix_len + i < n:
            # Procura a maior extensão que já apareceu como substring
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
        # Normalização: c(n) / (n / log2(n))
        norm = n / np.log2(max(n, 2))
        return complexity / norm

    def compute_lempel_ziv(self, df: pd.DataFrame) -> pd.Series:
        """
        Entropia Lempel-Ziv do fluxo de ordens.

        ── Teoria ──────────────────────────────────────────────────────────
        Mede o conteúdo informacional da sequência de retornos.
          • Entropia ALTA → retornos são imprevisíveis (mercado eficiente).
          • Entropia BAIXA → padrões repetitivos → regime de tendência forte
            ou manipulação — o modelo pode explorar essa previsibilidade.

        Binarizamos os retornos (1 se positivo, 0 se negativo) e aplicamos
        LZ76 em janela rolling.
        """
        close = df["close"].values.astype(np.float64)
        ret = np.diff(close, prepend=np.nan)
        binary = np.where(ret > 0, "1", "0")

        n = len(df)
        w = self.lz_window
        lz = np.full(n, np.nan)

        for i in range(w, n):
            window_str = "".join(binary[i - w + 1 : i + 1])
            lz[i] = self._lempel_ziv_complexity(window_str)

        return pd.Series(lz, index=df.index, name="lz_entropy")

    # ------------------------------------------------------------------
    # 2f. Savitzky-Golay Smoothing (experimental)
    # ------------------------------------------------------------------
    @staticmethod
    def savgol_smooth(
        series: pd.Series, window: int = SAVGOL_WINDOW, polyorder: int = SAVGOL_POLYORDER
    ) -> pd.Series:
        """
        Suaviza a série de preços com filtro Savitzky-Golay.

        ── Por que SG em vez de Média Móvel? ────────────────────────────
        A MA simples (ou EWM) é um filtro passa-baixa que introduz LAG
        proporcional à janela.  O Savitzky-Golay ajusta um polinômio
        local de grau `polyorder` via mínimos quadrados em cada janela,
        preservando:
          • Derivadas locais (picos e vales mantêm posição e amplitude)
          • Menor distorção de fase (lag muito reduzido vs MA)

        Isso é útil para calcular retornos e volatilidade sobre preços
        com menos ruído de microestrutura, sem deslocar o timing do sinal.

        Parâmetros: window=21 (deve ser ímpar), polyorder=3.
        """
        values = series.values.astype(np.float64)
        # savgol_filter exige window <= len(values) e window ímpar
        w = min(window, len(values))
        if w % 2 == 0:
            w -= 1
        if w < polyorder + 2:
            return series.copy()
        smoothed = savgol_filter(values, window_length=w, polyorder=polyorder)
        return pd.Series(smoothed, index=series.index, name="close_sg")

    # ------------------------------------------------------------------
    # 2f-bis. Savitzky-Golay CAUSAL (sem look-ahead)
    # ------------------------------------------------------------------
    @staticmethod
    def savgol_smooth_causal(
        series: pd.Series, window: int = SAVGOL_WINDOW, polyorder: int = SAVGOL_POLYORDER
    ) -> pd.Series:
        """
        Suaviza a série de preços com filtro Savitzky-Golay CAUSAL.

        ── Diferença do SG centrado (savgol_smooth) ─────────────────────
        O SG centrado usa barras passadas E futuras — perfeito para análise
        offline, mas IMPOSSÍVEL em live trading (não temos barras futuras).

        O SG causal ajusta o mesmo polinômio de grau `polyorder`, mas
        avalia no ÚLTIMO ponto da janela:
            Para cada t, ajusta poly sobre [t-window+1, ..., t]
            e usa o valor ajustado em t.

        Isso é equivalente a usar savgol_coeffs com pos=window-1.

        ── Trade-off ────────────────────────────────────────────────────
        • Mais lag que o SG centrado (o polinômio é "puxado" para a borda)
        • Menos suavização nos extremos
        • Mas SEM look-ahead — resultado válido para uso em produção

        As primeiras (window-1) barras ficam como NaN (warmup).
        """
        values = series.values.astype(np.float64)
        w = min(window, len(values))
        if w % 2 == 0:
            w -= 1
        if w < polyorder + 2:
            return series.copy()

        # Coeficientes para avaliação na última posição da janela (causal)
        coeffs = savgol_coeffs(w, polyorder, pos=w - 1)
        # Convolução: o coeficiente[0] corresponde ao ponto mais antigo da janela
        smoothed = np.convolve(values, coeffs, mode="full")
        # Recortar para alinhar com a série original
        # A convolução produz len(values) + len(coeffs) - 1 pontos
        # Queremos os pontos [w-1, w, ..., w-1+len(values)-1] = [w-1 : w-1+n]
        smoothed = smoothed[w - 1 : w - 1 + len(values)]
        # Primeiras (w-1) barras = NaN (warmup, não temos barras passadas suficientes)
        smoothed[: w - 1] = np.nan

        return pd.Series(smoothed, index=series.index, name="close_sg_causal")

    # ------------------------------------------------------------------
    # 2g. RSI — Relative Strength Index (experimental)
    # ------------------------------------------------------------------
    @staticmethod
    def compute_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
        """
        Índice de Força Relativa (RSI) de Wilder.

        ── Teoria ──────────────────────────────────────────────────────────
        RSI mede a persistência direcional dos retornos recentes:
            RSI = 100 - 100 / (1 + RS)
            RS  = EWM(ganhos, span=period) / EWM(perdas, span=period)

        Valores extremos indicam:
          • RSI > 70 → sobrecompra (possível reversão para baixo)
          • RSI < 30 → sobrevenda  (possível reversão para cima)

        Para criptoativos com momentum forte, RSI captura algo que retornos
        puros (ret_5, ret_20) não medem: a RAZÃO entre dias de alta e
        dias de baixa, ponderada por magnitude.

        Complementa as features existentes porque nenhuma delas captura
        diretamente a persistência de direção.
        """
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(span=period, min_periods=period).mean()
        avg_loss = loss.ewm(span=period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - 100.0 / (1.0 + rs)
        return pd.Series(rsi.values, index=close.index, name="rsi")

    # ------------------------------------------------------------------
    # 2h. Transform — orquestra todas as features
    # ------------------------------------------------------------------
    def transform(
        self, dollar_bars: pd.DataFrame, fng_df: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Calcula todas as features sobre dollar bars e retorna o DataFrame
        enriquecido + lista de nomes das feature columns.

        Parâmetros
        ----------
        dollar_bars : DataFrame de Dollar Bars (output de DollarBarBuilder)
        fng_df : DataFrame de Fear & Greed [timestamp, fear_greed] (opcional)

        Retorna
        -------
        (df_features, feature_names)
        """
        df = dollar_bars.copy()
        print("  Calculando FFD (Diferenciação Fracionária)...")
        df["ffd_close"] = self.fractional_diff(df["close"])

        print("  Calculando VPIN...")
        df["vpin"] = self.compute_vpin(df)

        print("  Calculando Kyle Lambda...")
        df["kyle_lambda"] = self.compute_kyle_lambda(df)

        print("  Calculando Roll Spread...")
        df["roll_spread"] = self.compute_roll_spread(df)

        print("  Calculando Lempel-Ziv Entropy...")
        df["lz_entropy"] = self.compute_lempel_ziv(df)

        # Features tradicionais (momentum e volatilidade)
        close_raw = df["close"].astype(np.float64)

        # Savitzky-Golay: suavizar close antes de calcular ret/vol
        if self.use_savgol_causal:
            print(f"  Aplicando Savitzky-Golay CAUSAL (window={self.savgol_window}, poly={self.savgol_polyorder})...")
            close = self.savgol_smooth_causal(close_raw, self.savgol_window, self.savgol_polyorder)
        elif self.use_savgol:
            print(f"  Aplicando Savitzky-Golay centrado (window={self.savgol_window}, poly={self.savgol_polyorder})...")
            close = self.savgol_smooth(close_raw, self.savgol_window, self.savgol_polyorder)
        else:
            close = close_raw

        ret = close.pct_change()
        df["ret_5"] = close.pct_change(5)
        df["ret_20"] = close.pct_change(20)
        df["log_volume"] = np.log1p(df["volume"].astype(np.float64))
        df["volatility_20"] = ret.rolling(20, min_periods=20).std()

        # RSI (experimental)
        if self.use_rsi:
            print(f"  Calculando RSI (period={self.rsi_period})...")
            df["rsi"] = self.compute_rsi(close_raw, self.rsi_period)

        # Fear & Greed: merge por data (lag 1 dia para evitar leakage)
        if fng_df is not None and len(fng_df) > 0:
            fng = fng_df.copy()
            fng["timestamp"] = pd.to_datetime(fng["timestamp"])
            if fng["timestamp"].dt.tz is None:
                fng["timestamp"] = fng["timestamp"].dt.tz_localize("UTC")
            fng["date"] = fng["timestamp"].dt.date
            fng_map = fng.set_index("date")["fear_greed"].to_dict()

            df["timestamp"] = pd.to_datetime(df["timestamp"])
            if df["timestamp"].dt.tz is None:
                df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
            # Usar o Fear & Greed do dia ANTERIOR (evita leakage)
            df["date_prev"] = (df["timestamp"] - pd.Timedelta(days=1)).dt.date
            df["fear_greed"] = df["date_prev"].map(fng_map)
            df["fear_greed"] = df["fear_greed"].ffill()
            df.drop(columns=["date_prev"], inplace=True)
        else:
            df["fear_greed"] = np.nan

        # Lista de features
        feature_names = [
            "ffd_close",
            "vpin",
            "kyle_lambda",
            "roll_spread",
            "lz_entropy",
            "ret_5",
            "ret_20",
            "log_volume",
            "volatility_20",
            "fear_greed",
        ]
        if self.use_rsi:
            feature_names.append("rsi")

        # Dropar warmup NaNs
        df = df.dropna(subset=feature_names).reset_index(drop=True)

        print(f"  Features calculadas: {len(feature_names)} colunas, {len(df)} barras")
        return df, feature_names


# ==========================================================================
# 3. TRIPLE-BARRIER METHOD — Cap. 3 AFML
# ==========================================================================
class TripleBarrierLabeler:
    """
    Rotulagem Triple-Barrier para classificação de eventos financeiros.

    ── Por que não usar retornos fixos como rótulo? ─────────────────────
    Usar "retorno > 0 → label=1" ignora o risco e a dinâmica de volatilidade.
    O Triple-Barrier Method define três cenários para cada posição:

      ┌─────────────────────────────────────────┐
      │  PROFIT-TAKE  ──→  upper = close × (1 + pt × σ)  │ label = +1
      │  STOP-LOSS    ──→  lower = close × (1 - sl × σ)  │ label = -1
      │  TEMPO EXPIRADO → vertical = t + max_bars         │ label =  0
      └─────────────────────────────────────────┘

    As barreiras horizontais são DINÂMICAS: escalam com a volatilidade
    prevista (EWM std dos retornos logarítmicos).  Em mercados calmos as
    barreiras se estreitam; em crises se alargam — adaptando a sensibilidade
    do rótulo ao regime corrente.

    O par (t0, t1) — instante de entrada e instante de toque da barreira —
    é fundamental para o Purged K-Fold (evita leakage).
    """

    def __init__(
        self,
        volatility_lookback: int = VOL_LOOKBACK,
        pt_multiplier: float = PT_MULTIPLIER,
        sl_multiplier: float = SL_MULTIPLIER,
        max_holding_bars: int = MAX_HOLDING_BARS,
    ):
        self.volatility_lookback = volatility_lookback
        self.pt_multiplier = pt_multiplier
        self.sl_multiplier = sl_multiplier
        self.max_holding_bars = max_holding_bars

    # ------------------------------------------------------------------
    def compute_daily_volatility(self, close: pd.Series) -> pd.Series:
        """
        Volatilidade diária prevista via EWM std dos retornos logarítmicos.

        Usamos span = volatility_lookback para que a estimativa reaja
        rapidamente a mudanças de regime (mais peso em observações recentes).
        """
        log_ret = np.log(close / close.shift(1))
        vol = log_ret.ewm(span=self.volatility_lookback, min_periods=self.volatility_lookback).std()
        return vol

    # ------------------------------------------------------------------
    def apply_barriers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica o Triple-Barrier Method a cada dollar bar.

        Retorna DataFrame com colunas adicionais:
          - label: +1 (profit-take), -1 (stop-loss), 0 (vertical/tempo)
          - t0: índice da barra de entrada
          - t1: índice da barra onde a barreira foi tocada
        """
        close = df["close"].values.astype(np.float64)
        high = df["high"].values.astype(np.float64)
        low = df["low"].values.astype(np.float64)
        vol = self.compute_daily_volatility(pd.Series(close)).values
        n = len(df)

        labels = np.full(n, np.nan)
        t0_arr = np.full(n, -1, dtype=np.int64)
        t1_arr = np.full(n, -1, dtype=np.int64)

        for i in range(n):
            if np.isnan(vol[i]) or vol[i] < 1e-12:
                continue

            entry_price = close[i]
            upper = entry_price * (1.0 + self.pt_multiplier * vol[i])
            lower = entry_price * (1.0 - self.sl_multiplier * vol[i])
            max_j = min(i + self.max_holding_bars, n)

            touched = False
            for j in range(i + 1, max_j):
                # Verifica se o HIGH tocou a barreira superior (profit-take)
                if high[j] >= upper:
                    labels[i] = 1
                    t0_arr[i] = i
                    t1_arr[i] = j
                    touched = True
                    break
                # Verifica se o LOW tocou a barreira inferior (stop-loss)
                if low[j] <= lower:
                    labels[i] = -1
                    t0_arr[i] = i
                    t1_arr[i] = j
                    touched = True
                    break

            if not touched and max_j > i + 1:
                # Barreira vertical: tempo expirou
                labels[i] = 0
                t0_arr[i] = i
                t1_arr[i] = max_j - 1

        df = df.copy()
        df["label"] = labels
        df["t0"] = t0_arr
        df["t1"] = t1_arr

        # Remover barras sem rótulo (warmup da volatilidade)
        df = df.dropna(subset=["label"]).reset_index(drop=True)
        df["label"] = df["label"].astype(int)
        df["t0"] = df["t0"].astype(int)
        df["t1"] = df["t1"].astype(int)

        # Diagnóstico
        counts = df["label"].value_counts().to_dict()
        print(f"  Distribuição de rótulos: {counts}")
        return df


# ==========================================================================
# 4. META-LABELING — Cap. 3.6 AFML
# ==========================================================================
class MetaLabeler:
    """
    Meta-Labeling: O Coração da Estratégia de López de Prado.

    ── Conceito ─────────────────────────────────────────────────────────
    Em vez de treinar um único modelo para prever a direção E o momento
    da aposta, separamos em dois estágios:

    Estágio 1 (Modelo Primário — direção):
      Prediz se o próximo evento será +1 (compra) ou -1 (venda).
      Pode ter recall alto mas precision baixa (muitos falsos positivos).

    Estágio 2 (Meta-Modelo — "apostar ou não"):
      Recebe as mesmas features e decide: "Devo confiar na predição do
      modelo primário?" → meta_label ∈ {0, 1}.

    O meta-label é definido como:
      meta_label = 1  se primary_prediction == true_label (correto)
      meta_label = 0  se primary_prediction != true_label (incorreto)

    O resultado final é:
      - Se meta_prob > 0.5 → mantém a predição primária.
      - Se meta_prob ≤ 0.5 → label = 0 (não apostar).

    ── Por que isso funciona? ───────────────────────────────────────────
    O meta-modelo aprende a FILTRAR os falsos positivos do modelo primário,
    melhorando significativamente o F1-Score e o Sharpe Ratio da estratégia.
    """

    def __init__(
        self,
        primary_params: Optional[Dict] = None,
        meta_params: Optional[Dict] = None,
    ):
        default_rf = dict(
            n_estimators=RF_N_ESTIMATORS,
            max_depth=RF_MAX_DEPTH,
            min_samples_leaf=RF_MIN_SAMPLES_LEAF,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=RNG_SEED,
        )
        self.primary_params = {**default_rf, **(primary_params or {})}
        self.meta_params = {**default_rf, **(meta_params or {})}
        self.primary_model: Optional[RandomForestClassifier] = None
        self.meta_model: Optional[RandomForestClassifier] = None

    # ------------------------------------------------------------------
    def fit_primary(self, X: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
        """
        Treina modelo primário para predizer direção (+1 ou -1).
        Filtra amostras com label=0 (tempo expirado) para sinal mais limpo.
        """
        mask = y != 0
        X_dir = X[mask]
        y_dir = y[mask]
        self.primary_model = RandomForestClassifier(**self.primary_params)
        self.primary_model.fit(X_dir, y_dir)
        acc = accuracy_score(y_dir, self.primary_model.predict(X_dir))
        print(f"  Modelo primário treinado (in-sample acc={acc:.4f}, n={len(y_dir)})")
        return self.primary_model

    # ------------------------------------------------------------------
    @staticmethod
    def generate_meta_labels(
        primary_preds: np.ndarray, true_labels: np.ndarray
    ) -> np.ndarray:
        """
        Gera meta-labels: 1 se a predição primária está correta, 0 caso contrário.
        """
        return (primary_preds == true_labels).astype(int)

    # ------------------------------------------------------------------
    def fit_meta(self, X: np.ndarray, meta_y: np.ndarray) -> RandomForestClassifier:
        """
        Treina meta-modelo: prediz P(modelo primário está correto).
        """
        self.meta_model = RandomForestClassifier(**self.meta_params)
        self.meta_model.fit(X, meta_y)
        acc = accuracy_score(meta_y, self.meta_model.predict(X))
        dist = dict(zip(*np.unique(meta_y, return_counts=True)))
        print(f"  Meta-modelo treinado (in-sample acc={acc:.4f}, dist={dist})")
        return self.meta_model

    # ------------------------------------------------------------------
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predição combinada:
          1. primary_pred = direção (+1 ou -1)
          2. meta_prob = P(primário está correto)
          3. final = primary_pred se meta_prob > 0.5, senão 0 (não apostar)

        Retorna (final_predictions, meta_probabilities).
        """
        if self.primary_model is None or self.meta_model is None:
            raise RuntimeError("Modelos não treinados. Chame fit_primary e fit_meta primeiro.")

        primary_pred = self.primary_model.predict(X)
        meta_prob = self.meta_model.predict_proba(X)
        # Índice da classe 1 (correto)
        idx_1 = list(self.meta_model.classes_).index(1)
        meta_confidence = meta_prob[:, idx_1]

        final = np.where(meta_confidence > 0.5, primary_pred, 0)
        return final, meta_confidence


# ==========================================================================
# 5. PURGED K-FOLD CROSS-VALIDATION COM EMBARGO — Cap. 7 AFML
# ==========================================================================
class PurgedKFoldCV:
    """
    Validação cruzada que respeita a estrutura temporal e a sobreposição
    de rótulos do Triple-Barrier.

    ── O problema do K-Fold ingênuo ─────────────────────────────────────
    No K-Fold padrão, um rótulo no fold de teste pode ter sido determinado
    por barras que estão no fold de treino (porque o triple-barrier olha
    para o futuro ao definir t1).  Isso gera leakage e superestima a
    performance.

    ── Solução: Purging + Embargo ───────────────────────────────────────
    1. PURGE: remove do treino qualquer amostra i cujo span [t0_i, t1_i]
       se sobreponha com o span [t0_j, t1_j] de qualquer amostra j no teste.

    2. EMBARGO: remove do treino as primeiras N amostras APÓS o fold de teste.
       Isso previne leakage de features com lag (ex: rolling windows).

    Os folds são CONTÍGUOS (não embaralhados) para respeitar a ordem temporal.
    """

    def __init__(
        self,
        n_folds: int = N_FOLDS,
        purge_pct: float = PURGE_PCT,
        embargo_pct: float = EMBARGO_PCT,
    ):
        self.n_folds = n_folds
        self.purge_pct = purge_pct
        self.embargo_pct = embargo_pct

    # ------------------------------------------------------------------
    def split(
        self, n_samples: int, t0: np.ndarray, t1: np.ndarray
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Gera splits de treino/teste com purging e embargo.

        Parâmetros
        ----------
        n_samples : número total de amostras
        t0, t1 : arrays de inteiros com os spans das labels (índices)

        Retorna
        -------
        Lista de tuplas (train_indices, test_indices)
        """
        indices = np.arange(n_samples)
        fold_size = n_samples // self.n_folds
        embargo_n = int(n_samples * self.embargo_pct)

        splits = []
        for k in range(self.n_folds):
            test_start = k * fold_size
            test_end = (k + 1) * fold_size if k < self.n_folds - 1 else n_samples
            test_idx = indices[test_start:test_end]

            # Spans do teste
            test_t0_min = t0[test_idx].min()
            test_t1_max = t1[test_idx].max()

            # Purge: remover do treino amostras com overlap
            train_mask = np.ones(n_samples, dtype=bool)
            train_mask[test_start:test_end] = False
            # Uma amostra i no treino tem overlap se t0_i < test_t1_max E t1_i > test_t0_min
            overlap = (t0 < test_t1_max) & (t1 > test_t0_min)
            train_mask[overlap] = False

            # Embargo: remover amostras logo após o teste
            embargo_start = test_end
            embargo_end = min(test_end + embargo_n, n_samples)
            train_mask[embargo_start:embargo_end] = False

            train_idx = indices[train_mask]
            splits.append((train_idx, test_idx))

        return splits

    # ------------------------------------------------------------------
    def cross_validate(
        self,
        model_factory: Callable[[], RandomForestClassifier],
        X: np.ndarray,
        y: np.ndarray,
        t0: np.ndarray,
        t1: np.ndarray,
    ) -> Dict[str, object]:
        """
        Executa validação cruzada completa e retorna métricas por fold.
        """
        splits = self.split(len(X), t0, t1)
        fold_accs = []
        fold_f1s = []

        for k, (train_idx, test_idx) in enumerate(splits):
            model = model_factory()
            X_tr, y_tr = X[train_idx], y[train_idx]
            X_te, y_te = X[test_idx], y[test_idx]

            model.fit(X_tr, y_tr)
            y_pred = model.predict(X_te)
            acc = accuracy_score(y_te, y_pred)
            f1 = f1_score(y_te, y_pred, average="weighted", zero_division=0)
            fold_accs.append(acc)
            fold_f1s.append(f1)
            print(
                f"    Fold {k + 1}/{self.n_folds}: "
                f"acc={acc:.4f}, f1={f1:.4f}, "
                f"train={len(train_idx)}, test={len(test_idx)}"
            )

        results = {
            "fold_accuracies": fold_accs,
            "fold_f1s": fold_f1s,
            "mean_accuracy": np.mean(fold_accs),
            "std_accuracy": np.std(fold_accs),
            "mean_f1": np.mean(fold_f1s),
            "std_f1": np.std(fold_f1s),
        }
        print(
            f"  CV Resultado: acc={results['mean_accuracy']:.4f} "
            f"± {results['std_accuracy']:.4f}, "
            f"f1={results['mean_f1']:.4f} ± {results['std_f1']:.4f}"
        )
        return results


# ==========================================================================
# 6. MODEL EVALUATOR — Cap. 8 (MDA) e Cap. 14 (PSR) AFML
# ==========================================================================
class ModelEvaluator:
    """
    Avaliação de modelos seguindo as diretrizes de López de Prado.

    • MDA (Mean Decrease Accuracy) — importância por permutação (Cap. 8)
    • PSR (Probabilistic Sharpe Ratio) — significância estatística (Cap. 14)
    """

    def __init__(self, risk_free_rate: float = 0.0):
        self.risk_free_rate = risk_free_rate

    # ------------------------------------------------------------------
    def mean_decrease_accuracy(
        self,
        model: RandomForestClassifier,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        n_repeats: int = 5,
    ) -> pd.DataFrame:
        """
        MDA: Feature Importance por Permutação (Cap. 8 AFML).

        ── Por que NÃO usar Gini importance (MDI)? ─────────────────────
        MDI (feature_importances_ do sklearn) sofre de viés para features
        com alta cardinalidade e não funciona out-of-sample.  Além disso,
        não captura interações entre features correlacionadas.

        MDA é mais confiável porque:
        1. Mede no conjunto de TESTE (out-of-sample).
        2. Permuta cada feature individualmente e mede a queda de accuracy.
        3. Features importantes causam grande queda; irrelevantes, nenhuma.

        ── Algoritmo ────────────────────────────────────────────────────
        baseline_acc = accuracy(model, X_test, y_test)
        Para cada feature j, repita n_repeats vezes:
          X_shuffled = X_test com coluna j permutada aleatoriamente
          acc_j = accuracy(model, X_shuffled, y_test)
          mda_j = baseline_acc - acc_j
        Retorna média e std de mda_j para cada feature.
        """
        rng = np.random.RandomState(RNG_SEED)
        baseline_acc = accuracy_score(y_test, model.predict(X_test))

        importances = {name: [] for name in feature_names}
        for j, name in enumerate(feature_names):
            for _ in range(n_repeats):
                X_perm = X_test.copy()
                X_perm[:, j] = rng.permutation(X_perm[:, j])
                acc_perm = accuracy_score(y_test, model.predict(X_perm))
                importances[name].append(baseline_acc - acc_perm)

        mda_df = pd.DataFrame(
            {
                "feature": feature_names,
                "mda_mean": [np.mean(importances[n]) for n in feature_names],
                "mda_std": [np.std(importances[n]) for n in feature_names],
            }
        )
        mda_df = mda_df.sort_values("mda_mean", ascending=False).reset_index(drop=True)
        return mda_df

    # ------------------------------------------------------------------
    def probabilistic_sharpe_ratio(
        self, returns: np.ndarray, sr_benchmark: float = 0.0
    ) -> float:
        """
        Probabilistic Sharpe Ratio (Cap. 14 AFML).

        ── Teoria ──────────────────────────────────────────────────────────
        O Sharpe Ratio convencional (SR = μ/σ) ignora:
        • Tamanho da amostra (pode ser sorte com poucas observações)
        • Assimetria e curtose dos retornos (caudas pesadas)

        O PSR testa H0: SR ≤ sr_benchmark, incorporando momentos de ordem
        superior:

          PSR = Φ[ (SR̂ - SR*) × √(T-1) / √(1 - γ₃·SR̂ + (γ₄-1)/4·SR̂²) ]

        onde γ₃ = skewness, γ₄ = kurtosis (excesso), T = observações.

        PSR > 0.95 → performance estatisticamente significativa a 95%.
        PSR < 0.50 → não podemos rejeitar que o SR é apenas ruído.
        """
        returns = returns[~np.isnan(returns)]
        T = len(returns)
        if T < 3:
            return 0.0

        sr_hat = np.mean(returns) / max(np.std(returns, ddof=1), 1e-12)
        skew = sp_stats.skew(returns)
        kurt = sp_stats.kurtosis(returns)  # excesso de curtose

        denominator = 1.0 - skew * sr_hat + (kurt - 1.0) / 4.0 * sr_hat ** 2
        if denominator <= 0:
            denominator = 1e-12

        psr = sp_stats.norm.cdf(
            (sr_hat - sr_benchmark) * np.sqrt(T - 1) / np.sqrt(denominator)
        )
        return float(psr)

    # ------------------------------------------------------------------
    @staticmethod
    def compute_strategy_returns(
        predictions: np.ndarray, actual_returns: np.ndarray
    ) -> np.ndarray:
        """
        Retorno por barra da estratégia:
          - Se prediction = +1 → comprado → retorno = actual_return
          - Se prediction = -1 → vendido  → retorno = -actual_return
          - Se prediction =  0 → fora     → retorno = 0
        """
        return predictions * actual_returns

    # ------------------------------------------------------------------
    def full_evaluation(
        self,
        model: RandomForestClassifier,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        predictions: np.ndarray,
        actual_returns: np.ndarray,
    ) -> Dict:
        """Executa MDA + PSR + classification report completo."""
        print("\n--- Feature Importance (MDA) ---")
        mda_df = self.mean_decrease_accuracy(model, X_test, y_test, feature_names)
        for _, row in mda_df.iterrows():
            print(f"  {row['feature']:20s}  MDA={row['mda_mean']:.6f} ± {row['mda_std']:.6f}")

        strategy_ret = self.compute_strategy_returns(predictions, actual_returns)
        psr = self.probabilistic_sharpe_ratio(strategy_ret)
        sr = np.mean(strategy_ret) / max(np.std(strategy_ret, ddof=1), 1e-12)

        print(f"\n--- Probabilistic Sharpe Ratio ---")
        print(f"  Sharpe Ratio (amostra): {sr:.4f}")
        print(f"  PSR: {psr:.4f} ({'SIGNIFICATIVO' if psr > 0.95 else 'não significativo'})")

        print(f"\n--- Classification Report ---")
        report = classification_report(y_test, predictions, zero_division=0)
        print(report)

        return {
            "mda": mda_df,
            "psr": psr,
            "sharpe_ratio": sr,
            "strategy_returns": strategy_ret,
            "classification_report": report,
        }


# ==========================================================================
# 7. VISUALIZER
# ==========================================================================
class Visualizer:
    """Gera plots diagnósticos e salva em disco."""

    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    # ------------------------------------------------------------------
    def plot_dollar_bars_sampling(
        self, dollar_bars: pd.DataFrame
    ) -> None:
        """Distribuição de ticks por dollar bar (mostra variação do sampling)."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Histograma de tick_count
        axes[0].hist(dollar_bars["tick_count"], bins=50, edgecolor="black", alpha=0.7)
        axes[0].set_xlabel("Ticks por Dollar Bar")
        axes[0].set_ylabel("Frequência")
        axes[0].set_title("Distribuição de ticks por Dollar Bar")
        axes[0].axvline(
            dollar_bars["tick_count"].median(), color="red", linestyle="--",
            label=f'Mediana={dollar_bars["tick_count"].median():.0f}'
        )
        axes[0].legend()

        # Dollar volume por barra (deve ser ~constante)
        axes[1].plot(dollar_bars["dollar_volume"].values, linewidth=0.5, alpha=0.7)
        axes[1].set_xlabel("Índice da Dollar Bar")
        axes[1].set_ylabel("Dollar Volume")
        axes[1].set_title("Dollar Volume por Barra (deve ser ~constante)")

        plt.tight_layout()
        path = os.path.join(self.save_dir, "dollar_bars_sampling.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Plot salvo: {path}")

    # ------------------------------------------------------------------
    def plot_feature_importance_mda(self, mda_df: pd.DataFrame) -> None:
        """Bar chart horizontal de MDA com barras de erro."""
        fig, ax = plt.subplots(figsize=(10, 6))
        names = mda_df["feature"].values
        means = mda_df["mda_mean"].values
        stds = mda_df["mda_std"].values

        y_pos = np.arange(len(names))
        ax.barh(y_pos, means, xerr=stds, align="center", alpha=0.8, capsize=3)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.invert_yaxis()
        ax.set_xlabel("Mean Decrease Accuracy (MDA)")
        ax.set_title("Feature Importance — MDA (AFML Cap. 8)")
        ax.axvline(0, color="gray", linestyle="--", linewidth=0.8)
        plt.tight_layout()
        path = os.path.join(self.save_dir, "feature_importance_mda.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Plot salvo: {path}")

    # ------------------------------------------------------------------
    def plot_triple_barrier_labels(
        self, df: pd.DataFrame
    ) -> None:
        """Preço com rótulos do triple-barrier coloridos."""
        fig, ax = plt.subplots(figsize=(14, 6))
        colors = {1: "green", -1: "red", 0: "gray"}
        labels_map = {1: "Profit-Take (+1)", -1: "Stop-Loss (-1)", 0: "Vertical (0)"}

        ax.plot(df["close"].values, color="black", linewidth=0.5, alpha=0.6, label="Close")
        for lbl, color in colors.items():
            mask = df["label"] == lbl
            if mask.any():
                ax.scatter(
                    np.where(mask)[0],
                    df.loc[mask, "close"].values,
                    c=color, s=3, alpha=0.5, label=labels_map[lbl],
                )
        ax.set_xlabel("Índice da Dollar Bar")
        ax.set_ylabel("Preço BTC (USD)")
        ax.set_title("Triple-Barrier Labels sobre Dollar Bars")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        path = os.path.join(self.save_dir, "triple_barrier_labels.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Plot salvo: {path}")

    # ------------------------------------------------------------------
    def plot_meta_label_filtering(
        self,
        primary_preds: np.ndarray,
        final_preds: np.ndarray,
        close_prices: np.ndarray,
    ) -> None:
        """Mostra quais trades o meta-labeling filtrou."""
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(close_prices, color="black", linewidth=0.5, alpha=0.6, label="Close")

        kept = final_preds != 0
        filtered = (primary_preds != 0) & (final_preds == 0)

        if kept.any():
            ax.scatter(
                np.where(kept)[0], close_prices[kept],
                c="blue", s=4, alpha=0.5, label=f"Mantidos ({kept.sum()})"
            )
        if filtered.any():
            ax.scatter(
                np.where(filtered)[0], close_prices[filtered],
                c="orange", s=4, alpha=0.5, label=f"Filtrados ({filtered.sum()})"
            )
        ax.set_xlabel("Índice")
        ax.set_ylabel("Preço BTC (USD)")
        ax.set_title("Meta-Labeling: Trades mantidos vs filtrados")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        path = os.path.join(self.save_dir, "meta_label_filtering.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Plot salvo: {path}")

    # ------------------------------------------------------------------
    def plot_cumulative_returns(
        self,
        strategy_returns: np.ndarray,
        benchmark_returns: np.ndarray,
        psr_value: float,
    ) -> None:
        """Retorno acumulado da estratégia vs benchmark, com anotação do PSR."""
        fig, ax = plt.subplots(figsize=(14, 6))
        cum_strat = np.cumsum(strategy_returns)
        cum_bench = np.cumsum(benchmark_returns)

        ax.plot(cum_strat, label="Estratégia (Meta-Label)", linewidth=1.2, color="blue")
        ax.plot(cum_bench, label="Benchmark (Buy & Hold)", linewidth=1.0, color="gray", alpha=0.7)
        ax.fill_between(range(len(cum_strat)), cum_strat, alpha=0.1, color="blue")

        ax.text(
            0.02, 0.95, f"PSR = {psr_value:.4f}",
            transform=ax.transAxes, fontsize=12, verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )
        ax.set_xlabel("Índice da Barra (teste)")
        ax.set_ylabel("Retorno Acumulado")
        ax.set_title("Retorno Acumulado: Estratégia vs Benchmark")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        path = os.path.join(self.save_dir, "cumulative_returns.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Plot salvo: {path}")


# ==========================================================================
# 8. MARCOS PIPELINE — ORQUESTRADOR
# ==========================================================================
class MarcosPipeline:
    """
    Pipeline completo seguindo as "Leis de Marcos López de Prado".

    ┌────────────────────────────────────────────────────────────────┐
    │  LEI 1: Use barras information-driven, não de tempo.           │
    │  LEI 2: Diferencie fracionariamente para preservar memória.    │
    │  LEI 3: Rotule com triple-barrier, não retornos simples.       │
    │  LEI 4: Meta-label para controlar falsos positivos.            │
    │  LEI 5: Purge e embargo no CV para evitar leakage.             │
    │  LEI 6: Use MDA (não MDI) para importância de features.        │
    │  LEI 7: Use PSR para confirmar significância estatística.      │
    └────────────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        data_dir: str,
        save_dir: str,
        config: Optional[Dict] = None,
    ):
        self.data_dir = data_dir
        self.save_dir = save_dir
        cfg = config or {}

        # Instanciar componentes com config override
        self.bar_builder = DollarBarBuilder(
            calibration_days=cfg.get("calibration_days", DOLLAR_BAR_CALIBRATION_DAYS),
            bars_per_day=cfg.get("bars_per_day", DOLLAR_BARS_PER_DAY),
        )
        self.feature_engine = FeatureEngine(
            ffd_d=cfg.get("ffd_d", FFD_D),
            ffd_threshold=cfg.get("ffd_threshold", FFD_THRESHOLD),
            vpin_n_buckets=cfg.get("vpin_n_buckets", VPIN_N_BUCKETS),
            kyle_window=cfg.get("kyle_window", KYLE_WINDOW),
            roll_window=cfg.get("roll_window", ROLL_WINDOW),
            lz_window=cfg.get("lz_window", LZ_WINDOW),
            use_savgol=cfg.get("use_savgol", False),
            use_savgol_causal=cfg.get("use_savgol_causal", False),
            savgol_window=cfg.get("savgol_window", SAVGOL_WINDOW),
            savgol_polyorder=cfg.get("savgol_polyorder", SAVGOL_POLYORDER),
            use_rsi=cfg.get("use_rsi", False),
            rsi_period=cfg.get("rsi_period", RSI_PERIOD),
        )
        self.labeler = TripleBarrierLabeler(
            volatility_lookback=cfg.get("vol_lookback", VOL_LOOKBACK),
            pt_multiplier=cfg.get("pt_multiplier", PT_MULTIPLIER),
            sl_multiplier=cfg.get("sl_multiplier", SL_MULTIPLIER),
            max_holding_bars=cfg.get("max_holding_bars", MAX_HOLDING_BARS),
        )
        self.meta_labeler = MetaLabeler()
        self.cv = PurgedKFoldCV(
            n_folds=cfg.get("n_folds", N_FOLDS),
            purge_pct=cfg.get("purge_pct", PURGE_PCT),
            embargo_pct=cfg.get("embargo_pct", EMBARGO_PCT),
        )
        self.evaluator = ModelEvaluator()
        self.visualizer = Visualizer(save_dir)

    # ------------------------------------------------------------------
    def _load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Carrega BTC 1-min e Fear & Greed dos CSVs."""
        btc_path = os.path.join(self.data_dir, "btcusdt_1m.csv")
        fng_path = os.path.join(self.data_dir, "fear_greed.csv")

        btc_df = pd.read_csv(btc_path, parse_dates=["timestamp"])
        fng_df = pd.read_csv(fng_path, parse_dates=["timestamp"])

        print(f"  BTC 1-min: {btc_df.shape}")
        print(f"  Fear & Greed: {fng_df.shape}")
        return btc_df, fng_df

    # ------------------------------------------------------------------
    def run(self) -> Dict:
        """
        Executa o pipeline completo.

        Fluxo:
          1. Carregar dados
          2. Construir Dollar Bars
          3. Engenharia de features
          4. Triple-Barrier labeling
          5. Purged K-Fold CV (validação do modelo primário)
          6. Meta-Labeling (treino + predição)
          7. Avaliação (MDA + PSR)
          8. Visualização
        """
        np.random.seed(RNG_SEED)

        # ── 1. CARREGAR DADOS ──────────────────────────────────────────
        print("\n" + "=" * 70)
        print("ETAPA 1: Carregando dados")
        print("=" * 70)
        btc_df, fng_df = self._load_data()

        # ── 2. DOLLAR BARS ─────────────────────────────────────────────
        print("\n" + "=" * 70)
        print("ETAPA 2: Construindo Dollar Bars (AFML Cap. 2)")
        print("=" * 70)
        threshold = self.bar_builder.calibrate_threshold(btc_df)
        print(f"  Threshold calibrado: ${threshold:,.0f}")
        dollar_bars = self.bar_builder.transform(btc_df)
        print(f"  Dollar Bars geradas: {len(dollar_bars)}")
        print(f"  Ticks/barra — mediana={dollar_bars['tick_count'].median():.0f}, "
              f"min={dollar_bars['tick_count'].min()}, max={dollar_bars['tick_count'].max()}")

        # ── 3. FEATURE ENGINEERING ─────────────────────────────────────
        print("\n" + "=" * 70)
        print("ETAPA 3: Engenharia de Features (AFML Cap. 5, 18)")
        print("=" * 70)
        df_feat, feature_names = self.feature_engine.transform(dollar_bars, fng_df)

        # ── 4. TRIPLE-BARRIER LABELING ─────────────────────────────────
        print("\n" + "=" * 70)
        print("ETAPA 4: Triple-Barrier Labeling (AFML Cap. 3)")
        print("=" * 70)
        df_labeled = self.labeler.apply_barriers(df_feat)

        # ── 5. PURGED K-FOLD CV ────────────────────────────────────────
        print("\n" + "=" * 70)
        print("ETAPA 5: Purged K-Fold Cross-Validation (AFML Cap. 7)")
        print("=" * 70)
        X_all = df_labeled[feature_names].values
        y_all = df_labeled["label"].values
        t0_all = df_labeled["t0"].values
        t1_all = df_labeled["t1"].values

        def rf_factory():
            return RandomForestClassifier(
                n_estimators=RF_N_ESTIMATORS,
                max_depth=RF_MAX_DEPTH,
                min_samples_leaf=RF_MIN_SAMPLES_LEAF,
                max_features="sqrt",
                class_weight="balanced_subsample",
                random_state=RNG_SEED,
            )

        cv_results = self.cv.cross_validate(rf_factory, X_all, y_all, t0_all, t1_all)

        # ── 6. META-LABELING ──────────────────────────────────────────
        print("\n" + "=" * 70)
        print("ETAPA 6: Meta-Labeling (AFML Cap. 3.6)")
        print("=" * 70)
        # Split temporal 80/20
        n = len(df_labeled)
        split_idx = int(n * TRAIN_RATIO)
        X_train, X_test = X_all[:split_idx], X_all[split_idx:]
        y_train, y_test = y_all[:split_idx], y_all[split_idx:]

        # Treinar modelo primário (apenas amostras com label != 0)
        self.meta_labeler.fit_primary(X_train, y_train)

        # Gerar meta-labels no treino
        # Para o meta-modelo, usamos TODAS as amostras do treino
        primary_preds_train = self.meta_labeler.primary_model.predict(X_train)
        meta_y_train = MetaLabeler.generate_meta_labels(primary_preds_train, y_train)

        # Treinar meta-modelo
        self.meta_labeler.fit_meta(X_train, meta_y_train)

        # Predição no teste
        final_preds, meta_probs = self.meta_labeler.predict(X_test)
        primary_preds_test = self.meta_labeler.primary_model.predict(X_test)

        # ── 7. AVALIAÇÃO ──────────────────────────────────────────────
        print("\n" + "=" * 70)
        print("ETAPA 7: Avaliação (MDA + PSR) (AFML Cap. 8, 14)")
        print("=" * 70)
        # Retornos reais das barras de teste
        close_test = df_labeled["close"].values[split_idx:]
        actual_returns = np.diff(close_test, prepend=close_test[0]) / np.maximum(
            close_test, 1e-12
        )

        eval_results = self.evaluator.full_evaluation(
            model=self.meta_labeler.primary_model,
            X_test=X_test,
            y_test=y_test,
            feature_names=feature_names,
            predictions=final_preds,
            actual_returns=actual_returns,
        )

        # ── 8. VISUALIZAÇÃO ──────────────────────────────────────────
        print("\n" + "=" * 70)
        print("ETAPA 8: Gerando visualizações")
        print("=" * 70)
        self.visualizer.plot_dollar_bars_sampling(dollar_bars)
        self.visualizer.plot_feature_importance_mda(eval_results["mda"])
        self.visualizer.plot_triple_barrier_labels(df_labeled)
        self.visualizer.plot_meta_label_filtering(
            primary_preds_test, final_preds, close_test
        )
        benchmark_returns = actual_returns  # buy & hold
        self.visualizer.plot_cumulative_returns(
            eval_results["strategy_returns"], benchmark_returns, eval_results["psr"]
        )

        # ── RESULTADO FINAL ──────────────────────────────────────────
        results = {
            "dollar_bars": len(dollar_bars),
            "features": len(feature_names),
            "labeled_bars": len(df_labeled),
            "cv_mean_accuracy": cv_results["mean_accuracy"],
            "cv_mean_f1": cv_results["mean_f1"],
            "psr": eval_results["psr"],
            "sharpe_ratio": eval_results["sharpe_ratio"],
            "meta_f1": f1_score(y_test, final_preds, average="weighted", zero_division=0),
            "mda_top_features": eval_results["mda"].head(5).to_dict("records"),
        }
        return results


# ==========================================================================
# MAIN
# ==========================================================================
def main() -> None:
    """
    Ponto de entrada standalone.

    Roda 4 configurações (A/B test) e imprime tabela comparativa:
      1. Baseline (sem SG, sem RSI)
      2. Savitzky-Golay only
      3. RSI only
      4. Savitzky-Golay + RSI
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, DATA_DIR)
    base_save_dir = os.path.join(script_dir, SAVE_DIR)

    print("=" * 70)
    print("  PIPELINE MARCOS LÓPEZ DE PRADO — Crypto Regime Detection")
    print("  Baseado em 'Advances in Financial Machine Learning' (2018)")
    print("  + Testes experimentais: Savitzky-Golay e RSI")
    print("=" * 70)

    # ── Configurações do A/B test ──────────────────────────────────────
    configs = [
        {"name": "Baseline",    "use_savgol": False, "use_rsi": False},
        {"name": "SavGol",      "use_savgol": True,  "use_rsi": False},
        {"name": "RSI",         "use_savgol": False, "use_rsi": True},
        {"name": "SavGol+RSI",  "use_savgol": True,  "use_rsi": True},
        {"name": "SavGol2",     "use_savgol_causal": True, "use_rsi": False},
    ]

    all_results = []
    for cfg in configs:
        name = cfg.pop("name")
        save_dir = os.path.join(base_save_dir, name.lower().replace("+", "_"))

        print(f"\n{'#' * 70}")
        print(f"  CONFIGURAÇÃO: {name}")
        print(f"{'#' * 70}")

        pipeline = MarcosPipeline(data_dir=data_dir, save_dir=save_dir, config=cfg)
        results = pipeline.run()
        results["name"] = name

        # Top 3 features por MDA
        top3 = [f["feature"] for f in results["mda_top_features"][:3]]
        results["top3_mda"] = ", ".join(top3)
        all_results.append(results)

    # ── Tabela comparativa ─────────────────────────────────────────────
    print("\n\n" + "=" * 90)
    print("  TABELA COMPARATIVA — A/B TEST")
    print("=" * 90)
    header = f"  {'Config':<14s} {'CV Acc':>8s} {'CV F1':>8s} {'Meta F1':>9s} {'SR':>8s} {'PSR':>6s}  {'Top 3 MDA features'}"
    print(header)
    print("  " + "-" * 86)
    for r in all_results:
        line = (
            f"  {r['name']:<14s} "
            f"{r['cv_mean_accuracy']:>8.4f} "
            f"{r['cv_mean_f1']:>8.4f} "
            f"{r['meta_f1']:>9.4f} "
            f"{r['sharpe_ratio']:>8.4f} "
            f"{r['psr']:>6.4f}  "
            f"{r['top3_mda']}"
        )
        print(line)
    print("=" * 90)

    # Melhor configuração
    best = max(all_results, key=lambda r: r["cv_mean_f1"])
    print(f"\n  Melhor config por CV F1: {best['name']} (F1={best['cv_mean_f1']:.4f})")
    print(f"  Plots salvos em subpastas de: {base_save_dir}")


if __name__ == "__main__":
    main()
