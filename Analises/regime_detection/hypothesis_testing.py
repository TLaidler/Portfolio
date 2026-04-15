#!/usr/bin/env python3
# coding: utf-8
"""
=============================================================================
Hypothesis Testing — Regime Detection BTC/USDT
=============================================================================

Hipótese 5: "Dollar-bar-normalized momentum adapta automaticamente o horizonte
temporal ao regime de volatilidade."

ret_20 em dollar bars NÃO é retorno de 1 dia fixo. É retorno sobre ~$13B de
volume. Em dias calmos, 20 barras cobrem 2-3 dias (momentum de médio prazo).
Em dias voláteis, 20 barras cobrem 6-12 horas (momentum de curto prazo).
O horizonte se adapta ao regime sem nenhum parâmetro — é propriedade emergente
da amostragem por dollar volume (AFML, Teorema 2.1).

Testes:
  T1. Horizonte temporal efetivo: distribuição de horas cobertas por ret_20
  T2. Correlação bars_per_day vs horizonte: volume alto → horizonte curto?
  T3. Autocorrelação condicional: ret_20 tem mais autocorrelação em dias
      voláteis (horizonte curto) vs calmos (horizonte longo)?
  T4. Comparação: ret_20 dollar bars vs ret_1d time bars — o adaptativo
      preserva mais sinal?
  T5. Sharpe condicional por regime de volume

Saída: relatorios/hypothesis_5_adaptive_momentum.md + plots em relatorios/pngs/
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as sp_stats
from utils.savgol import savgol_causal

# Reutilizar DollarBarBuilder do pipeline principal
from regime_detection_advanced import DollarBarBuilder, DEFAULT_CONFIG

# ==========================================================================
# CONFIGURAÇÃO
# ==========================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
REPORT_DIR = os.path.join(SCRIPT_DIR, "relatorios")
PNG_DIR = os.path.join(REPORT_DIR, "pngs")

SG_WINDOW = DEFAULT_CONFIG["savgol_window"]   # 21
SG_POLY = DEFAULT_CONFIG["savgol_polyorder"]  # 3
RET_WINDOW = 20  # janela de momentum em dollar bars

os.makedirs(PNG_DIR, exist_ok=True)


# ==========================================================================
# UTILIDADES
# ==========================================================================
# savgol_causal imported from utils.savgol (canonical, edge-padded version)


def load_data() -> pd.DataFrame:
    """Carrega BTC 1-min e retorna DataFrame."""
    path = os.path.join(DATA_DIR, "btcusdt_1m.csv")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    print(f"  BTC 1-min carregado: {df.shape}")
    return df


def build_dollar_bars(df_1m: pd.DataFrame) -> pd.DataFrame:
    """Constrói dollar bars com config padrão (20 bars/dia)."""
    builder = DollarBarBuilder(
        calibration_days=DEFAULT_CONFIG["dollar_bar_calibration_days"],
        bars_per_day=DEFAULT_CONFIG["dollar_bars_per_day"],
    )
    bars = builder.transform(df_1m)
    print(f"  Dollar bars: {len(bars)} (threshold: ${builder.threshold:,.0f})")
    return bars


def build_time_bars(df_1m: pd.DataFrame, freq: str = "1D") -> pd.DataFrame:
    """Constrói barras de tempo (1 dia) a partir de 1-min."""
    df = df_1m.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")
    bars = df.resample(freq).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()
    bars = bars.reset_index()
    print(f"  Time bars ({freq}): {len(bars)}")
    return bars


# ==========================================================================
# TESTE 1: Horizonte temporal efetivo de ret_20
# ==========================================================================
def test_1_horizon_distribution(bars: pd.DataFrame) -> dict:
    """
    Calcula quantas HORAS cada janela de 20 dollar bars cobre.
    Se ret_20 fosse fixo, seria sempre ~24h. Em dollar bars, varia.
    """
    print("\n" + "=" * 70)
    print("  TESTE 1: Distribuição do horizonte temporal de ret_20")
    print("=" * 70)

    ts = pd.to_datetime(bars["timestamp"])
    # Horizonte em horas entre barra i e barra i-20
    horizons_hours = []
    for i in range(RET_WINDOW, len(ts)):
        delta = (ts.iloc[i] - ts.iloc[i - RET_WINDOW]).total_seconds() / 3600.0
        horizons_hours.append(delta)
    horizons = np.array(horizons_hours)

    stats = {
        "mean_hours": np.mean(horizons),
        "median_hours": np.median(horizons),
        "std_hours": np.std(horizons),
        "min_hours": np.min(horizons),
        "max_hours": np.max(horizons),
        "p10_hours": np.percentile(horizons, 10),
        "p25_hours": np.percentile(horizons, 25),
        "p75_hours": np.percentile(horizons, 75),
        "p90_hours": np.percentile(horizons, 90),
        "cv": np.std(horizons) / np.mean(horizons),  # coef. variação
    }

    print(f"    Media:  {stats['mean_hours']:.1f}h ({stats['mean_hours']/24:.1f} dias)")
    print(f"    Mediana:{stats['median_hours']:.1f}h ({stats['median_hours']/24:.1f} dias)")
    print(f"    Std:    {stats['std_hours']:.1f}h")
    print(f"    Min:    {stats['min_hours']:.1f}h  |  Max: {stats['max_hours']:.1f}h")
    print(f"    P10:    {stats['p10_hours']:.1f}h  |  P90: {stats['p90_hours']:.1f}h")
    print(f"    CV:     {stats['cv']:.3f}")

    if stats["cv"] < 0.10:
        print("    >> CV < 0.10: horizonte quase fixo. Hipótese 5 REFUTADA.")
    elif stats["cv"] < 0.30:
        print("    >> CV moderado (0.10-0.30): alguma adaptação, mas limitada.")
    else:
        print("    >> CV > 0.30: horizonte altamente variável. Hipótese 5 SUPORTADA.")

    # --- Plot ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histograma
    ax = axes[0]
    ax.hist(horizons, bins=80, edgecolor="black", alpha=0.7, color="#3498db")
    ax.axvline(24, color="red", ls="--", lw=2, label="24h (1 dia fixo)")
    ax.axvline(stats["median_hours"], color="green", ls="--", lw=2,
               label=f"Mediana = {stats['median_hours']:.1f}h")
    ax.set_xlabel("Horizonte de ret_20 (horas)")
    ax.set_ylabel("Frequência")
    ax.set_title("Distribuição do Horizonte Temporal de ret_20")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Horizonte ao longo do tempo
    ax = axes[1]
    ts_plot = ts.iloc[RET_WINDOW:]
    ax.scatter(ts_plot, horizons, s=1, alpha=0.3, c="#2c3e50")
    ax.axhline(24, color="red", ls="--", lw=1.5, label="24h")
    ax.set_xlabel("Data")
    ax.set_ylabel("Horizonte (horas)")
    ax.set_title("Horizonte de ret_20 ao Longo do Tempo")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()

    plt.tight_layout()
    fig.savefig(os.path.join(PNG_DIR, "h5_t1_horizon_distribution.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {**stats, "horizons": horizons, "timestamps": ts.iloc[RET_WINDOW:].values}


# ==========================================================================
# TESTE 2: Correlação entre bars_per_day e horizonte
# ==========================================================================
def test_2_bars_per_day_correlation(bars: pd.DataFrame, t1_result: dict) -> dict:
    """
    Se a hipótese é correta: mais bars/dia → horizonte MENOR (correlação negativa).
    """
    print("\n" + "=" * 70)
    print("  TESTE 2: Correlação bars_per_day vs horizonte")
    print("=" * 70)

    ts = pd.to_datetime(bars["timestamp"])
    bars_date = ts.dt.date
    bars_per_day = bars_date.value_counts().sort_index()

    # Alinhar horizonte com dia da barra final de cada janela
    horizons = t1_result["horizons"]
    horizon_dates = pd.to_datetime(t1_result["timestamps"]).date

    # Média do horizonte por dia
    df_h = pd.DataFrame({"date": horizon_dates, "horizon_h": horizons})
    daily_horizon = df_h.groupby("date")["horizon_h"].median()

    # Merge
    df_merge = pd.DataFrame({
        "bars_per_day": bars_per_day,
        "median_horizon_h": daily_horizon,
    }).dropna()

    # Correlação
    rho, p_val = sp_stats.spearmanr(df_merge["bars_per_day"],
                                     df_merge["median_horizon_h"])

    print(f"    N dias: {len(df_merge)}")
    print(f"    Spearman rho: {rho:.4f}")
    print(f"    p-value:      {p_val:.2e}")

    if rho < -0.5 and p_val < 0.01:
        print("    >> Correlação negativa forte e significativa. Hipótese 5 SUPORTADA.")
    elif rho < -0.3 and p_val < 0.05:
        print("    >> Correlação negativa moderada. Hipótese 5 parcialmente suportada.")
    else:
        print("    >> Correlação fraca ou não significativa. Hipótese 5 enfraquecida.")

    # --- Plot ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    ax.scatter(df_merge["bars_per_day"], df_merge["median_horizon_h"],
               s=8, alpha=0.4, c="#2c3e50")
    # Linha de tendência
    z = np.polyfit(df_merge["bars_per_day"], df_merge["median_horizon_h"], 1)
    x_line = np.linspace(df_merge["bars_per_day"].min(),
                         df_merge["bars_per_day"].max(), 100)
    ax.plot(x_line, np.polyval(z, x_line), "r--", lw=2,
            label=f"ρ={rho:.3f}, p={p_val:.1e}")
    ax.set_xlabel("Dollar Bars por Dia")
    ax.set_ylabel("Horizonte Mediano de ret_20 (horas)")
    ax.set_title("Bars/Dia vs Horizonte Temporal")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Série temporal de bars/dia
    ax = axes[1]
    ax.plot(df_merge.index, df_merge["bars_per_day"], lw=0.8, alpha=0.7,
            color="#3498db", label="Bars/dia")
    ax.set_xlabel("Data")
    ax.set_ylabel("Dollar Bars / Dia")
    ax.set_title("Variação de Bars/Dia ao Longo do Tempo")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()

    plt.tight_layout()
    fig.savefig(os.path.join(PNG_DIR, "h5_t2_bars_vs_horizon.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {"spearman_rho": rho, "p_value": p_val, "n_days": len(df_merge)}


# ==========================================================================
# TESTE 3: Autocorrelação condicional por regime de volume
# ==========================================================================
def test_3_conditional_autocorrelation(bars: pd.DataFrame) -> dict:
    """
    Se ret_20 adaptativo é mais eficiente: a autocorrelação de ret_20 deveria
    ser POSITIVA tanto em regimes de alto volume (horizonte curto) quanto em
    regimes de baixo volume (horizonte longo).

    Comparar com autocorrelação de retorno de janela fixa (1 dia) como controle.
    """
    print("\n" + "=" * 70)
    print("  TESTE 3: Autocorrelação condicional de ret_20 por regime de volume")
    print("=" * 70)

    close_raw = bars["close"].values.astype(np.float64)
    close_sg = savgol_causal(close_raw, SG_WINDOW, SG_POLY)
    close_s = pd.Series(close_sg)
    ret_20 = close_s.pct_change(RET_WINDOW).values

    # Volume diário para definir regimes
    ts = pd.to_datetime(bars["timestamp"])
    bars_cp = bars.copy()
    bars_cp["date"] = ts.dt.date
    daily_vol = bars_cp.groupby("date")["dollar_volume"].sum()
    vol_median = daily_vol.median()

    # Classificar cada barra por regime
    bar_daily_vol = bars_cp["date"].map(daily_vol)
    high_vol_mask = bar_daily_vol.values > vol_median
    low_vol_mask = ~high_vol_mask

    # Autocorrelação de ret_20 em cada regime
    valid = ~np.isnan(ret_20)

    def autocorr_lag1(x):
        x = x[~np.isnan(x)]
        if len(x) < 30:
            return np.nan, np.nan
        r = np.corrcoef(x[:-1], x[1:])[0, 1]
        # t-test para significância
        n = len(x) - 1
        t_stat = r * np.sqrt(n - 2) / np.sqrt(1 - r**2 + 1e-12)
        p_val = 2 * (1 - sp_stats.t.cdf(abs(t_stat), df=n - 2))
        return r, p_val

    ret_high = ret_20[valid & high_vol_mask]
    ret_low = ret_20[valid & low_vol_mask]
    ret_all = ret_20[valid]

    ac_high, p_high = autocorr_lag1(ret_high)
    ac_low, p_low = autocorr_lag1(ret_low)
    ac_all, p_all = autocorr_lag1(ret_all)

    print(f"    Autocorrelação lag-1 de ret_20:")
    print(f"      Global:       r={ac_all:.4f}  (p={p_all:.2e}, n={np.sum(valid)})")
    print(f"      Alto volume:  r={ac_high:.4f} (p={p_high:.2e}, n={len(ret_high)})")
    print(f"      Baixo volume: r={ac_low:.4f}  (p={p_low:.2e}, n={len(ret_low)})")

    # Autocorrelação em múltiplos lags para cada regime
    max_lag = 10
    ac_lags_high = []
    ac_lags_low = []
    ac_lags_all = []

    for lag in range(1, max_lag + 1):
        def ac_lag(x, lag):
            x = x[~np.isnan(x)]
            if len(x) < lag + 10:
                return np.nan
            return np.corrcoef(x[:-lag], x[lag:])[0, 1]

        ac_lags_high.append(ac_lag(ret_high, lag))
        ac_lags_low.append(ac_lag(ret_low, lag))
        ac_lags_all.append(ac_lag(ret_all, lag))

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(10, 6))
    lags = list(range(1, max_lag + 1))
    ax.bar(np.array(lags) - 0.2, ac_lags_high, width=0.2, label="Alto Volume",
           color="#e74c3c", alpha=0.8)
    ax.bar(np.array(lags), ac_lags_low, width=0.2, label="Baixo Volume",
           color="#3498db", alpha=0.8)
    ax.bar(np.array(lags) + 0.2, ac_lags_all, width=0.2, label="Global",
           color="#95a5a6", alpha=0.8)
    ax.axhline(0, color="black", lw=0.8)
    # Bandas de confiança 95% (aproximação)
    n_min = min(len(ret_high), len(ret_low))
    ci = 1.96 / np.sqrt(n_min)
    ax.axhline(ci, color="gray", ls=":", lw=1, alpha=0.5)
    ax.axhline(-ci, color="gray", ls=":", lw=1, alpha=0.5)
    ax.set_xlabel("Lag")
    ax.set_ylabel("Autocorrelação")
    ax.set_title("Autocorrelação de ret_20 por Regime de Volume")
    ax.set_xticks(lags)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(os.path.join(PNG_DIR, "h5_t3_conditional_autocorrelation.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "ac_all": ac_all, "p_all": p_all,
        "ac_high_vol": ac_high, "p_high_vol": p_high,
        "ac_low_vol": ac_low, "p_low_vol": p_low,
        "n_high": len(ret_high), "n_low": len(ret_low),
    }


# ==========================================================================
# TESTE 4: Dollar Bars ret_20 vs Time Bars ret_1d
# ==========================================================================
def test_4_dollar_vs_time_bars(
    df_1m: pd.DataFrame, dollar_bars: pd.DataFrame
) -> dict:
    """
    Compara poder preditivo de:
      A) ret_20 SavGol em dollar bars (horizonte adaptativo)
      B) ret_1d SavGol em time bars (horizonte fixo 24h)

    Métrica: autocorrelação, Sharpe de sign(ret) como proxy de momentum.
    """
    print("\n" + "=" * 70)
    print("  TESTE 4: ret_20 (dollar bars) vs ret_1d (time bars)")
    print("=" * 70)

    # --- Dollar bars: ret_20 SavGol ---
    close_db = dollar_bars["close"].values.astype(np.float64)
    close_db_sg = savgol_causal(close_db, SG_WINDOW, SG_POLY)
    ret_20_db = pd.Series(close_db_sg).pct_change(RET_WINDOW).values

    # Retorno futuro (next bar) para medir capacidade preditiva
    actual_ret_db = np.diff(close_db, prepend=close_db[0]) / np.maximum(close_db, 1e-12)

    # --- Time bars: ret_1d SavGol ---
    time_bars = build_time_bars(df_1m, "1D")
    close_tb = time_bars["close"].values.astype(np.float64)
    close_tb_sg = savgol_causal(close_tb, min(SG_WINDOW, len(close_tb)),
                                 SG_POLY)
    ret_1d_tb = pd.Series(close_tb_sg).pct_change(1).values
    actual_ret_tb = np.diff(close_tb, prepend=close_tb[0]) / np.maximum(close_tb, 1e-12)

    # --- Métricas ---
    def momentum_metrics(signal, actual_ret, name):
        valid = ~np.isnan(signal) & ~np.isnan(actual_ret)
        sig = signal[valid]
        act = actual_ret[valid]

        # Shift signal 1 bar forward (predict next bar return)
        sig_shifted = sig[:-1]
        act_next = act[1:]

        # Sign strategy: long se signal > 0, short se < 0
        positions = np.sign(sig_shifted)
        strat_ret = positions * act_next

        sr = np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)
        hit_rate = np.mean((strat_ret > 0).astype(float))

        # Autocorrelação do sinal
        ac1 = np.corrcoef(sig[:-1], sig[1:])[0, 1]

        # Informação: correlação sinal → retorno futuro
        ic = np.corrcoef(sig_shifted, act_next)[0, 1]

        print(f"    {name}:")
        print(f"      N={len(sig_shifted)}, SR={sr:.4f}, Hit={hit_rate:.4f}, "
              f"AC1={ac1:.4f}, IC={ic:.4f}")
        return {
            "n": len(sig_shifted), "sharpe": sr, "hit_rate": hit_rate,
            "autocorr_1": ac1, "information_coeff": ic,
        }

    m_db = momentum_metrics(ret_20_db, actual_ret_db, "ret_20 Dollar Bars")
    m_tb = momentum_metrics(ret_1d_tb, actual_ret_tb, "ret_1d Time Bars")

    # Veredito
    sr_ratio = m_db["sharpe"] / max(abs(m_tb["sharpe"]), 1e-12)
    print(f"\n    Razão Sharpe (dollar/time): {sr_ratio:.2f}x")
    if sr_ratio > 1.2:
        print("    >> Dollar bars > 20% melhor. Hipótese 5 SUPORTADA.")
    elif sr_ratio > 0.8:
        print("    >> Performance similar. Hipótese 5 INCONCLUSIVA.")
    else:
        print("    >> Time bars melhor. Hipótese 5 REFUTADA.")

    # --- Plot ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    metrics = ["sharpe", "hit_rate", "autocorr_1", "information_coeff"]
    labels = ["Sharpe", "Hit Rate", "Autocorr(1)", "IC"]
    vals_db = [m_db[m] for m in metrics]
    vals_tb = [m_tb[m] for m in metrics]

    ax = axes[0]
    x = np.arange(len(metrics))
    ax.bar(x - 0.15, vals_db, 0.3, label="ret_20 Dollar Bars", color="#3498db")
    ax.bar(x + 0.15, vals_tb, 0.3, label="ret_1d Time Bars", color="#e74c3c")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Dollar Bars vs Time Bars: Métricas de Momentum")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")
    ax.axhline(0, color="black", lw=0.8)

    # Retorno acumulado das estratégias simples
    ax = axes[1]
    valid_db = ~np.isnan(ret_20_db)
    sig_db = np.sign(ret_20_db[valid_db][:-1])
    cum_db = np.cumsum(sig_db * actual_ret_db[valid_db][1:])

    valid_tb = ~np.isnan(ret_1d_tb)
    sig_tb = np.sign(ret_1d_tb[valid_tb][:-1])
    cum_tb = np.cumsum(sig_tb * actual_ret_tb[valid_tb][1:])

    ax.plot(cum_db, label=f"ret_20 Dollar Bars (SR={m_db['sharpe']:.4f})",
            lw=1.2, color="#3498db")
    ax.plot(cum_tb, label=f"ret_1d Time Bars (SR={m_tb['sharpe']:.4f})",
            lw=1.2, color="#e74c3c")
    ax.set_xlabel("Barra (índice)")
    ax.set_ylabel("Retorno Acumulado")
    ax.set_title("Sign(momentum) — Retorno Acumulado")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(os.path.join(PNG_DIR, "h5_t4_dollar_vs_time_bars.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {"dollar_bars": m_db, "time_bars": m_tb, "sr_ratio": sr_ratio}


# ==========================================================================
# TESTE 5: Sharpe condicional por regime de volume
# ==========================================================================
def test_5_sharpe_by_volume_regime(bars: pd.DataFrame) -> dict:
    """
    Divide o dataset em quintis de volume diário.
    Computa Sharpe de sign(ret_20) em cada quintil.

    Se hipótese 5 é correta: Sharpe deveria ser positivo em TODOS os quintis,
    pois ret_20 se adapta automaticamente ao regime.
    """
    print("\n" + "=" * 70)
    print("  TESTE 5: Sharpe de sign(ret_20) por quintil de volume")
    print("=" * 70)

    close_raw = bars["close"].values.astype(np.float64)
    close_sg = savgol_causal(close_raw, SG_WINDOW, SG_POLY)
    ret_20 = pd.Series(close_sg).pct_change(RET_WINDOW).values
    actual_ret = np.diff(close_raw, prepend=close_raw[0]) / np.maximum(close_raw, 1e-12)

    ts = pd.to_datetime(bars["timestamp"])
    bars_cp = bars.copy()
    bars_cp["date"] = ts.dt.date
    daily_dvol = bars_cp.groupby("date")["dollar_volume"].sum()

    # Quintis
    quintile_labels = pd.qcut(daily_dvol, 5, labels=[1, 2, 3, 4, 5])
    bar_quintile = bars_cp["date"].map(quintile_labels).values

    results_by_q = {}
    valid = ~np.isnan(ret_20)

    print(f"    {'Quintil':>8s} {'N bars':>8s} {'SR':>10s} {'Hit%':>8s} "
          f"{'Vol Med ($B)':>14s} {'Hor Med (h)':>12s}")
    print(f"    {'-'*62}")

    # Horizonte mediano por quintil
    horizons = np.full(len(bars), np.nan)
    for i in range(RET_WINDOW, len(ts)):
        horizons[i] = (ts.iloc[i] - ts.iloc[i - RET_WINDOW]).total_seconds() / 3600.0

    for q in range(1, 6):
        mask = (bar_quintile == q) & valid
        idx = np.where(mask)[0]
        idx = idx[idx > 0]  # precisa de pelo menos 1 barra anterior

        if len(idx) < 30:
            print(f"    Q{q}: insuficiente (n={len(idx)})")
            continue

        sig = np.sign(ret_20[idx[:-1]])
        strat = sig * actual_ret[idx[1:]]
        sr = np.mean(strat) / max(np.std(strat, ddof=1), 1e-12)
        hit = np.mean((strat > 0).astype(float))

        # Volume mediano do quintil
        dates_q = bars_cp.iloc[idx]["date"].unique()
        vol_med = daily_dvol[dates_q].median() / 1e9

        # Horizonte mediano
        hor_med = np.nanmedian(horizons[idx])

        results_by_q[q] = {
            "n": len(idx), "sharpe": sr, "hit_rate": hit,
            "volume_median_B": vol_med, "horizon_median_h": hor_med,
        }
        print(f"    Q{q:>7d} {len(idx):>8d} {sr:>10.4f} {hit:>7.1%} "
              f"{vol_med:>13.1f} {hor_med:>11.1f}")

    # Todos positivos?
    sharpes = [v["sharpe"] for v in results_by_q.values()]
    all_positive = all(s > 0 for s in sharpes)
    print(f"\n    Sharpe positivo em todos os quintis: {'SIM' if all_positive else 'NAO'}")

    if all_positive:
        print("    >> Momentum funciona em todos os regimes de volume. Hipótese 5 SUPORTADA.")
    else:
        neg = [q for q, v in results_by_q.items() if v["sharpe"] <= 0]
        print(f"    >> Sharpe negativo nos quintis {neg}. Hipótese 5 parcialmente refutada.")

    # Monotonia: horizonte deveria diminuir com volume
    hor_vs_vol = sp_stats.spearmanr(
        [v["volume_median_B"] for v in results_by_q.values()],
        [v["horizon_median_h"] for v in results_by_q.values()]
    )
    print(f"    Correlacao volume vs horizonte (quintis): rho={hor_vs_vol.statistic:.3f}, "
          f"p={hor_vs_vol.pvalue:.3f}")

    # --- Plot ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    qs = sorted(results_by_q.keys())

    ax = axes[0]
    sharpes_q = [results_by_q[q]["sharpe"] for q in qs]
    colors = ["#2ecc71" if s > 0 else "#e74c3c" for s in sharpes_q]
    ax.bar(qs, sharpes_q, color=colors, edgecolor="black", alpha=0.8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Quintil de Volume Diário (1=baixo, 5=alto)")
    ax.set_ylabel("Sharpe Ratio (sign momentum)")
    ax.set_title("Sharpe de sign(ret_20) por Regime de Volume")
    ax.set_xticks(qs)
    ax.grid(True, alpha=0.3, axis="y")

    ax = axes[1]
    vols = [results_by_q[q]["volume_median_B"] for q in qs]
    hors = [results_by_q[q]["horizon_median_h"] for q in qs]
    ax.bar(np.array(qs) - 0.15, vols, 0.3, label="Volume ($B)", color="#3498db")
    ax2 = ax.twinx()
    ax2.bar(np.array(qs) + 0.15, hors, 0.3, label="Horizonte (h)", color="#e67e22")
    ax.set_xlabel("Quintil de Volume")
    ax.set_ylabel("Volume Mediano ($B)", color="#3498db")
    ax2.set_ylabel("Horizonte Mediano (h)", color="#e67e22")
    ax.set_title("Volume vs Horizonte por Quintil")
    ax.set_xticks(qs)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    fig.savefig(os.path.join(PNG_DIR, "h5_t5_sharpe_by_volume_regime.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)

    return results_by_q


# ==========================================================================
# TESTE 7: Cross-Market — S&P500 e IBOVESPA
# ==========================================================================
def _run_single_market_h5(
    label: str,
    df_1m: pd.DataFrame,
    bars_per_day: int = 20,
    calibration_days: int = 30,
) -> dict:
    """
    Roda os testes H5 essenciais para um unico mercado:
      - Horizonte CV
      - Correlacao bars/dia vs horizonte
      - Sharpe sign(ret_20) SavGol em dollar bars
      - Sharpe sign(ret_1d) em time bars (controle)
      - Ablacao filtro (SavGol vs raw vs MA)
    """
    print(f"\n    --- {label} ---")

    # Dollar bars
    builder = DollarBarBuilder(
        calibration_days=calibration_days,
        bars_per_day=bars_per_day,
    )
    bars = builder.transform(df_1m)
    print(f"    Dollar bars: {len(bars)} (threshold: {builder.threshold:,.0f})")

    if len(bars) < RET_WINDOW * 5:
        print(f"    SKIP: menos de {RET_WINDOW*5} dollar bars. Insuficiente.")
        return {"label": label, "skip": True}

    ts = pd.to_datetime(bars["timestamp"])
    close_raw = bars["close"].values.astype(np.float64)

    # --- Horizonte ---
    horizons = []
    for i in range(RET_WINDOW, len(ts)):
        delta = (ts.iloc[i] - ts.iloc[i - RET_WINDOW]).total_seconds() / 3600.0
        horizons.append(delta)
    horizons = np.array(horizons)
    cv = np.std(horizons) / np.mean(horizons) if np.mean(horizons) > 0 else 0

    # --- Bars/dia vs horizonte (Spearman) ---
    bars_date = ts.dt.date
    bars_per_day_series = bars_date.value_counts().sort_index()
    horizon_dates = pd.to_datetime(ts.iloc[RET_WINDOW:].values).date
    df_h = pd.DataFrame({"date": horizon_dates, "horizon_h": horizons})
    daily_horizon = df_h.groupby("date")["horizon_h"].median()
    df_merge = pd.DataFrame({
        "bars_per_day": bars_per_day_series,
        "median_horizon_h": daily_horizon,
    }).dropna()
    if len(df_merge) > 5:
        rho, p_rho = sp_stats.spearmanr(df_merge["bars_per_day"],
                                         df_merge["median_horizon_h"])
    else:
        rho, p_rho = np.nan, np.nan

    # --- Momentum metrics helper ---
    actual_ret = np.diff(close_raw, prepend=close_raw[0]) / np.maximum(close_raw, 1e-12)

    def _momentum_sr(signal, actual_ret):
        valid = ~np.isnan(signal) & ~np.isnan(actual_ret)
        sig = signal[valid]
        act = actual_ret[valid]
        if len(sig) < 30:
            return np.nan, np.nan, np.nan
        sig_s = sig[:-1]
        act_n = act[1:]
        pos = np.sign(sig_s)
        strat = pos * act_n
        sr = np.mean(strat) / max(np.std(strat, ddof=1), 1e-12)
        hit = np.mean((strat > 0).astype(float))
        ic = np.corrcoef(sig_s, act_n)[0, 1]
        return sr, hit, ic

    # --- SavGol, Raw, MA ---
    close_sg = savgol_causal(close_raw, SG_WINDOW, SG_POLY)
    close_ma = pd.Series(close_raw).rolling(SG_WINDOW, min_periods=SG_WINDOW).mean().values

    ret_sg = pd.Series(close_sg).pct_change(RET_WINDOW).values
    ret_raw = pd.Series(close_raw).pct_change(RET_WINDOW).values
    ret_ma = pd.Series(close_ma).pct_change(RET_WINDOW).values

    sr_sg, hit_sg, ic_sg = _momentum_sr(ret_sg, actual_ret)
    sr_raw, hit_raw, ic_raw = _momentum_sr(ret_raw, actual_ret)
    sr_ma, hit_ma, ic_ma = _momentum_sr(ret_ma, actual_ret)

    # --- Time bars ret_1d como controle ---
    tb = df_1m.copy()
    tb["timestamp"] = pd.to_datetime(tb["timestamp"])
    tb = tb.set_index("timestamp").resample("1D").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }).dropna().reset_index()

    sr_time = np.nan
    if len(tb) > 30:
        close_tb = tb["close"].values.astype(np.float64)
        close_tb_sg = savgol_causal(close_tb, min(SG_WINDOW, len(close_tb)), SG_POLY)
        ret_tb = pd.Series(close_tb_sg).pct_change(1).values
        actual_tb = np.diff(close_tb, prepend=close_tb[0]) / np.maximum(close_tb, 1e-12)
        sr_time, _, _ = _momentum_sr(ret_tb, actual_tb)

    sr_ratio = sr_sg / max(abs(sr_time), 1e-12) if not np.isnan(sr_time) else np.nan

    result = {
        "label": label, "skip": False,
        "n_bars_1m": len(df_1m), "n_dollar_bars": len(bars),
        "horizon_mean_h": np.mean(horizons),
        "horizon_median_h": np.median(horizons),
        "horizon_cv": cv,
        "rho_bars_horizon": rho, "p_rho": p_rho,
        "sr_savgol": sr_sg, "hit_savgol": hit_sg, "ic_savgol": ic_sg,
        "sr_raw": sr_raw, "hit_raw": hit_raw,
        "sr_ma": sr_ma, "hit_ma": hit_ma,
        "sr_time_1d": sr_time,
        "sr_ratio_dollar_time": sr_ratio,
    }

    print(f"    Horizonte: media={np.mean(horizons):.1f}h, CV={cv:.3f}")
    print(f"    rho(bars/dia, horizonte) = {rho:.3f} (p={p_rho:.2e})")
    print(f"    SR SavGol={sr_sg:.4f}  Raw={sr_raw:.4f}  MA={sr_ma:.4f}  "
          f"Time1d={sr_time:.4f}")
    print(f"    SR ratio (dollar_sg / time_1d) = {sr_ratio:.2f}x")

    return result


def test_7_cross_market() -> dict:
    """
    Testa Hipotese 5 em S&P500 (SPY) e IBOVESPA (BOVA11).
    Compara com BTC para avaliar universalidade.
    """
    print("\n" + "=" * 70)
    print("  TESTE 7: Cross-Market — S&P500 e IBOVESPA")
    print("=" * 70)

    markets = {}

    # S&P500 ETF (minutely)
    sp_path = os.path.join(DATA_DIR, "sp500_etf_1m.csv")
    if os.path.exists(sp_path):
        df_sp = pd.read_csv(sp_path, parse_dates=["timestamp"])
        markets["SP500_ETF"] = _run_single_market_h5("S&P500 ETF (SPY)", df_sp)
    else:
        print("  [SKIP] sp500_etf_1m.csv nao encontrado")

    # IBOVESPA ETF (minutely)
    ibov_path = os.path.join(DATA_DIR, "ibov_etf_1m.csv")
    if os.path.exists(ibov_path):
        df_ibov = pd.read_csv(ibov_path, parse_dates=["timestamp"])
        markets["IBOV_ETF"] = _run_single_market_h5("IBOVESPA ETF (BOVA11)", df_ibov)
    else:
        print("  [SKIP] ibov_etf_1m.csv nao encontrado")

    # BTC para comparacao (recomputa rapido)
    btc_path = os.path.join(DATA_DIR, "btcusdt_1m.csv")
    if os.path.exists(btc_path):
        df_btc = pd.read_csv(btc_path, parse_dates=["timestamp"])
        markets["BTC"] = _run_single_market_h5("BTC/USDT", df_btc)

    # --- Resumo ---
    print(f"\n    {'Mercado':<20s} {'N dbars':>8s} {'CV':>6s} {'rho':>7s} "
          f"{'SR_sg':>8s} {'SR_raw':>8s} {'SR_ma':>8s} {'SR_time':>8s} {'Ratio':>7s}")
    print(f"    {'-'*82}")
    for key, r in markets.items():
        if r.get("skip"):
            print(f"    {r['label']:<20s} SKIP")
            continue
        print(f"    {r['label']:<20s} {r['n_dollar_bars']:>8d} {r['horizon_cv']:>6.3f} "
              f"{r['rho_bars_horizon']:>7.3f} {r['sr_savgol']:>8.4f} "
              f"{r['sr_raw']:>8.4f} {r['sr_ma']:>8.4f} "
              f"{r['sr_time_1d']:>8.4f} {r['sr_ratio_dollar_time']:>6.1f}x")

    # --- Plot comparativo ---
    valid_markets = {k: v for k, v in markets.items() if not v.get("skip")}
    if len(valid_markets) >= 2:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        names = [v["label"] for v in valid_markets.values()]
        x = np.arange(len(names))

        # Panel 1: Horizon CV
        ax = axes[0]
        cvs = [v["horizon_cv"] for v in valid_markets.values()]
        colors_cv = ["#2ecc71" if c > 0.3 else "#e67e22" if c > 0.1 else "#e74c3c"
                     for c in cvs]
        ax.bar(x, cvs, color=colors_cv, edgecolor="black", alpha=0.8)
        ax.axhline(0.3, color="green", ls="--", lw=1, alpha=0.5, label="CV=0.3 (limiar)")
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=8, rotation=15)
        ax.set_ylabel("Coeficiente de Variacao")
        ax.set_title("T7a: Variabilidade do Horizonte")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

        # Panel 2: Sharpe por filtro
        ax = axes[1]
        w = 0.2
        sr_sg = [v["sr_savgol"] for v in valid_markets.values()]
        sr_rw = [v["sr_raw"] for v in valid_markets.values()]
        sr_m = [v["sr_ma"] for v in valid_markets.values()]
        ax.bar(x - w, sr_sg, w, label="SavGol", color="#3498db")
        ax.bar(x, sr_rw, w, label="Raw", color="#95a5a6")
        ax.bar(x + w, sr_m, w, label="MA(21)", color="#e67e22")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=8, rotation=15)
        ax.set_ylabel("Sharpe Ratio")
        ax.set_title("T7b: Sharpe por Filtro (Dollar Bars)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

        # Panel 3: Dollar bars vs Time bars
        ax = axes[2]
        sr_db = [v["sr_savgol"] for v in valid_markets.values()]
        sr_tb = [v["sr_time_1d"] for v in valid_markets.values()]
        ax.bar(x - 0.15, sr_db, 0.3, label="Dollar Bars + SavGol", color="#3498db")
        ax.bar(x + 0.15, sr_tb, 0.3, label="Time Bars 1D + SavGol", color="#e74c3c")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=8, rotation=15)
        ax.set_ylabel("Sharpe Ratio")
        ax.set_title("T7c: Dollar Bars vs Time Bars")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()
        fig.savefig(os.path.join(PNG_DIR, "h5_t7_cross_market.png"),
                    dpi=150, bbox_inches="tight")
        plt.close(fig)

    return markets


# ==========================================================================
# PLOT: Candlestick + SavGol overlay (time bars vs dollar bars)
# ==========================================================================
def _plot_candlestick_ax(ax, bars_df, title, n_bars=100):
    """Desenha candlestick manual num eixo matplotlib."""
    df = bars_df.tail(n_bars).reset_index(drop=True)
    ts = pd.to_datetime(df["timestamp"])
    o = df["open"].values.astype(float)
    h = df["high"].values.astype(float)
    l = df["low"].values.astype(float)
    c = df["close"].values.astype(float)

    # Largura minima do body para que candles com open~=close sejam visiveis
    price_range = max(np.nanmax(h) - np.nanmin(l), 1e-8)
    min_body = price_range * 0.003

    for i in range(len(df)):
        color = "#2ecc71" if c[i] >= o[i] else "#e74c3c"
        # Wick
        ax.plot([i, i], [l[i], h[i]], color=color, lw=0.8, zorder=2)
        # Body
        body_bot = min(o[i], c[i])
        body_top = max(o[i], c[i])
        body_h = max(body_top - body_bot, min_body)
        ax.bar(i, body_h, bottom=body_bot, width=0.6, color=color,
               edgecolor=color, linewidth=0.5, zorder=3)

    ax.set_title(title, fontsize=10)
    ax.set_xlim(-1, len(df))

    # Y-axis fixado ao range de precos reais (sem artefatos do filtro)
    y_lo = np.nanmin(l)
    y_hi = np.nanmax(h)
    margin = (y_hi - y_lo) * 0.05
    ax.set_ylim(y_lo - margin, y_hi + margin)

    # Tick labels: ~5 dates
    step = max(len(df) // 5, 1)
    ticks = list(range(0, len(df), step))
    labels = [ts.iloc[t].strftime("%Y-%m-%d\n%H:%M") for t in ticks]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontsize=7, rotation=30)
    ax.grid(True, alpha=0.2)
    return df


def plot_candlestick_with_savgol(
    label: str,
    df_1m: pd.DataFrame,
    fname_prefix: str,
    n_display: int = 100,
) -> str:
    """
    Gera 2 paineis (time bars 1D vs dollar bars) com candlestick + SavGol overlay.
    Retorna o filename do PNG salvo.
    """
    print(f"\n    Gerando candlestick + SavGol: {label}")

    # --- Time bars (1D) ---
    tb = df_1m.copy()
    tb["timestamp"] = pd.to_datetime(tb["timestamp"])
    tb = tb.set_index("timestamp").resample("1D").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }).dropna().reset_index()

    close_tb = tb["close"].values.astype(np.float64)
    sg_tb = savgol_causal(close_tb, min(SG_WINDOW, len(close_tb)), SG_POLY)

    # --- Dollar bars ---
    builder = DollarBarBuilder(
        calibration_days=DEFAULT_CONFIG["dollar_bar_calibration_days"],
        bars_per_day=DEFAULT_CONFIG["dollar_bars_per_day"],
    )
    db = builder.transform(df_1m)
    close_db = db["close"].values.astype(np.float64)
    sg_db = savgol_causal(close_db, SG_WINDOW, SG_POLY)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))

    def _overlay_savgol(ax, df_slice, sg_full, start_idx):
        """Plota SavGol sobre candlestick, clipando ao range de preco."""
        sg_slice = sg_full[start_idx:].copy()
        xs = np.arange(len(df_slice))
        # Limites de preco visivel
        lo = float(df_slice["low"].min())
        hi = float(df_slice["high"].max())
        # Clipar SavGol ao range de preco (remove artefatos de borda)
        margin = (hi - lo) * 0.05
        valid = ~np.isnan(sg_slice)
        sg_slice = np.clip(sg_slice, lo - margin, hi + margin)
        if np.any(valid):
            ax.plot(xs[valid], sg_slice[valid], color="#ff6600",
                    lw=2.2, label=f"SavGol causal (w={SG_WINDOW}, p={SG_POLY})",
                    zorder=5, alpha=0.9)
        ax.legend(fontsize=8, loc="upper left")
        ax.set_ylabel("Preco")

    # --- Panel 1: Time bars ---
    df_tb = _plot_candlestick_ax(
        axes[0], tb, f"{label} — Time Bars (1D)", n_bars=n_display)
    start_tb = max(0, len(tb) - n_display)
    _overlay_savgol(axes[0], df_tb, sg_tb, start_tb)

    # --- Panel 2: Dollar bars ---
    df_db = _plot_candlestick_ax(
        axes[1], db, f"{label} — Dollar Bars", n_bars=n_display)
    start_db = max(0, len(db) - n_display)
    _overlay_savgol(axes[1], df_db, sg_db, start_db)

    plt.suptitle(f"Filtro SavGol Causal sobre Candlestick — {label}",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()

    fname = f"h5_candlestick_savgol_{fname_prefix}.png"
    fig.savefig(os.path.join(PNG_DIR, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"    Salvo: {fname}")
    return fname


def plot_savgol_window_explanation(
    df_1m: pd.DataFrame,
    n_display: int = 60,
) -> str:
    """
    Plot didatico: mostra a janela de 21 dollar bars usada pelo SavGol causal
    para calcular UM ponto especifico (marcado com X vermelho).
    Duas linhas verticais delimitam a janela [i-w+1, i].
    """
    print("\n    Gerando plot explicativo da janela SavGol...")

    builder = DollarBarBuilder(
        calibration_days=DEFAULT_CONFIG["dollar_bar_calibration_days"],
        bars_per_day=DEFAULT_CONFIG["dollar_bars_per_day"],
    )
    db = builder.transform(df_1m)
    close_db = db["close"].values.astype(np.float64)
    sg_db = savgol_causal(close_db, SG_WINDOW, SG_POLY)
    ts = pd.to_datetime(db["timestamp"])

    # Ultimas n_display barras
    df_slice = db.tail(n_display).reset_index(drop=True)
    start = max(0, len(db) - n_display)
    sg_slice = sg_db[start:]
    close_slice = close_db[start:]

    # Ponto de exemplo: proximo do meio do grafico
    mid = n_display // 2
    # Garantir que a janela inteira cabe no grafico (mid >= SG_WINDOW - 1)
    mid = max(SG_WINDOW, mid)
    mid = min(mid, n_display - 1)

    w = SG_WINDOW
    win_start = mid - (w - 1)  # primeira barra da janela
    win_end = mid              # barra atual (ponto calculado)

    fig, ax = plt.subplots(1, 1, figsize=(16, 7))

    # --- Candlestick ---
    o = df_slice["open"].values.astype(float)
    h = df_slice["high"].values.astype(float)
    l = df_slice["low"].values.astype(float)
    c = df_slice["close"].values.astype(float)
    price_range = max(np.nanmax(h) - np.nanmin(l), 1e-8)
    min_body = price_range * 0.003

    for i in range(len(df_slice)):
        color = "#2ecc71" if c[i] >= o[i] else "#e74c3c"
        ax.plot([i, i], [l[i], h[i]], color=color, lw=0.8, zorder=2)
        body_bot = min(o[i], c[i])
        body_top = max(o[i], c[i])
        body_h = max(body_top - body_bot, min_body)
        # Barras dentro da janela: leve destaque
        if win_start <= i <= win_end:
            ax.bar(i, body_h, bottom=body_bot, width=0.6, color=color,
                   edgecolor="black", linewidth=0.8, zorder=3)
        else:
            ax.bar(i, body_h, bottom=body_bot, width=0.6, color=color,
                   edgecolor=color, linewidth=0.5, zorder=3, alpha=0.4)

    # --- SavGol line ---
    xs = np.arange(len(df_slice))
    valid = ~np.isnan(sg_slice)
    lo_price = float(np.nanmin(l))
    hi_price = float(np.nanmax(h))
    margin = (hi_price - lo_price) * 0.05
    sg_clipped = np.clip(sg_slice, lo_price - margin, hi_price + margin)
    if np.any(valid):
        ax.plot(xs[valid], sg_clipped[valid], color="#ff6600", lw=2.2,
                label=f"SavGol causal (w={w}, p={SG_POLY})", zorder=5, alpha=0.9)

    # --- Janela: area sombreada ---
    ax.axvspan(win_start - 0.5, win_end + 0.5, color="#3498db", alpha=0.12,
               zorder=1, label=f"Janela SavGol ({w} barras)")

    # --- Linhas verticais nos limites da janela ---
    ax.axvline(win_start - 0.5, color="#2980b9", ls="--", lw=1.5, zorder=6)
    ax.axvline(win_end + 0.5, color="#2980b9", ls="--", lw=1.5, zorder=6)

    # --- Ponto X vermelho no valor SavGol calculado ---
    sg_val = sg_clipped[mid]
    if not np.isnan(sg_val):
        ax.scatter([mid], [sg_val], color="red", s=120, marker="X",
                   zorder=10, edgecolors="black", linewidths=0.8,
                   label=f"Ponto calculado (bar {mid})")

    # --- Anotacao ---
    ts_slice = pd.to_datetime(df_slice["timestamp"])
    t_start = ts_slice.iloc[win_start]
    t_end = ts_slice.iloc[win_end]
    delta_h = (t_end - t_start).total_seconds() / 3600.0
    annot_text = (f"Janela: {w} dollar bars\n"
                  f"De {t_start.strftime('%m-%d %H:%M')} "
                  f"a {t_end.strftime('%m-%d %H:%M')}\n"
                  f"= {delta_h:.1f} horas ({delta_h/24:.1f} dias)")
    # Posicionar anotacao acima do ponto
    ax.annotate(annot_text, xy=(mid, sg_val),
                xytext=(mid + 8, hi_price - price_range * 0.05),
                fontsize=9, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#2980b9",
                          alpha=0.9),
                arrowprops=dict(arrowstyle="->", color="#2980b9", lw=1.5),
                zorder=11)

    # --- Eixos ---
    ax.set_xlim(-1, len(df_slice))
    y_lo = lo_price - (hi_price - lo_price) * 0.05
    y_hi = hi_price + (hi_price - lo_price) * 0.1
    ax.set_ylim(y_lo, y_hi)

    step = max(len(df_slice) // 6, 1)
    ticks = list(range(0, len(df_slice), step))
    labels = [ts_slice.iloc[t].strftime("%Y-%m-%d\n%H:%M") for t in ticks]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontsize=8, rotation=30)
    ax.set_ylabel("Preco (USD)", fontsize=11)
    ax.set_title("SavGol Causal: Janela de Calculo em Dollar Bars — BTC/USDT",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    fname = "h5_savgol_window_explanation.png"
    fig.savefig(os.path.join(PNG_DIR, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"    Salvo: {fname}")
    return fname


# ==========================================================================
# TESTE 6: Ablacao do filtro — SavGol vs Raw vs MA
# ==========================================================================
def test_6_filter_ablation(bars: pd.DataFrame) -> dict:
    """
    Isola o efeito do filtro mantendo dollar bars e ret_20 constantes.

      A) raw:    pct_change(20) no close bruto
      B) SavGol: pct_change(20) no close SavGol causal (window=21, poly=3)
      C) MA(21): pct_change(20) no close suavizado por MA simples (window=21)

    Mesma janela de suavização (21) para SavGol e MA. Comparação justa.
    """
    print("\n" + "=" * 70)
    print("  TESTE 6: Ablacao do filtro — SavGol vs Raw vs MA(21)")
    print("=" * 70)

    close_raw = bars["close"].values.astype(np.float64)

    # Três versões do close
    close_sg = savgol_causal(close_raw, SG_WINDOW, SG_POLY)
    close_ma = pd.Series(close_raw).rolling(SG_WINDOW, min_periods=SG_WINDOW).mean().values

    filters = {
        "raw":    close_raw,
        "savgol": close_sg,
        "ma_21":  close_ma,
    }

    # Retorno futuro bruto (para medir capacidade preditiva)
    actual_ret = np.diff(close_raw, prepend=close_raw[0]) / np.maximum(close_raw, 1e-12)

    results = {}

    print(f"\n    {'Filtro':<10s} {'N':>7s} {'SR':>10s} {'Hit%':>8s} "
          f"{'AC1':>8s} {'IC':>8s} {'Lag(bars)':>10s}")
    print(f"    {'-'*62}")

    for name, close_filtered in filters.items():
        signal = pd.Series(close_filtered).pct_change(RET_WINDOW).values
        valid = ~np.isnan(signal) & ~np.isnan(actual_ret)

        sig = signal[valid]
        act = actual_ret[valid]

        # Shift: signal[t] prediz actual_ret[t+1]
        sig_shifted = sig[:-1]
        act_next = act[1:]

        positions = np.sign(sig_shifted)
        strat_ret = positions * act_next

        sr = np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)
        hit = np.mean((strat_ret > 0).astype(float))
        ac1 = np.corrcoef(sig[:-1], sig[1:])[0, 1] if len(sig) > 2 else np.nan
        ic = np.corrcoef(sig_shifted, act_next)[0, 1]

        # Medir lag do filtro: cross-correlação entre signal e retorno futuro
        # Em qual offset a correlação é máxima?
        max_offset = 5
        cc = []
        for offset in range(max_offset + 1):
            if offset == 0:
                c = np.corrcoef(sig[:-1], act[1:])[0, 1]
            else:
                c = np.corrcoef(sig[:-1-offset], act[1+offset:])[0, 1]
            cc.append(c)
        best_offset = int(np.argmax(cc))

        results[name] = {
            "n": len(sig_shifted), "sharpe": sr, "hit_rate": hit,
            "autocorr_1": ac1, "information_coeff": ic,
            "best_lag": best_offset,
        }
        print(f"    {name:<10s} {len(sig_shifted):>7d} {sr:>10.4f} {hit:>7.1%} "
              f"{ac1:>8.4f} {ic:>8.4f} {best_offset:>10d}")

    # Veredito
    srs = {k: v["sharpe"] for k, v in results.items()}
    best = max(srs, key=srs.get)
    worst = min(srs, key=srs.get)

    print(f"\n    Melhor filtro: {best} (SR={srs[best]:.4f})")
    print(f"    Pior filtro:  {worst} (SR={srs[worst]:.4f})")

    sg_vs_raw = srs["savgol"] / max(abs(srs["raw"]), 1e-12)
    sg_vs_ma = srs["savgol"] / max(abs(srs["ma_21"]), 1e-12)
    print(f"    SavGol/Raw:   {sg_vs_raw:.2f}x")
    print(f"    SavGol/MA:    {sg_vs_ma:.2f}x")

    if best == "raw":
        print("    >> O filtro NAO ajuda. O sinal esta nas dollar bars, nao no SavGol.")
    elif best == "savgol":
        if sg_vs_raw > 1.2:
            print("    >> SavGol superior (>20%). Filtro causal preserva derivadas locais.")
        else:
            print("    >> SavGol marginalmente melhor. Filtro ajuda, mas nao e decisivo.")
    else:
        print("    >> MA melhor que SavGol. Resultado inesperado — investigar lag.")

    # --- Plot ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Métricas comparativas
    ax = axes[0]
    metric_names = ["sharpe", "hit_rate", "information_coeff"]
    metric_labels = ["Sharpe", "Hit Rate", "IC"]
    x = np.arange(len(metric_names))
    width = 0.25
    colors = {"raw": "#95a5a6", "savgol": "#3498db", "ma_21": "#e67e22"}

    for i, (fname, fres) in enumerate(results.items()):
        vals = [fres[m] for m in metric_names]
        ax.bar(x + i * width, vals, width, label=fname, color=colors[fname])

    ax.set_xticks(x + width)
    ax.set_xticklabels(metric_labels)
    ax.set_title("Ablacao do Filtro: SavGol vs Raw vs MA(21)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")
    ax.axhline(0, color="black", lw=0.8)

    # Retorno acumulado
    ax = axes[1]
    for fname, close_filtered in filters.items():
        signal = pd.Series(close_filtered).pct_change(RET_WINDOW).values
        valid = ~np.isnan(signal)
        sig = np.sign(signal[valid][:-1])
        cum = np.cumsum(sig * actual_ret[valid][1:])
        ax.plot(cum, label=f"{fname} (SR={results[fname]['sharpe']:.4f})",
                lw=1.2, color=colors[fname])

    ax.set_xlabel("Barra (indice)")
    ax.set_ylabel("Retorno Acumulado")
    ax.set_title("sign(ret_20) — Retorno Acumulado por Filtro")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(os.path.join(PNG_DIR, "h5_t6_filter_ablation.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)

    return results


# ==========================================================================
# TESTE 8: Random Walk Null Model (GATE TEST)
# ==========================================================================
def test_8_random_walk_null(df_1m: pd.DataFrame, bars: pd.DataFrame,
                            n_simulations: int = 500) -> dict:
    """
    Null hypothesis: SR=0.18 is an artifact of the pipeline
    (SavGol + pct_change + sign) applied to any series with similar volatility.

    Generates GBM paths with drift=0 and drift=real, applies the SAME pipeline,
    and computes null SR distribution. If P95_null >= SR_real, discovery is dead.
    """
    print("\n" + "=" * 70)
    print("  TESTE 8: Random Walk Null Model")
    print("=" * 70)

    close_raw = bars["close"].values.astype(np.float64)
    close_sg = savgol_causal(close_raw, SG_WINDOW, SG_POLY)
    signal = pd.Series(close_sg).pct_change(RET_WINDOW).values
    actual_ret = np.diff(close_raw, prepend=close_raw[0]) / np.maximum(close_raw, 1e-12)

    valid = ~np.isnan(signal) & ~np.isnan(actual_ret)
    sig = signal[valid]
    act = actual_ret[valid]
    positions = np.sign(sig[:-1])
    strat_ret = positions * act[1:]
    sr_real = np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)
    print(f"    SR real (per-bar): {sr_real:.4f}")

    # Calibrate from real dollar bar returns
    bar_returns = bars["close"].pct_change().dropna().values
    sigma = np.std(bar_returns)
    drift_real = np.mean(bar_returns)
    n_bars = len(close_raw)
    print(f"    Calibration: sigma={sigma:.6f}, drift_real={drift_real:.6f}, n_bars={n_bars}")

    def _run_simulation(mu, sigma, n, seed):
        """Generate GBM path, apply SavGol + sign(ret_20), compute SR."""
        rng = np.random.RandomState(seed)
        rets = mu + sigma * rng.randn(n - 1)
        prices = np.cumprod(np.concatenate([[100.0], 1 + rets]))
        sg = savgol_causal(prices, SG_WINDOW, SG_POLY)
        sig_sim = pd.Series(sg).pct_change(RET_WINDOW).values
        act_sim = np.diff(prices, prepend=prices[0]) / np.maximum(prices, 1e-12)
        v = ~np.isnan(sig_sim) & ~np.isnan(act_sim)
        s = sig_sim[v]
        a = act_sim[v]
        if len(s) < RET_WINDOW + 2:
            return np.nan
        pos = np.sign(s[:-1])
        sr = pos * a[1:]
        return np.mean(sr) / max(np.std(sr, ddof=1), 1e-12)

    # Run simulations: drift=0 and drift=real
    print(f"    Running {n_simulations} simulations (drift=0)...")
    sr_null_zero = np.array([_run_simulation(0.0, sigma, n_bars, i)
                             for i in range(n_simulations)])
    sr_null_zero = sr_null_zero[~np.isnan(sr_null_zero)]

    print(f"    Running {n_simulations} simulations (drift=real)...")
    sr_null_drift = np.array([_run_simulation(drift_real, sigma, n_bars, i + 10000)
                              for i in range(n_simulations)])
    sr_null_drift = sr_null_drift[~np.isnan(sr_null_drift)]

    p5_z, p50_z, p95_z = np.percentile(sr_null_zero, [5, 50, 95])
    p5_d, p50_d, p95_d = np.percentile(sr_null_drift, [5, 50, 95])

    pvalue_zero = np.mean(sr_null_zero >= sr_real)
    pvalue_drift = np.mean(sr_null_drift >= sr_real)

    print(f"\n    Drift=0:    P5={p5_z:.4f}  P50={p50_z:.4f}  P95={p95_z:.4f}  "
          f"p-value={pvalue_zero:.4f}")
    print(f"    Drift=real: P5={p5_d:.4f}  P50={p50_d:.4f}  P95={p95_d:.4f}  "
          f"p-value={pvalue_drift:.4f}")

    # Verdict
    if pvalue_zero < 0.05:
        verdict_zero = "PASS (SR_real > 95% of null)"
    else:
        verdict_zero = "FAIL (SR_real within null distribution)"

    if pvalue_drift < 0.05:
        verdict_drift = "PASS (strategy adds value beyond buy-and-hold)"
    else:
        verdict_drift = "FAIL (strategy ~ buy-and-hold in disguise)"

    print(f"\n    Drift=0 verdict: {verdict_zero}")
    print(f"    Drift=real verdict: {verdict_drift}")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, sr_null, label, pval in [
        (axes[0], sr_null_zero, "Drift=0 (Pure Noise)", pvalue_zero),
        (axes[1], sr_null_drift, f"Drift={drift_real:.6f} (Real)", pvalue_drift),
    ]:
        ax.hist(sr_null, bins=40, alpha=0.7, color="steelblue", edgecolor="white",
                label=f"Null (N={len(sr_null)})")
        ax.axvline(sr_real, color="red", lw=2, ls="--", label=f"SR real = {sr_real:.4f}")
        ax.axvline(np.percentile(sr_null, 95), color="orange", lw=1, ls=":",
                   label=f"P95 = {np.percentile(sr_null, 95):.4f}")
        ax.set_title(f"T8: Null Model — {label}\np-value = {pval:.4f}")
        ax.set_xlabel("Sharpe Ratio (per-bar)")
        ax.legend(fontsize=8)

    plt.tight_layout()
    path = os.path.join(PNG_DIR, "h5_t8_random_walk_null.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    Plot: {path}")

    result = {
        "sr_real": sr_real,
        "drift_zero": {"p5": p5_z, "p50": p50_z, "p95": p95_z,
                       "pvalue": pvalue_zero, "verdict": verdict_zero,
                       "distribution": sr_null_zero},
        "drift_real": {"p5": p5_d, "p50": p50_d, "p95": p95_d,
                       "pvalue": pvalue_drift, "verdict": verdict_drift,
                       "distribution": sr_null_drift},
        "n_simulations": n_simulations,
        "sigma": sigma, "drift": drift_real,
        "plot": path,
    }
    return result


# ==========================================================================
# TESTE 9: Sharpe por Trades Independentes
# ==========================================================================
def test_9_independent_trade_sr(bars: pd.DataFrame) -> dict:
    """
    The per-bar SR is inflated because signal has autocorrelation ~0.97.
    Group returns between signal changes to get independent trade returns.
    """
    print("\n" + "=" * 70)
    print("  TESTE 9: Sharpe por Trades Independentes")
    print("=" * 70)

    close_raw = bars["close"].values.astype(np.float64)
    close_sg = savgol_causal(close_raw, SG_WINDOW, SG_POLY)
    signal = pd.Series(close_sg).pct_change(RET_WINDOW).values
    actual_ret = np.diff(close_raw, prepend=close_raw[0]) / np.maximum(close_raw, 1e-12)

    valid = ~np.isnan(signal) & ~np.isnan(actual_ret)
    sig = signal[valid]
    act = actual_ret[valid]

    positions = np.sign(sig[:-1])
    strat_ret = positions * act[1:]

    # Per-bar SR
    sr_bar = np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)

    # Identify trade boundaries (where position changes sign)
    trade_returns = []
    current_trade_ret = []
    current_pos = positions[0]

    for i in range(len(positions)):
        if positions[i] != current_pos and current_pos != 0:
            # Trade ended — compound returns
            compounded = np.prod(1 + np.array(current_trade_ret)) - 1
            trade_returns.append(compounded)
            current_trade_ret = []
            current_pos = positions[i]
        current_trade_ret.append(strat_ret[i])

    # Last trade
    if current_trade_ret:
        compounded = np.prod(1 + np.array(current_trade_ret)) - 1
        trade_returns.append(compounded)

    trade_returns = np.array(trade_returns)
    n_trades = len(trade_returns)

    sr_trade = np.mean(trade_returns) / max(np.std(trade_returns, ddof=1), 1e-12)

    # Estimate bars/year and trades/year for annualization
    timestamps = bars["timestamp"].values
    total_days = (pd.Timestamp(timestamps[-1]) - pd.Timestamp(timestamps[0])).days
    total_years = total_days / 365.25
    bars_per_year = len(bars) / max(total_years, 0.01)
    trades_per_year = n_trades / max(total_years, 0.01)

    sr_bar_annual = sr_bar * np.sqrt(bars_per_year)
    sr_trade_annual = sr_trade * np.sqrt(trades_per_year)

    # Average trade duration in bars
    avg_trade_len = len(positions) / max(n_trades, 1)

    print(f"    Per-bar:  SR={sr_bar:.4f}  annualized={sr_bar_annual:.2f}  "
          f"(N={len(strat_ret)}, {bars_per_year:.0f} bars/yr)")
    print(f"    Per-trade: SR={sr_trade:.4f}  annualized={sr_trade_annual:.2f}  "
          f"(N={n_trades}, {trades_per_year:.0f} trades/yr)")
    print(f"    Avg trade duration: {avg_trade_len:.1f} bars")
    print(f"    Inflation factor: {sr_bar_annual/max(sr_trade_annual, 0.01):.1f}x")

    # Verdict
    if sr_trade_annual > 0.5:
        verdict = "PASS (meaningful edge per trade)"
    elif sr_trade_annual > 0:
        verdict = "MARGINAL (positive but weak edge)"
    else:
        verdict = "FAIL (no edge per independent trade)"
    print(f"    Verdict: {verdict}")

    # Trade return distribution plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(trade_returns, bins=50, alpha=0.7, color="steelblue", edgecolor="white")
    axes[0].axvline(np.mean(trade_returns), color="red", lw=2, ls="--",
                    label=f"Mean={np.mean(trade_returns):.4f}")
    axes[0].set_title(f"T9: Independent Trade Returns\nN={n_trades}, "
                      f"SR_trade_ann={sr_trade_annual:.2f}")
    axes[0].set_xlabel("Compounded Return per Trade")
    axes[0].legend()

    # Comparison bar chart
    labels = ["SR bar\n(per-bar)", "SR bar\n(annualized)", "SR trade\n(per-trade)",
              "SR trade\n(annualized)"]
    values = [sr_bar, sr_bar_annual, sr_trade, sr_trade_annual]
    colors = ["steelblue", "steelblue", "coral", "coral"]
    axes[1].bar(labels, values, color=colors, alpha=0.8, edgecolor="white")
    axes[1].set_title("T9: Per-Bar vs Per-Trade Sharpe")
    axes[1].set_ylabel("Sharpe Ratio")
    for i, v in enumerate(values):
        axes[1].text(i, v + 0.1, f"{v:.2f}", ha="center", fontsize=9)

    plt.tight_layout()
    path = os.path.join(PNG_DIR, "h5_t9_independent_trade_sr.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    Plot: {path}")

    return {
        "sr_bar": sr_bar, "sr_bar_annual": sr_bar_annual,
        "sr_trade": sr_trade, "sr_trade_annual": sr_trade_annual,
        "n_trades": n_trades, "n_bars": len(strat_ret),
        "avg_trade_len": avg_trade_len,
        "trades_per_year": trades_per_year,
        "bars_per_year": bars_per_year,
        "trade_returns": trade_returns,
        "verdict": verdict,
        "plot": path,
    }


# ==========================================================================
# TESTE 10: Bear Market Test
# ==========================================================================
def test_10_bear_market(df_1m: pd.DataFrame) -> dict:
    """
    Split data into bull/bear periods and test strategy in each.
    Uses SMA-60 daily to define regimes.
    """
    print("\n" + "=" * 70)
    print("  TESTE 10: Bear Market Test")
    print("=" * 70)

    # Build daily bars for regime classification
    df = df_1m.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    daily = df.set_index("timestamp").resample("1D").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum"
    }).dropna()
    daily["sma60"] = daily["close"].rolling(60).mean()
    daily["regime"] = np.where(daily["close"] > daily["sma60"], "bull", "bear")

    # Define periods
    periods = []
    current_regime = daily["regime"].iloc[60]
    period_start = daily.index[60]

    for date, row in daily.iloc[61:].iterrows():
        if row["regime"] != current_regime:
            periods.append({
                "start": period_start,
                "end": date,
                "regime": current_regime
            })
            current_regime = row["regime"]
            period_start = date
    # Last period
    periods.append({
        "start": period_start,
        "end": daily.index[-1],
        "regime": current_regime
    })

    # Filter to periods > 30 days
    periods = [p for p in periods if (p["end"] - p["start"]).days > 30]
    print(f"    {len(periods)} periods found (>30 days)")

    results = []
    print(f"\n    {'Period':<28s} {'Regime':<6s} {'Days':>5s} {'N_bars':>7s} "
          f"{'SR_strat':>9s} {'SR_bh':>9s} {'Hit%':>6s} {'MaxDD':>7s}")
    print(f"    {'-'*85}")

    for p in periods:
        # Slice 1-min data for this period
        mask = (df["timestamp"] >= p["start"]) & (df["timestamp"] < p["end"])
        df_slice = df[mask]
        if len(df_slice) < 1440:  # less than 1 day of 1-min data
            continue

        # Build dollar bars for this period
        try:
            builder = DollarBarBuilder(
                calibration_days=DEFAULT_CONFIG["dollar_bar_calibration_days"],
                bars_per_day=DEFAULT_CONFIG["dollar_bars_per_day"],
            )
            bars_p = builder.transform(df_slice)
        except Exception:
            continue

        if len(bars_p) < RET_WINDOW + SG_WINDOW + 5:
            continue

        close_raw = bars_p["close"].values.astype(np.float64)
        close_sg = savgol_causal(close_raw, SG_WINDOW, SG_POLY)
        signal = pd.Series(close_sg).pct_change(RET_WINDOW).values
        actual_ret = np.diff(close_raw, prepend=close_raw[0]) / np.maximum(close_raw, 1e-12)

        valid = ~np.isnan(signal) & ~np.isnan(actual_ret)
        sig = signal[valid]
        act = actual_ret[valid]

        if len(sig) < RET_WINDOW + 2:
            continue

        positions = np.sign(sig[:-1])
        strat_ret = positions * act[1:]

        sr_strat = np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)
        hit = np.mean((strat_ret > 0).astype(float))

        # Buy-and-hold SR
        bh_ret = act[1:]
        sr_bh = np.mean(bh_ret) / max(np.std(bh_ret, ddof=1), 1e-12)

        # Max drawdown
        equity = np.cumprod(1 + strat_ret)
        peak = np.maximum.accumulate(equity)
        dd = (equity - peak) / peak
        max_dd = np.min(dd)

        days = (p["end"] - p["start"]).days
        period_str = f"{p['start'].strftime('%Y-%m')}->{p['end'].strftime('%Y-%m')}"

        results.append({
            "period": period_str,
            "regime": p["regime"],
            "days": days,
            "n_bars": len(strat_ret),
            "sr_strat": sr_strat,
            "sr_bh": sr_bh,
            "hit_rate": hit,
            "max_dd": max_dd,
            "pct_long": np.mean(positions > 0),
        })

        print(f"    {period_str:<28s} {p['regime']:<6s} {days:>5d} {len(strat_ret):>7d} "
              f"{sr_strat:>9.4f} {sr_bh:>9.4f} {hit:>5.1%} {max_dd:>7.1%}")

    # Aggregate by regime
    bulls = [r for r in results if r["regime"] == "bull"]
    bears = [r for r in results if r["regime"] == "bear"]

    sr_bull = np.mean([r["sr_strat"] for r in bulls]) if bulls else np.nan
    sr_bear = np.mean([r["sr_strat"] for r in bears]) if bears else np.nan
    long_pct_bear = np.mean([r["pct_long"] for r in bears]) if bears else np.nan

    print(f"\n    Aggregate: SR_bull={sr_bull:.4f}  SR_bear={sr_bear:.4f}")
    if bears:
        print(f"    Bear market: avg {long_pct_bear:.1%} time long")

    # Verdict
    if np.isnan(sr_bear):
        verdict = "INCONCLUSIVE (no bear periods found)"
    elif sr_bear > 0 and long_pct_bear < 0.7:
        verdict = "PASS (positive SR in bear, not always long)"
    elif sr_bear > 0:
        verdict = "MARGINAL (positive SR in bear, but mostly long)"
    else:
        verdict = "FAIL (negative SR in bear market)"
    print(f"    Verdict: {verdict}")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # SR by period
    period_labels = [r["period"] for r in results]
    srs = [r["sr_strat"] for r in results]
    regimes = [r["regime"] for r in results]
    colors_bar = ["forestgreen" if r == "bull" else "firebrick" for r in regimes]

    axes[0].barh(range(len(srs)), srs, color=colors_bar, alpha=0.8, edgecolor="white")
    axes[0].set_yticks(range(len(srs)))
    axes[0].set_yticklabels(period_labels, fontsize=7)
    axes[0].axvline(0, color="black", lw=0.5)
    axes[0].set_xlabel("Sharpe Ratio (per-bar)")
    axes[0].set_title("T10: SR by Market Regime Period")

    # % long in bear periods
    if bears:
        bear_labels = [r["period"] for r in bears]
        bear_long = [r["pct_long"] for r in bears]
        bear_sr = [r["sr_strat"] for r in bears]
        axes[1].bar(range(len(bears)), bear_long, alpha=0.7, color="firebrick",
                    edgecolor="white", label="% Long")
        ax2 = axes[1].twinx()
        ax2.plot(range(len(bears)), bear_sr, "ko-", label="SR")
        axes[1].set_xticks(range(len(bears)))
        axes[1].set_xticklabels(bear_labels, rotation=45, fontsize=7)
        axes[1].set_ylabel("% Long")
        ax2.set_ylabel("SR")
        axes[1].set_title("T10: Bear Market Periods")
        axes[1].legend(loc="upper left")
        ax2.legend(loc="upper right")
    else:
        axes[1].text(0.5, 0.5, "No bear periods found", ha="center", va="center",
                     transform=axes[1].transAxes)

    plt.tight_layout()
    path = os.path.join(PNG_DIR, "h5_t10_bear_market.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    Plot: {path}")

    return {
        "periods": results,
        "sr_bull": sr_bull, "sr_bear": sr_bear,
        "long_pct_bear": long_pct_bear,
        "n_bull_periods": len(bulls), "n_bear_periods": len(bears),
        "verdict": verdict,
        "plot": path,
    }


# ==========================================================================
# TESTE 11: SavGol-as-Instrument
# ==========================================================================
def test_11_savgol_instrument(df_1m: pd.DataFrame, bars: pd.DataFrame) -> dict:
    """
    Test if SR≈0.18 is a universal property of the operator
    sign(SavGol(pct_change(20))) applied to any series with positive autocorrelation.

    Applies pipeline to 5 synthetic series:
      (A) BTC real (baseline)
      (B) BTC returns shuffled (destroys temporal structure, keeps distribution)
      (C) Random walk, vol=BTC, drift=0
      (D) Random walk, vol=BTC, drift=BTC
      (E) AR(1) calibrated to BTC return autocorrelation, drift=0
    """
    print("\n" + "=" * 70)
    print("  TESTE 11: SavGol-as-Instrument")
    print("=" * 70)

    close_raw = bars["close"].values.astype(np.float64)
    bar_returns = bars["close"].pct_change().dropna().values
    sigma = np.std(bar_returns)
    mu = np.mean(bar_returns)
    ac1_ret = np.corrcoef(bar_returns[:-1], bar_returns[1:])[0, 1]
    n = len(close_raw)

    print(f"    BTC calibration: sigma={sigma:.6f}, mu={mu:.6f}, AC1_ret={ac1_ret:.4f}")

    def _compute_sr(prices):
        """Apply full pipeline to a price series and return SR."""
        sg = savgol_causal(prices, SG_WINDOW, SG_POLY)
        sig = pd.Series(sg).pct_change(RET_WINDOW).values
        act = np.diff(prices, prepend=prices[0]) / np.maximum(prices, 1e-12)
        v = ~np.isnan(sig) & ~np.isnan(act)
        s = sig[v]
        a = act[v]
        if len(s) < RET_WINDOW + 2:
            return np.nan
        pos = np.sign(s[:-1])
        sr = pos * a[1:]
        return np.mean(sr) / max(np.std(sr, ddof=1), 1e-12)

    # (A) BTC Real
    sr_real = _compute_sr(close_raw)
    print(f"    (A) BTC Real:             SR = {sr_real:.4f}")

    # (B) Shuffled returns
    rng = np.random.RandomState(42)
    shuffled_rets = bar_returns.copy()
    rng.shuffle(shuffled_rets)
    prices_shuffled = np.cumprod(np.concatenate([[close_raw[0]], 1 + shuffled_rets]))
    sr_shuffled = _compute_sr(prices_shuffled)
    print(f"    (B) Returns Shuffled:     SR = {sr_shuffled:.4f}")

    # (C) Random Walk drift=0
    n_mc = 100
    sr_rw_zero = []
    for i in range(n_mc):
        r = sigma * np.random.RandomState(i).randn(n - 1)
        p = np.cumprod(np.concatenate([[100.0], 1 + r]))
        sr_rw_zero.append(_compute_sr(p))
    sr_rw_zero = np.array(sr_rw_zero)
    sr_rw_zero_mean = np.nanmean(sr_rw_zero)
    print(f"    (C) RW drift=0:           SR = {sr_rw_zero_mean:.4f} "
          f"(std={np.nanstd(sr_rw_zero):.4f})")

    # (D) Random Walk drift=real
    sr_rw_drift = []
    for i in range(n_mc):
        r = mu + sigma * np.random.RandomState(i + 5000).randn(n - 1)
        p = np.cumprod(np.concatenate([[100.0], 1 + r]))
        sr_rw_drift.append(_compute_sr(p))
    sr_rw_drift = np.array(sr_rw_drift)
    sr_rw_drift_mean = np.nanmean(sr_rw_drift)
    print(f"    (D) RW drift=real:        SR = {sr_rw_drift_mean:.4f} "
          f"(std={np.nanstd(sr_rw_drift):.4f})")

    # (E) AR(1) calibrated to BTC return autocorrelation, drift=0
    sr_ar1 = []
    for i in range(n_mc):
        rng_i = np.random.RandomState(i + 9000)
        ar_rets = np.zeros(n - 1)
        ar_rets[0] = sigma * rng_i.randn()
        for j in range(1, len(ar_rets)):
            ar_rets[j] = ac1_ret * ar_rets[j - 1] + sigma * np.sqrt(1 - ac1_ret**2) * rng_i.randn()
        p = np.cumprod(np.concatenate([[100.0], 1 + ar_rets]))
        sr_ar1.append(_compute_sr(p))
    sr_ar1 = np.array(sr_ar1)
    sr_ar1_mean = np.nanmean(sr_ar1)
    print(f"    (E) AR(1) drift=0:        SR = {sr_ar1_mean:.4f} "
          f"(std={np.nanstd(sr_ar1):.4f})")

    # Interpretation
    print(f"\n    Interpretation:")
    if abs(sr_real - sr_rw_drift_mean) < 0.02:
        interp = "Strategy ~ buy-and-hold (drift explains SR)"
    elif abs(sr_real - sr_ar1_mean) < 0.02:
        interp = "Filter exploits return autocorrelation, not regime structure"
    elif sr_real > sr_rw_drift_mean + 0.03 and sr_real > sr_ar1_mean + 0.03:
        interp = "Genuine alpha beyond drift and autocorrelation"
    else:
        interp = "Mixed — partial artifact, partial signal"
    print(f"    {interp}")

    # Verdict
    if sr_real > sr_rw_drift_mean + 0.03 and sr_real > sr_ar1_mean + 0.03:
        verdict = "PASS (genuine alpha)"
    elif sr_real > sr_rw_drift_mean + 0.01:
        verdict = "MARGINAL (some alpha but mostly drift/autocorrelation)"
    else:
        verdict = "FAIL (SR explained by drift or autocorrelation)"
    print(f"    Verdict: {verdict}")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))

    labels = ["(A) BTC\nReal", "(B) Returns\nShuffled",
              "(C) RW\ndrift=0", "(D) RW\ndrift=real", "(E) AR(1)\ndrift=0"]
    means = [sr_real, sr_shuffled, sr_rw_zero_mean, sr_rw_drift_mean, sr_ar1_mean]
    stds = [0, 0, np.nanstd(sr_rw_zero), np.nanstd(sr_rw_drift), np.nanstd(sr_ar1)]
    colors_plot = ["firebrick", "gray", "steelblue", "steelblue", "goldenrod"]

    bars_plt = ax.bar(labels, means, yerr=stds, color=colors_plot, alpha=0.8,
                      edgecolor="white", capsize=5)
    ax.axhline(sr_real, color="firebrick", lw=1, ls=":", alpha=0.5)
    ax.set_ylabel("Sharpe Ratio (per-bar)")
    ax.set_title(f"T11: SavGol-as-Instrument\n{interp}")

    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 0.005, f"{m:.4f}", ha="center", fontsize=9)

    plt.tight_layout()
    path = os.path.join(PNG_DIR, "h5_t11_savgol_instrument.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    Plot: {path}")

    return {
        "sr_real": sr_real, "sr_shuffled": sr_shuffled,
        "sr_rw_zero": sr_rw_zero_mean, "sr_rw_zero_std": np.nanstd(sr_rw_zero),
        "sr_rw_drift": sr_rw_drift_mean, "sr_rw_drift_std": np.nanstd(sr_rw_drift),
        "sr_ar1": sr_ar1_mean, "sr_ar1_std": np.nanstd(sr_ar1),
        "interpretation": interp,
        "verdict": verdict,
        "plot": path,
    }


# ==========================================================================
# TESTE 12: Per-Feature T8 (Null Model for Each Feature)
# ==========================================================================
def test_12_feature_null_model(df_1m: pd.DataFrame, bars: pd.DataFrame,
                               n_simulations: int = 100) -> dict:
    """
    Run T8-style null model on individual features to identify which
    have genuine predictive power vs which are pipeline artifacts.

    For each feature, compute the feature on real data and on N random
    walk paths, then use sign(feature) as the strategy signal.
    """
    from utils.savgol import savgol_causal, savgol_causal_deriv

    print("\n" + "=" * 70)
    print("  TESTE 12: Per-Feature Null Model")
    print("=" * 70)

    close_raw = bars["close"].values.astype(np.float64)
    bar_returns = bars["close"].pct_change().dropna().values
    sigma = np.std(bar_returns)
    n_bars = len(close_raw)

    actual_ret = np.diff(close_raw, prepend=close_raw[0]) / np.maximum(close_raw, 1e-12)

    # --- Define feature extractors ---
    def _feat_sg_velocity(prices):
        vel = savgol_causal_deriv(prices, SG_WINDOW, SG_POLY, deriv=1)
        price_safe = np.where(prices > 1e-12, prices, np.nan)
        vel_norm = vel / price_safe
        sg = savgol_causal(prices, SG_WINDOW, SG_POLY)
        ret = pd.Series(sg).pct_change().values
        vol = pd.Series(ret).rolling(20, min_periods=20).std().values
        vol_safe = np.where(vol > 1e-12, vol, np.nan)
        return vel_norm / vol_safe

    def _feat_sg_acceleration(prices):
        acc = savgol_causal_deriv(prices, SG_WINDOW, SG_POLY, deriv=2)
        price_safe = np.where(prices > 1e-12, prices, np.nan)
        return acc / price_safe

    def _feat_sg_curvature(prices):
        vel = savgol_causal_deriv(prices, SG_WINDOW, SG_POLY, deriv=1)
        acc = savgol_causal_deriv(prices, SG_WINDOW, SG_POLY, deriv=2)
        price_safe = np.where(prices > 1e-12, prices, np.nan)
        v = vel / price_safe
        a = acc / price_safe
        return a / np.power(1 + v**2, 1.5)

    def _feat_ret20_savgol(prices):
        sg = savgol_causal(prices, SG_WINDOW, SG_POLY)
        return pd.Series(sg).pct_change(RET_WINDOW).values

    def _feat_ffd(prices):
        """Fractional differentiation (d=0.4)."""
        d = 0.4
        threshold = 1e-4
        weights = [1.0]
        k = 1
        while True:
            w = -weights[-1] * (d - k + 1) / k
            if abs(w) < threshold:
                break
            weights.append(w)
            k += 1
        weights = np.array(weights[::-1])
        result = np.convolve(prices, weights, mode="full")[:len(prices)]
        result[:len(weights) - 1] = np.nan
        return result

    def _compute_feature_sr(feature_values, returns):
        """Compute SR of sign(feature) strategy."""
        valid = ~np.isnan(feature_values) & ~np.isnan(returns)
        f = feature_values[valid]
        r = returns[valid]
        if len(f) < 50:
            return np.nan
        pos = np.sign(f[:-1])
        sr = pos * r[1:]
        return np.mean(sr) / max(np.std(sr, ddof=1), 1e-12)

    features = {
        "sg_velocity": _feat_sg_velocity,
        "sg_acceleration": _feat_sg_acceleration,
        "sg_curvature": _feat_sg_curvature,
        "ret20_savgol (old)": _feat_ret20_savgol,
        "ffd_0.4": _feat_ffd,
    }

    # --- VPIN and Kyle Lambda need volume, which random walks don't have ---
    # For these we test differently: shuffle the returns but keep volume structure
    volume_raw = bars["volume"].values.astype(np.float64) if "volume" in bars.columns else None

    def _vpin_feature(close_arr, volume_arr):
        """Simplified VPIN calculation."""
        n = len(close_arr)
        ret = np.diff(close_arr, prepend=close_arr[0]) / np.maximum(close_arr, 1e-12)
        # Buy volume estimation via bulk classification
        buy_vol = np.where(ret > 0, volume_arr, 0)
        sell_vol = np.where(ret <= 0, volume_arr, 0)
        total_vol = volume_arr
        # VPIN over rolling 50-bar window
        n_buckets = 50
        vpin = np.full(n, np.nan)
        for i in range(n_buckets, n):
            bv = buy_vol[i-n_buckets:i]
            sv = sell_vol[i-n_buckets:i]
            tv = total_vol[i-n_buckets:i]
            tv_sum = np.sum(tv)
            if tv_sum > 0:
                vpin[i] = np.sum(np.abs(bv - sv)) / tv_sum
        return vpin

    def _kyle_lambda_feature(close_arr, volume_arr):
        """Simplified Kyle Lambda."""
        n = len(close_arr)
        ret = np.diff(close_arr, prepend=close_arr[0])
        signed_vol = np.sign(ret) * volume_arr
        kyle = np.full(n, np.nan)
        w = 20
        for i in range(w, n):
            y = ret[i-w:i]
            x = signed_vol[i-w:i]
            x_c = x - np.mean(x)
            var_x = np.var(x)
            if var_x > 1e-20:
                kyle[i] = np.cov(y - np.mean(y), x_c)[0, 1] / var_x
        return kyle

    # Compute SR on real data for all features
    results = {}

    print(f"\n    {'Feature':<25s} {'SR_real':>8s} {'SR_null':>8s} {'SR_null_std':>11s} "
          f"{'p-value':>8s} {'Verdict':>10s}")
    print(f"    {'-'*78}")

    for feat_name, feat_fn in features.items():
        # Real SR
        feat_real = feat_fn(close_raw)
        sr_real = _compute_feature_sr(feat_real, actual_ret)

        # Null: random walks
        sr_nulls = []
        for i in range(n_simulations):
            rng = np.random.RandomState(i)
            r_syn = sigma * rng.randn(n_bars - 1)
            p_syn = np.cumprod(np.concatenate([[100.0], 1 + r_syn]))
            act_syn = np.diff(p_syn, prepend=p_syn[0]) / np.maximum(p_syn, 1e-12)
            feat_syn = feat_fn(p_syn)
            sr_nulls.append(_compute_feature_sr(feat_syn, act_syn))

        sr_nulls = np.array(sr_nulls)
        sr_nulls = sr_nulls[~np.isnan(sr_nulls)]
        sr_null_mean = np.mean(sr_nulls)
        sr_null_std = np.std(sr_nulls)
        pvalue = np.mean(sr_nulls >= sr_real) if len(sr_nulls) > 0 else 1.0

        verdict = "GENUINE" if pvalue < 0.05 else "ARTIFACT"
        results[feat_name] = {
            "sr_real": sr_real, "sr_null_mean": sr_null_mean,
            "sr_null_std": sr_null_std, "pvalue": pvalue, "verdict": verdict,
        }
        print(f"    {feat_name:<25s} {sr_real:>8.4f} {sr_null_mean:>8.4f} "
              f"{sr_null_std:>11.4f} {pvalue:>8.4f} {verdict:>10s}")

    # VPIN and Kyle Lambda: test with shuffled returns (preserves volume structure)
    if volume_raw is not None:
        for feat_name, feat_fn in [("vpin", _vpin_feature), ("kyle_lambda", _kyle_lambda_feature)]:
            feat_real = feat_fn(close_raw, volume_raw)
            sr_real = _compute_feature_sr(feat_real, actual_ret)

            sr_nulls = []
            for i in range(n_simulations):
                rng = np.random.RandomState(i + 20000)
                shuffled = bar_returns.copy()
                rng.shuffle(shuffled)
                p_syn = np.cumprod(np.concatenate([[close_raw[0]], 1 + shuffled]))
                act_syn = np.diff(p_syn, prepend=p_syn[0]) / np.maximum(p_syn, 1e-12)
                feat_syn = feat_fn(p_syn, volume_raw)
                sr_nulls.append(_compute_feature_sr(feat_syn, act_syn))

            sr_nulls = np.array(sr_nulls)
            sr_nulls = sr_nulls[~np.isnan(sr_nulls)]
            sr_null_mean = np.mean(sr_nulls)
            sr_null_std = np.std(sr_nulls)
            pvalue = np.mean(sr_nulls >= sr_real) if len(sr_nulls) > 0 else 1.0

            verdict = "GENUINE" if pvalue < 0.05 else "ARTIFACT"
            results[feat_name] = {
                "sr_real": sr_real, "sr_null_mean": sr_null_mean,
                "sr_null_std": sr_null_std, "pvalue": pvalue, "verdict": verdict,
            }
            print(f"    {feat_name:<25s} {sr_real:>8.4f} {sr_null_mean:>8.4f} "
                  f"{sr_null_std:>11.4f} {pvalue:>8.4f} {verdict:>10s}")

    # Summary
    genuine = [k for k, v in results.items() if v["verdict"] == "GENUINE"]
    artifacts = [k for k, v in results.items() if v["verdict"] == "ARTIFACT"]
    print(f"\n    Genuine features ({len(genuine)}): {', '.join(genuine) if genuine else 'none'}")
    print(f"    Artifact features ({len(artifacts)}): {', '.join(artifacts) if artifacts else 'none'}")

    # Plot
    feat_names = list(results.keys())
    sr_reals = [results[k]["sr_real"] for k in feat_names]
    sr_nulls_m = [results[k]["sr_null_mean"] for k in feat_names]
    sr_nulls_s = [results[k]["sr_null_std"] for k in feat_names]
    verdicts = [results[k]["verdict"] for k in feat_names]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(feat_names))
    width = 0.35

    colors_real = ["forestgreen" if v == "GENUINE" else "firebrick" for v in verdicts]
    ax.bar(x - width/2, sr_reals, width, color=colors_real, alpha=0.8, label="SR Real")
    ax.bar(x + width/2, sr_nulls_m, width, yerr=sr_nulls_s, color="steelblue",
           alpha=0.6, label="SR Null (mean +/- std)", capsize=3)

    ax.set_xticks(x)
    ax.set_xticklabels(feat_names, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Sharpe Ratio (per-bar)")
    ax.set_title("T12: Per-Feature Null Model\nGreen = genuine, Red = artifact")
    ax.legend()
    ax.axhline(0, color="black", lw=0.5)

    plt.tight_layout()
    path = os.path.join(PNG_DIR, "h5_t12_feature_null_model.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    Plot: {path}")

    return {"features": results, "genuine": genuine, "artifacts": artifacts, "plot": path}


# ==========================================================================
# RELATÓRIO
# ==========================================================================
def generate_report(t1, t2, t3, t4, t5, t6, t7=None,
                    t8=None, t9=None, t10=None, t11=None, t12=None,
                    candle_btc=None, candle_sp=None,
                    window_expl=None) -> str:
    """Gera relatório Markdown com resultados de todos os testes."""

    # Veredito geral
    evidence_for = 0
    evidence_against = 0

    if t1["cv"] > 0.30:
        evidence_for += 1
    elif t1["cv"] > 0.10:
        evidence_for += 0.5
    else:
        evidence_against += 1

    if t2["spearman_rho"] < -0.5 and t2["p_value"] < 0.01:
        evidence_for += 1
    elif t2["spearman_rho"] < -0.3 and t2["p_value"] < 0.05:
        evidence_for += 0.5
    else:
        evidence_against += 1

    if t3["ac_high_vol"] > 0 and t3["ac_low_vol"] > 0:
        evidence_for += 1
    else:
        evidence_against += 0.5

    if t4["sr_ratio"] > 1.2:
        evidence_for += 1
    elif t4["sr_ratio"] > 0.8:
        evidence_for += 0.5
    else:
        evidence_against += 1

    all_q_positive = all(v["sharpe"] > 0 for v in t5.values())
    if all_q_positive:
        evidence_for += 1
    else:
        evidence_against += 1

    total = evidence_for + evidence_against
    score = evidence_for / total if total > 0 else 0

    if score >= 0.7:
        verdict = "SUPORTADA"
    elif score >= 0.4:
        verdict = "PARCIALMENTE SUPORTADA"
    else:
        verdict = "REFUTADA"

    report = f"""# Hipótese 5: Momentum Adaptativo via Dollar Bars

**Data:** 2026-03-25
**Hipótese:** ret_20 em dollar bars adapta automaticamente o horizonte temporal
ao regime de volatilidade/volume, funcionando como momentum de curto prazo em
crises e momentum de médio prazo em mercados calmos.

**Veredito: {verdict}** (evidência: {evidence_for:.1f}/{total:.1f} = {score:.0%})

---

## T1: Distribuição do Horizonte Temporal

Se ret_20 fosse equivalente a "retorno de 1 dia", o horizonte seria ~24h com
variância mínima. A variabilidade do horizonte mede o grau de adaptação.

| Métrica | Valor |
|---------|-------|
| Média | {t1['mean_hours']:.1f}h ({t1['mean_hours']/24:.1f} dias) |
| Mediana | {t1['median_hours']:.1f}h ({t1['median_hours']/24:.1f} dias) |
| Desvio Padrão | {t1['std_hours']:.1f}h |
| Mínimo | {t1['min_hours']:.1f}h |
| Máximo | {t1['max_hours']:.1f}h |
| P10 — P90 | {t1['p10_hours']:.1f}h — {t1['p90_hours']:.1f}h |
| **Coef. Variação** | **{t1['cv']:.3f}** |

Interpretação: CV = {t1['cv']:.3f}. {"Horizonte altamente variável — ret_20 NÃO é 1 dia fixo." if t1['cv'] > 0.3 else "Horizonte com variação moderada." if t1['cv'] > 0.1 else "Horizonte quase fixo — pouca adaptação."}

![Distribuição do Horizonte](relatorios/pngs/h5_t1_horizon_distribution.png)

---

## T2: Correlação Bars/Dia vs Horizonte

Se mais volume → mais barras/dia → 20 barras cobrem menos horas → horizonte
menor. A correlação esperada é **negativa**.

| Métrica | Valor |
|---------|-------|
| Spearman ρ | {t2['spearman_rho']:.4f} |
| p-value | {t2['p_value']:.2e} |
| N dias | {t2['n_days']} |

{"Correlação negativa forte e significativa." if t2['spearman_rho'] < -0.5 and t2['p_value'] < 0.01 else "Correlação negativa moderada." if t2['spearman_rho'] < -0.3 and t2['p_value'] < 0.05 else "Correlação fraca ou não significativa."}

![Bars vs Horizonte](relatorios/pngs/h5_t2_bars_vs_horizon.png)

---

## T3: Autocorrelação Condicional por Regime de Volume

Se ret_20 adaptativo funciona: deveria ter autocorrelação positiva (momentum
existe) tanto em alto quanto em baixo volume.

| Regime | Autocorrelação lag-1 | p-value | N |
|--------|---------------------|---------|---|
| Global | {t3['ac_all']:.4f} | {t3['p_all']:.2e} | {t3['n_high']+t3['n_low']} |
| Alto Volume | {t3['ac_high_vol']:.4f} | {t3['p_high_vol']:.2e} | {t3['n_high']} |
| Baixo Volume | {t3['ac_low_vol']:.4f} | {t3['p_low_vol']:.2e} | {t3['n_low']} |

![Autocorrelação Condicional](relatorios/pngs/h5_t3_conditional_autocorrelation.png)

---

## T4: Dollar Bars ret_20 vs Time Bars ret_1d

Comparação direta: o momentum adaptativo (dollar bars) supera o fixo (time bars)?

| Métrica | ret_20 Dollar Bars | ret_1d Time Bars |
|---------|--------------------|------------------|
| N | {t4['dollar_bars']['n']} | {t4['time_bars']['n']} |
| Sharpe | {t4['dollar_bars']['sharpe']:.4f} | {t4['time_bars']['sharpe']:.4f} |
| Hit Rate | {t4['dollar_bars']['hit_rate']:.4f} | {t4['time_bars']['hit_rate']:.4f} |
| Autocorr(1) | {t4['dollar_bars']['autocorr_1']:.4f} | {t4['time_bars']['autocorr_1']:.4f} |
| IC (signal→return) | {t4['dollar_bars']['information_coeff']:.4f} | {t4['time_bars']['information_coeff']:.4f} |

**Razão Sharpe (dollar/time): {t4['sr_ratio']:.2f}x**

![Dollar vs Time Bars](relatorios/pngs/h5_t4_dollar_vs_time_bars.png)

---

## T5: Sharpe por Quintil de Volume

Se ret_20 adapta-se ao regime, deveria gerar Sharpe positivo em TODOS os
quintis de volume — não apenas nos "fáceis".

| Quintil | N bars | Sharpe | Hit% | Volume Med ($B) | Horizonte Med (h) |
|---------|--------|--------|------|-----------------|-------------------|"""

    for q in sorted(t5.keys()):
        v = t5[q]
        report += (
            f"\n| Q{q} ({'baixo' if q <= 2 else 'médio' if q == 3 else 'alto'} vol) "
            f"| {v['n']} | {v['sharpe']:.4f} | {v['hit_rate']:.1%} "
            f"| {v['volume_median_B']:.1f} | {v['horizon_median_h']:.1f} |"
        )

    all_pos = all(v["sharpe"] > 0 for v in t5.values())
    report += f"""

{"Sharpe positivo em **todos** os quintis." if all_pos else "Sharpe negativo em pelo menos um quintil."}

![Sharpe por Regime](relatorios/pngs/h5_t5_sharpe_by_volume_regime.png)

---

## T6: Ablacao do Filtro — SavGol vs Raw vs MA(21)

Questao ortogonal a H5: dado que dollar bars criam horizonte adaptativo,
qual filtro extrai melhor o sinal de momentum? Janela de suavizacao = 21 para
SavGol e MA (comparacao justa). Retorno = pct_change(20) em todos os casos.

| Filtro | Sharpe | Hit Rate | IC (signal->return) | Lag otimo |
|--------|--------|----------|--------------------|-----------|
| raw | {t6['raw']['sharpe']:.4f} | {t6['raw']['hit_rate']:.4f} | {t6['raw']['information_coeff']:.4f} | {t6['raw']['best_lag']} |
| savgol | {t6['savgol']['sharpe']:.4f} | {t6['savgol']['hit_rate']:.4f} | {t6['savgol']['information_coeff']:.4f} | {t6['savgol']['best_lag']} |
| ma_21 | {t6['ma_21']['sharpe']:.4f} | {t6['ma_21']['hit_rate']:.4f} | {t6['ma_21']['information_coeff']:.4f} | {t6['ma_21']['best_lag']} |

**Melhor: {max(t6, key=lambda k: t6[k]['sharpe'])}** | Razao SavGol/Raw: {t6['savgol']['sharpe']/max(abs(t6['raw']['sharpe']),1e-12):.2f}x | SavGol/MA: {t6['savgol']['sharpe']/max(abs(t6['ma_21']['sharpe']),1e-12):.2f}x

![Ablacao do Filtro](relatorios/pngs/h5_t6_filter_ablation.png)

---
"""

    # --- Candlestick + SavGol section ---
    if candle_btc or candle_sp:
        report += """
## Visualizacao: Filtro SavGol Causal sobre Candlestick

O filtro Savitzky-Golay causal (window={w}, polyorder={p}, pos=window-1) e aplicado
sem look-ahead: cada ponto usa apenas dados passados. Abaixo, comparamos o comportamento
do filtro sobre barras temporais (1 dia) vs dollar bars para os mesmos ativos.
A diferenca visual ilustra como dollar bars comprimem periodos de alto volume
(mais barras = mais resolucao) e expandem periodos calmos.

""".format(w=SG_WINDOW, p=SG_POLY)

        if candle_btc:
            report += f"### BTC/USDT\n\n![BTC Candlestick + SavGol](pngs/{candle_btc})\n\n"
        if window_expl:
            report += (
                "#### Como o SavGol causal calcula um ponto\n\n"
                "O grafico abaixo mostra a janela de 21 dollar bars (area azul) "
                "usada para calcular um unico ponto do filtro (X vermelho). "
                "O filtro causal (pos=window-1) usa APENAS barras anteriores — "
                "sem look-ahead.\n\n"
                f"![Janela SavGol Explicacao](pngs/{window_expl})\n\n"
            )
        if candle_sp:
            report += f"### S&P500 ETF (SPY)\n\n![SP500 Candlestick + SavGol](pngs/{candle_sp})\n\n"

        report += "---\n"

    # --- T7 Cross-Market section ---
    if t7 and len(t7) > 0:
        valid_t7 = {k: v for k, v in t7.items() if not v.get("skip")}
        report += """
## T7: Validacao Cross-Market — S&P500, IBOVESPA, BTC

O fenomeno de momentum adaptativo via dollar bars e universal ou especifico
de criptomoedas? Testamos o mesmo pipeline (dollar bars + SavGol causal +
ret_20) em S&P500 (SPY ETF 1-min) e IBOVESPA (BOVA11 ETF 1-min).

| Mercado | N Dollar Bars | CV Horizonte | rho(bars,horiz) | SR SavGol | SR Raw | SR MA | SR Time 1D | Ratio D/T |
|---------|--------------|-------------|----------------|-----------|--------|-------|------------|-----------|
"""
        for key, r in valid_t7.items():
            report += (
                f"| {r['label']} | {r['n_dollar_bars']} | {r['horizon_cv']:.3f} "
                f"| {r['rho_bars_horizon']:.3f} | {r['sr_savgol']:.4f} "
                f"| {r['sr_raw']:.4f} | {r['sr_ma']:.4f} "
                f"| {r['sr_time_1d']:.4f} | {r['sr_ratio_dollar_time']:.1f}x |\n"
            )

        # Interpretação automática
        n_cv_high = sum(1 for v in valid_t7.values() if v["horizon_cv"] > 0.3)
        n_sg_best = sum(1 for v in valid_t7.values() if v["sr_savgol"] > v["sr_raw"] and v["sr_savgol"] > v["sr_ma"])
        n_dollar_wins = sum(1 for v in valid_t7.values() if v["sr_ratio_dollar_time"] > 1.0)
        n_total = len(valid_t7)

        report += f"""
**Resultados cross-market:**
- CV do horizonte > 0.3 (adaptacao significativa): {n_cv_high}/{n_total} mercados
- SavGol como melhor filtro: {n_sg_best}/{n_total} mercados
- Dollar bars superam time bars (ratio > 1x): {n_dollar_wins}/{n_total} mercados

"""
        if n_cv_high == n_total and n_dollar_wins >= n_total - 1:
            report += "**Conclusao T7: Fenomeno UNIVERSAL.** O momentum adaptativo via dollar bars nao e especifico de BTC — ocorre em mercados com estruturas de microestrutura muito diferentes (cripto 24/7, equity US, equity BR).\n"
        elif n_cv_high >= n_total * 0.5:
            report += "**Conclusao T7: Fenomeno PARCIALMENTE UNIVERSAL.** O mecanismo de adaptacao do horizonte ocorre em multiplos mercados, mas a magnitude varia significativamente.\n"
        else:
            report += "**Conclusao T7: Fenomeno ESPECIFICO de BTC.** Os mercados tradicionais nao apresentam a mesma adaptacao de horizonte via dollar bars.\n"

        report += "\n![Cross-Market](relatorios/pngs/h5_t7_cross_market.png)\n\n---\n"

    # T8-T11 sections
    if t8 is not None:
        dz = t8["drift_zero"]
        dr = t8["drift_real"]
        report += f"""
---

## T8: Random Walk Null Model (GATE TEST)

**H0**: SR=0.18 surge do pipeline (SavGol+pct_change+sign) aplicado a qualquer
serie com volatilidade similar, mesmo sem estrutura preditiva.

| Cenario | P5 | P50 | P95 | p-value | Veredito |
|---------|-----|------|------|---------|----------|
| Drift=0 (ruido puro) | {dz['p5']:.4f} | {dz['p50']:.4f} | {dz['p95']:.4f} | {dz['pvalue']:.4f} | {dz['verdict']} |
| Drift=real ({t8['drift']:.6f}) | {dr['p5']:.4f} | {dr['p50']:.4f} | {dr['p95']:.4f} | {dr['pvalue']:.4f} | {dr['verdict']} |

**SR real: {t8['sr_real']:.4f}** | N simulacoes: {t8['n_simulations']}

![Random Walk Null](relatorios/pngs/h5_t8_random_walk_null.png)
"""

    if t9 is not None:
        report += f"""
---

## T9: Sharpe por Trades Independentes

O SR per-bar e inflado pela autocorrelacao do sinal (~0.97). Agrupando retornos
entre mudancas de sinal, obtemos trades independentes.

| Metrica | Per-Bar | Per-Trade |
|---------|---------|-----------|
| SR (raw) | {t9['sr_bar']:.4f} | {t9['sr_trade']:.4f} |
| SR (anualizado) | {t9['sr_bar_annual']:.2f} | {t9['sr_trade_annual']:.2f} |
| N | {t9['n_bars']} | {t9['n_trades']} |

- Duracao media por trade: {t9['avg_trade_len']:.1f} bars
- Trades/ano: {t9['trades_per_year']:.0f}
- **Fator de inflacao: {t9['sr_bar_annual']/max(t9['sr_trade_annual'], 0.01):.1f}x**

**Veredito: {t9['verdict']}**

![Independent Trade SR](relatorios/pngs/h5_t9_independent_trade_sr.png)
"""

    if t10 is not None:
        report += f"""
---

## T10: Bear Market Test

Dados separados em periodos bull/bear via SMA-60 diario.

| Periodo | Regime | Dias | N bars | SR strat | SR B&H | Hit% | MaxDD |
|---------|--------|------|--------|----------|--------|------|-------|
"""
        for p in t10["periods"]:
            report += (f"| {p['period']} | {p['regime']} | {p['days']} | "
                      f"{p['n_bars']} | {p['sr_strat']:.4f} | {p['sr_bh']:.4f} | "
                      f"{p['hit_rate']:.1%} | {p['max_dd']:.1%} |\n")
        report += f"""
**Agregado:** SR_bull={t10['sr_bull']:.4f} | SR_bear={t10['sr_bear']:.4f}
"""
        if t10["n_bear_periods"] > 0:
            report += f"Bear market: {t10['long_pct_bear']:.1%} do tempo long\n"
        report += f"""
**Veredito: {t10['verdict']}**

![Bear Market](relatorios/pngs/h5_t10_bear_market.png)
"""

    if t11 is not None:
        report += f"""
---

## T11: SavGol-as-Instrument

Pipeline aplicado a 5 tipos de serie para isolar a origem do SR.

| Serie | SR | Std |
|-------|----|-----|
| (A) BTC Real | {t11['sr_real']:.4f} | — |
| (B) Returns Shuffled | {t11['sr_shuffled']:.4f} | — |
| (C) RW drift=0 | {t11['sr_rw_zero']:.4f} | {t11['sr_rw_zero_std']:.4f} |
| (D) RW drift=real | {t11['sr_rw_drift']:.4f} | {t11['sr_rw_drift_std']:.4f} |
| (E) AR(1) drift=0 | {t11['sr_ar1']:.4f} | {t11['sr_ar1_std']:.4f} |

**Interpretacao:** {t11['interpretation']}

**Veredito: {t11['verdict']}**

![SavGol Instrument](relatorios/pngs/h5_t11_savgol_instrument.png)
"""

    if t12 is not None:
        report += f"""
---

## T12: Per-Feature Null Model

Cada feature testada individualmente contra random walks para separar
poder preditivo genuino de artefatos do pipeline.

| Feature | SR Real | SR Null (mean) | SR Null (std) | p-value | Veredito |
|---------|---------|----------------|---------------|---------|----------|
"""
        for fname, fdata in t12["features"].items():
            report += (f"| {fname} | {fdata['sr_real']:.4f} | {fdata['sr_null_mean']:.4f} | "
                      f"{fdata['sr_null_std']:.4f} | {fdata['pvalue']:.4f} | {fdata['verdict']} |\n")
        report += f"""
**Features genuinas:** {', '.join(t12['genuine']) if t12['genuine'] else 'nenhuma'}
**Artefatos:** {', '.join(t12['artifacts']) if t12['artifacts'] else 'nenhum'}

![Per-Feature Null Model](relatorios/pngs/h5_t12_feature_null_model.png)
"""

    # Conclusão
    t1_verdict = "SIM" if t1['cv'] > 0.3 else "PARCIAL" if t1['cv'] > 0.1 else "NAO"
    t2_verdict = "SIM" if t2['spearman_rho'] < -0.5 and t2['p_value'] < 0.01 else "PARCIAL" if t2['spearman_rho'] < -0.3 else "NAO"
    t3_verdict = "SIM" if t3['ac_high_vol'] > 0 and t3['ac_low_vol'] > 0 else "NAO"
    t4_verdict = "SIM" if t4['sr_ratio'] > 1.2 else "PARCIAL" if t4['sr_ratio'] > 0.8 else "NAO"
    t5_verdict = "SIM" if all_pos else "NAO"
    t5_label = "Sim" if all_pos else "Nao"
    best_filter = max(t6, key=lambda k: t6[k]['sharpe'])
    best_filter_sr = t6[best_filter]['sharpe']

    conclusion_text = ""
    if verdict == "SUPORTADA":
        conclusion_text = (
            "Se confirmada, a contribuicao central do pipeline nao e o Random Forest "
            "nem as features de microestrutura — e a **amostragem por dollar volume**, "
            "que transforma momentum de horizonte fixo em momentum adaptativo ao regime. "
            "Isso e derivavel da teoria (AFML Teorema 2.1) e tem implicacoes para "
            "qualquer estrategia de momentum em qualquer ativo."
        )

    report += f"""
## Conclusao

| Teste | Resultado | Suporte a Hipotese |
|-------|-----------|-------------------|
| T1: CV do horizonte | {t1['cv']:.3f} | {t1_verdict} |
| T2: rho(bars/dia, horizonte) | {t2['spearman_rho']:.3f} (p={t2['p_value']:.1e}) | {t2_verdict} |
| T3: AC condicional | high={t3['ac_high_vol']:.4f}, low={t3['ac_low_vol']:.4f} | {t3_verdict} |
| T4: SR ratio dollar/time | {t4['sr_ratio']:.2f}x | {t4_verdict} |
| T5: SR todos quintis > 0 | {t5_label} | {t5_verdict} |
| T6: Melhor filtro | {best_filter} (SR={best_filter_sr:.4f}) | Ablacao |
"""

    # Add T8-T11 to conclusion table
    if t8 is not None:
        t8_verdict = "SIM" if t8["drift_zero"]["pvalue"] < 0.05 else "NAO"
        report += f"| T8: Random Walk Null (drift=0) | p={t8['drift_zero']['pvalue']:.4f} | {t8_verdict} |\n"
        t8d_verdict = "SIM" if t8["drift_real"]["pvalue"] < 0.05 else "NAO"
        report += f"| T8: Random Walk Null (drift=real) | p={t8['drift_real']['pvalue']:.4f} | {t8d_verdict} |\n"
    if t9 is not None:
        t9_verdict = "SIM" if t9["sr_trade_annual"] > 0.5 else "PARCIAL" if t9["sr_trade_annual"] > 0 else "NAO"
        report += f"| T9: SR trades independentes (anual) | {t9['sr_trade_annual']:.2f} | {t9_verdict} |\n"
    if t10 is not None:
        t10_verdict = "SIM" if t10["sr_bear"] > 0 else "NAO"
        report += f"| T10: SR bear market | {t10['sr_bear']:.4f} | {t10_verdict} |\n"
    if t11 is not None:
        t11_verdict = "SIM" if "PASS" in t11["verdict"] else "PARCIAL" if "MARGINAL" in t11["verdict"] else "NAO"
        report += f"| T11: SavGol-as-Instrument | {t11['verdict']} | {t11_verdict} |\n"

    report += f"""
**Score original (T1-T5): {evidence_for:.1f}/{total:.1f} ({score:.0%}) — Hipotese {verdict}.**

{conclusion_text}
"""
    return report


# ==========================================================================
# MAIN
# ==========================================================================
def main():
    print("=" * 70)
    print("  HYPOTHESIS TESTING — Hipótese 5: Momentum Adaptativo")
    print("  ret_20 em Dollar Bars como horizonte auto-ajustável")
    print("=" * 70)

    # Carregar dados
    print("\n  Carregando dados...")
    df_1m = load_data()

    print("\n  Construindo dollar bars...")
    dollar_bars = build_dollar_bars(df_1m)

    # Rodar testes
    t1 = test_1_horizon_distribution(dollar_bars)
    t2 = test_2_bars_per_day_correlation(dollar_bars, t1)
    t3 = test_3_conditional_autocorrelation(dollar_bars)
    t4 = test_4_dollar_vs_time_bars(df_1m, dollar_bars)
    t5 = test_5_sharpe_by_volume_regime(dollar_bars)
    t6 = test_6_filter_ablation(dollar_bars)
    t7 = test_7_cross_market()

    # Validacao cientifica (T8-T11)
    t8 = test_8_random_walk_null(df_1m, dollar_bars, n_simulations=500)
    t9 = test_9_independent_trade_sr(dollar_bars)
    t10 = test_10_bear_market(df_1m)
    t11 = test_11_savgol_instrument(df_1m, dollar_bars)
    t12 = test_12_feature_null_model(df_1m, dollar_bars, n_simulations=100)

    # Plots candlestick + SavGol
    print("\n" + "=" * 70)
    print("  Gerando plots candlestick + SavGol...")
    print("=" * 70)
    candle_btc = plot_candlestick_with_savgol("BTC/USDT", df_1m, "btc")
    window_expl = plot_savgol_window_explanation(df_1m)

    sp_path = os.path.join(DATA_DIR, "sp500_etf_1m.csv")
    candle_sp = None
    if os.path.exists(sp_path):
        df_sp = pd.read_csv(sp_path, parse_dates=["timestamp"])
        candle_sp = plot_candlestick_with_savgol("S&P500 ETF (SPY)", df_sp, "sp500")

    # Gerar relatório
    print("\n" + "=" * 70)
    print("  Gerando relatório...")
    print("=" * 70)
    report = generate_report(t1, t2, t3, t4, t5, t6, t7,
                             t8=t8, t9=t9, t10=t10, t11=t11, t12=t12,
                             candle_btc=candle_btc, candle_sp=candle_sp,
                             window_expl=window_expl)

    report_path = os.path.join(REPORT_DIR, "hypothesis_5_adaptive_momentum.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Relatório salvo: {report_path}")

    # Plots salvos em: relatorios/pngs/h5_t{1-5}_*.png
    print(f"  Plots salvos em: {PNG_DIR}")
    print("\n  Concluído.")


if __name__ == "__main__":
    main()