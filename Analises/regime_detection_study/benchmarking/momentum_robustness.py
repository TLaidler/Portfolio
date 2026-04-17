"""
Momentum Robustness — Validacao Estatistica de sign(ret_20)
============================================================

Tres testes para responder: "o momentum em ret_20 e real ou sorte?"

  1. Walk-Forward: janelas deslizantes nao-sobrepostas. Se momentum e real,
     a maioria das janelas gera Sharpe > 0.

  2. Permutation Test: embaralha o sinal N vezes e compara Sharpe real
     vs distribuicao nula. Produz p-value.

  3. Autocorrelacao Direta: mede a correlacao serial dos retornos das
     dollar bars. Se nao existe autocorrelacao, momentum nao pode funcionar.

  4. Breakdown por Regime: separa periodos bull/bear e mede se momentum
     funciona em ambos ou so em um.

Uso:
  python momentum_robustness.py
"""

import os
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.savgol import savgol_causal
from scipy import stats
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACAO
# ═══════════════════════════════════════════════════════════════════
DATA_DIR = "../data"                   # pasta com btcusdt_1m.csv
SAVE_DIR = "save_point_robustness"

DOLLAR_BARS_PER_DAY = 10
CALIBRATION_DAYS = 30

SAVGOL_WINDOW = 21
SAVGOL_POLYORDER = 3

RET_WINDOW = 20                        # janela principal a testar

FEE_TAKER = 0.0270 / 100              # 0.0270% Binance USDT-M
FEE_MODE = "pessimistic"

# Walk-forward
WF_WINDOW_BARS = 500                   # barras por janela (~50 dias)

# Permutation test
PERM_N_SHUFFLES = 5000                 # permutacoes

# Autocorrelacao
AC_MAX_LAG = 100                       # lags maximos a testar

RNG_SEED = 42


# ═══════════════════════════════════════════════════════════════════
# FUNCOES UTILITARIAS (replica do momentum_benchmark.py)
# ═══════════════════════════════════════════════════════════════════
def build_dollar_bars(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["timestamp"]).dt.date
    tmp["dollar_vol"] = (
        (tmp["high"] + tmp["low"] + tmp["close"]) / 3.0 * tmp["volume"]
    )
    daily = tmp.groupby("date")["dollar_vol"].sum()
    daily_cal = daily.iloc[:CALIBRATION_DAYS]
    threshold = daily_cal.median() / DOLLAR_BARS_PER_DAY
    print(f"  Dollar bar threshold: ${threshold:,.0f}")

    typical_price = (
        df["high"].values + df["low"].values + df["close"].values
    ) / 3.0
    volume = df["volume"].values
    dollar_vol = typical_price * volume
    cum_dollar = np.cumsum(dollar_vol)

    n_bars_max = int(cum_dollar[-1] / threshold) + 1
    thresholds = np.arange(1, n_bars_max + 1) * threshold
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

    tmp2 = pd.DataFrame({
        "bar_id": bar_id, "timestamp": df["timestamp"].values,
        "open": df["open"].values, "high": df["high"].values,
        "low": df["low"].values, "close": df["close"].values,
        "volume": volume, "dollar_vol": dollar_vol,
    })
    tmp2 = tmp2[tmp2["bar_id"] >= 0]

    bars = tmp2.groupby("bar_id").agg(
        timestamp=("timestamp", "first"), open=("open", "first"),
        high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum"),
        dollar_volume=("dollar_vol", "sum"), tick_count=("bar_id", "count"),
    )
    bars["vwap"] = bars["dollar_volume"] / bars["volume"].replace(0, np.nan)
    bars = bars.reset_index(drop=True)
    print(f"  Dollar bars: {len(bars)}")
    return bars


# savgol_causal imported from utils.savgol (canonical, edge-padded version)


def compute_strategy_returns(
    predictions: np.ndarray,
    actual_returns: np.ndarray,
    fee_taker: float = 0.0,
    fee_mode: str = "pessimistic",
) -> np.ndarray:
    raw = predictions * actual_returns
    if fee_taker == 0.0:
        return raw
    fee_entry = fee_taker
    fee_exit = fee_taker if fee_mode == "pessimistic" else fee_taker * (0.009 / 0.027)
    costs = np.zeros_like(raw)
    prev = 0.0
    for i in range(len(predictions)):
        cur = predictions[i]
        if cur != prev:
            if prev != 0:
                costs[i] += fee_exit
            if cur != 0:
                costs[i] += fee_entry
        prev = cur
    return raw - costs


def compute_signal_and_returns(bars: pd.DataFrame):
    """Computa ret_20 (SavGol), sinal sign(ret_20), e actual returns."""
    close = bars["close"].values.astype(np.float64)
    close_sg = savgol_causal(close, SAVGOL_WINDOW, SAVGOL_POLYORDER)
    ret_n = pd.Series(close_sg).pct_change(RET_WINDOW).values
    predictions = np.sign(ret_n)
    predictions = np.nan_to_num(predictions, nan=0.0)
    actual_ret = np.diff(close, prepend=close[0]) / np.maximum(close, 1e-12)
    return predictions, actual_ret, close


def sharpe(returns: np.ndarray) -> float:
    if len(returns) < 2 or np.std(returns) == 0:
        return 0.0
    return np.mean(returns) / np.std(returns)


def _save(fig, name):
    path = os.path.join(SAVE_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"    Plot salvo: {path}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 1: WALK-FORWARD
# ═══════════════════════════════════════════════════════════════════
def test_walk_forward(bars: pd.DataFrame) -> dict:
    """
    Divide as dollar bars em janelas nao-sobrepostas de WF_WINDOW_BARS.
    Para cada janela, computa sign(ret_20) e mede Sharpe e retorno.
    """
    print("\n[TESTE 1] Walk-Forward Analysis")
    print("-" * 50)

    predictions, actual_ret, close = compute_signal_and_returns(bars)
    timestamps = pd.to_datetime(bars["timestamp"])

    n = len(bars)
    windows = []
    start = RET_WINDOW + SAVGOL_WINDOW  # pular warmup
    while start + WF_WINDOW_BARS <= n:
        end = start + WF_WINDOW_BARS
        slc = slice(start, end)

        pred_w = predictions[slc]
        ret_w = compute_strategy_returns(pred_w, actual_ret[slc], FEE_TAKER, FEE_MODE)
        equity_w = np.cumprod(1 + ret_w)

        sr = sharpe(ret_w)
        total_ret = equity_w[-1] - 1
        n_active = int(np.sum(pred_w != 0))
        pos_changes = int(np.sum(np.diff(pred_w) != 0))

        # BTC B&H na janela
        bh_ret = (close[end - 1] / close[start]) - 1

        ts_start = timestamps.iloc[start]
        ts_end = timestamps.iloc[end - 1]

        windows.append({
            "start": start, "end": end,
            "ts_start": ts_start, "ts_end": ts_end,
            "sharpe": sr, "return": total_ret,
            "bh_return": bh_ret, "alpha": total_ret - bh_ret,
            "n_active": n_active, "pos_changes": pos_changes,
        })
        start = end

    n_positive_sr = sum(1 for w in windows if w["sharpe"] > 0)
    n_positive_ret = sum(1 for w in windows if w["return"] > 0)
    n_positive_alpha = sum(1 for w in windows if w["alpha"] > 0)
    sharpes = [w["sharpe"] for w in windows]

    print(f"  Janelas: {len(windows)} x {WF_WINDOW_BARS} barras "
          f"(~{WF_WINDOW_BARS / DOLLAR_BARS_PER_DAY:.0f} dias cada)")
    print(f"  Sharpe > 0:  {n_positive_sr}/{len(windows)} "
          f"({n_positive_sr/len(windows)*100:.1f}%)")
    print(f"  Retorno > 0: {n_positive_ret}/{len(windows)} "
          f"({n_positive_ret/len(windows)*100:.1f}%)")
    print(f"  Alpha > 0:   {n_positive_alpha}/{len(windows)} "
          f"({n_positive_alpha/len(windows)*100:.1f}%)")
    print(f"  Sharpe medio: {np.mean(sharpes):.4f} +/- {np.std(sharpes):.4f}")
    print(f"  Sharpe min/max: {np.min(sharpes):.4f} / {np.max(sharpes):.4f}")

    for i, w in enumerate(windows):
        flag = "+" if w["sharpe"] > 0 else "-"
        print(f"    [{flag}] Janela {i+1:2d}: "
              f"{w['ts_start'].strftime('%Y-%m-%d')} a {w['ts_end'].strftime('%Y-%m-%d')} | "
              f"SR={w['sharpe']:+.4f} | Ret={w['return']:+.2%} | "
              f"BH={w['bh_return']:+.2%} | Alpha={w['alpha']:+.2%}")

    # --- Plot walk-forward ---
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Sharpe por janela
    ax = axes[0]
    x = range(len(windows))
    colors = ["#4CAF50" if w["sharpe"] > 0 else "#F44336" for w in windows]
    ax.bar(x, sharpes, color=colors, edgecolor="black", linewidth=0.5)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhline(np.mean(sharpes), color="blue", ls="--", lw=1.5,
               label=f"Media={np.mean(sharpes):.4f}")
    ax.set_ylabel("Sharpe Ratio")
    ax.set_title(f"Walk-Forward: Sharpe por Janela ({WF_WINDOW_BARS} barras) "
                 f"| {n_positive_sr}/{len(windows)} positivos")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Retorno vs BTC por janela
    ax = axes[1]
    rets = [w["return"] * 100 for w in windows]
    bhs = [w["bh_return"] * 100 for w in windows]
    width = 0.35
    ax.bar([i - width/2 for i in x], rets, width, label="sign(ret_20)", color="#2196F3")
    ax.bar([i + width/2 for i in x], bhs, width, label="BTC B&H", color="#FF9800", alpha=0.7)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Janela")
    ax.set_ylabel("Retorno (%)")
    ax.set_title("Retorno por Janela: sign(ret_20) vs BTC B&H")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Labels nas janelas
    labels = [f"{w['ts_start'].strftime('%y/%m')}" for w in windows]
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=45, fontsize=8)

    plt.tight_layout()
    _save(fig, "walk_forward.png")

    return {
        "windows": windows,
        "n_positive_sr": n_positive_sr,
        "n_total": len(windows),
        "pct_positive": n_positive_sr / len(windows) * 100,
        "mean_sharpe": np.mean(sharpes),
        "std_sharpe": np.std(sharpes),
    }


# ═══════════════════════════════════════════════════════════════════
# TESTE 2: PERMUTATION TEST
# ═══════════════════════════════════════════════════════════════════
def test_permutation(bars: pd.DataFrame) -> dict:
    """
    Embaralha o sinal sign(ret_20) N vezes e compara Sharpe real vs nulo.
    H0: "o sinal nao contem informacao — o Sharpe observado e acaso."
    """
    print(f"\n[TESTE 2] Permutation Test ({PERM_N_SHUFFLES} shuffles)")
    print("-" * 50)

    rng = np.random.default_rng(RNG_SEED)
    predictions, actual_ret, _ = compute_signal_and_returns(bars)

    # Sharpe real
    strat_ret = compute_strategy_returns(predictions, actual_ret, FEE_TAKER, FEE_MODE)
    real_sharpe = sharpe(strat_ret)

    # Sharpes nulos (shuffling as predicoes, mantendo actual_ret)
    null_sharpes = np.zeros(PERM_N_SHUFFLES)
    for i in range(PERM_N_SHUFFLES):
        perm_pred = predictions.copy()
        rng.shuffle(perm_pred)
        perm_ret = compute_strategy_returns(perm_pred, actual_ret, FEE_TAKER, FEE_MODE)
        null_sharpes[i] = sharpe(perm_ret)

    # p-value (one-sided: H1 = real > random)
    p_value = np.mean(null_sharpes >= real_sharpe)

    print(f"  Sharpe real: {real_sharpe:.6f}")
    print(f"  Sharpe nulo: {np.mean(null_sharpes):.6f} +/- {np.std(null_sharpes):.6f}")
    print(f"  Sharpe nulo max: {np.max(null_sharpes):.6f}")
    print(f"  p-value (one-sided): {p_value:.6f}")
    if p_value < 0.01:
        print(f"  >>> REJEITA H0 a 1% — sinal e ESTATISTICAMENTE SIGNIFICATIVO")
    elif p_value < 0.05:
        print(f"  >>> REJEITA H0 a 5% — sinal significativo (marginal)")
    else:
        print(f"  >>> NAO REJEITA H0 — sinal pode ser acaso")

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(null_sharpes, bins=80, edgecolor="black", alpha=0.7,
            color="#90CAF9", linewidth=0.3, label="H0: shuffle")
    ax.axvline(real_sharpe, color="red", lw=2.5, ls="--",
               label=f"Sharpe real = {real_sharpe:.4f}")
    ax.axvline(np.mean(null_sharpes), color="blue", lw=1.5, ls=":",
               label=f"Media nulo = {np.mean(null_sharpes):.4f}")

    # Percentis
    p95 = np.percentile(null_sharpes, 95)
    p99 = np.percentile(null_sharpes, 99)
    ax.axvline(p95, color="orange", lw=1, ls="--", label=f"P95 = {p95:.4f}")
    ax.axvline(p99, color="purple", lw=1, ls="--", label=f"P99 = {p99:.4f}")

    txt = (
        f"N shuffles = {PERM_N_SHUFFLES}\n"
        f"p-value = {p_value:.4f}\n"
        f"Sharpe real = {real_sharpe:.4f}\n"
        f"Sharpe nulo = {np.mean(null_sharpes):.4f}"
    )
    ax.text(0.02, 0.95, txt, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", family="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

    ax.set_xlabel("Sharpe Ratio")
    ax.set_ylabel("Frequencia")
    ax.set_title(f"Permutation Test — sign(ret_{RET_WINDOW}) | "
                 f"p-value = {p_value:.4f}")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, "permutation_test.png")

    return {
        "real_sharpe": real_sharpe,
        "null_mean": np.mean(null_sharpes),
        "null_std": np.std(null_sharpes),
        "p_value": p_value,
        "p95": p95,
        "p99": p99,
    }


# ═══════════════════════════════════════════════════════════════════
# TESTE 3: AUTOCORRELACAO DOS RETORNOS
# ═══════════════════════════════════════════════════════════════════
def test_autocorrelation(bars: pd.DataFrame) -> dict:
    """
    Mede autocorrelacao dos retornos das dollar bars em lags 1..AC_MAX_LAG.
    Se os retornos nao tem autocorrelacao, sign(ret_N) e coin flip.
    """
    print(f"\n[TESTE 3] Autocorrelacao dos Retornos (lags 1-{AC_MAX_LAG})")
    print("-" * 50)

    close = bars["close"].values.astype(np.float64)
    ret = np.diff(close) / close[:-1]  # retornos simples bar-a-bar

    n = len(ret)
    lags = np.arange(1, AC_MAX_LAG + 1)
    autocorrs = np.zeros(AC_MAX_LAG)
    p_values = np.zeros(AC_MAX_LAG)

    # Ljung-Box threshold (2/sqrt(n))
    ci_bound = 2.0 / np.sqrt(n)

    for i, lag in enumerate(lags):
        if lag < n:
            corr, pval = stats.pearsonr(ret[lag:], ret[:-lag])
            autocorrs[i] = corr
            p_values[i] = pval
        else:
            autocorrs[i] = 0.0
            p_values[i] = 1.0

    # Lags significativos (p < 0.05)
    sig_mask = p_values < 0.05
    n_significant = np.sum(sig_mask)

    # Autocorrelacao nos lags relevantes para ret_20
    ac_1 = autocorrs[0]
    ac_5 = autocorrs[4] if len(autocorrs) > 4 else 0
    ac_10 = autocorrs[9] if len(autocorrs) > 9 else 0
    ac_20 = autocorrs[19] if len(autocorrs) > 19 else 0

    # Autocorrelacao acumulada (soma dos lags 1-20, proxy para momentum de 20 barras)
    ac_cum_20 = np.sum(autocorrs[:20])

    print(f"  N retornos: {n}")
    print(f"  IC 95%: +/- {ci_bound:.4f}")
    print(f"  Lags significativos (p<0.05): {n_significant}/{AC_MAX_LAG}")
    print(f"  AC(1):  {ac_1:+.4f}  (p={p_values[0]:.4f})")
    print(f"  AC(5):  {ac_5:+.4f}  (p={p_values[4]:.4f})")
    print(f"  AC(10): {ac_10:+.4f} (p={p_values[9]:.4f})")
    print(f"  AC(20): {ac_20:+.4f} (p={p_values[19]:.4f})")
    print(f"  Sum AC(1-20): {ac_cum_20:+.4f} "
          f"({'POSITIVO = momentum' if ac_cum_20 > 0 else 'NEGATIVO = mean-reversion'})")

    # Teste Ljung-Box agregado nos lags 1-20
    Q_stat = n * (n + 2) * np.sum(autocorrs[:20]**2 / (n - lags[:20]))
    lb_pvalue = 1 - stats.chi2.cdf(Q_stat, df=20)
    print(f"  Ljung-Box Q(20): {Q_stat:.2f} (p={lb_pvalue:.6f})")
    if lb_pvalue < 0.05:
        print(f"  >>> REJEITA IID a 5% — retornos TEM autocorrelacao significativa")
    else:
        print(f"  >>> NAO REJEITA IID — sem evidencia de autocorrelacao")

    # --- Plot autocorrelacao ---
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    ax = axes[0]
    colors_ac = ["#F44336" if p < 0.05 else "#90CAF9" for p in p_values]
    ax.bar(lags, autocorrs, color=colors_ac, edgecolor="black", linewidth=0.3)
    ax.axhline(ci_bound, color="red", ls="--", lw=1, label=f"IC 95% ({ci_bound:.4f})")
    ax.axhline(-ci_bound, color="red", ls="--", lw=1)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Lag (barras)")
    ax.set_ylabel("Autocorrelacao")
    ax.set_title(f"Autocorrelacao dos Retornos — Dollar Bars | "
                 f"{n_significant}/{AC_MAX_LAG} lags significativos")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Plot zoom nos primeiros 30 lags
    ax = axes[1]
    zoom = min(30, AC_MAX_LAG)
    colors_zoom = ["#F44336" if p < 0.05 else "#90CAF9" for p in p_values[:zoom]]
    ax.bar(lags[:zoom], autocorrs[:zoom], color=colors_zoom,
           edgecolor="black", linewidth=0.5)
    ax.axhline(ci_bound, color="red", ls="--", lw=1, label=f"IC 95%")
    ax.axhline(-ci_bound, color="red", ls="--", lw=1)
    ax.axhline(0, color="black", lw=0.8)

    # Marcar lag 20
    if zoom >= 20:
        ax.axvline(20, color="green", ls=":", lw=2, alpha=0.7, label="Lag 20 (ret_20)")

    txt = (
        f"AC(1) = {ac_1:+.4f}\n"
        f"AC(20) = {ac_20:+.4f}\n"
        f"Sum AC(1-20) = {ac_cum_20:+.4f}\n"
        f"Ljung-Box p = {lb_pvalue:.4f}"
    )
    ax.text(0.98, 0.95, txt, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", horizontalalignment="right",
            family="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

    ax.set_xlabel("Lag (barras)")
    ax.set_ylabel("Autocorrelacao")
    ax.set_title("Zoom: Lags 1-30 (vermelho = p < 0.05)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    _save(fig, "autocorrelation.png")

    return {
        "ac_1": ac_1, "ac_5": ac_5, "ac_10": ac_10, "ac_20": ac_20,
        "ac_cum_20": ac_cum_20,
        "n_significant": n_significant,
        "ljung_box_Q": Q_stat,
        "ljung_box_p": lb_pvalue,
        "ci_bound": ci_bound,
    }


# ═══════════════════════════════════════════════════════════════════
# TESTE 4: BREAKDOWN POR REGIME (bull vs bear)
# ═══════════════════════════════════════════════════════════════════
def test_regime_breakdown(bars: pd.DataFrame) -> dict:
    """
    Classifica cada janela como bull ou bear (retorno BTC > ou < 0)
    e mede se momentum funciona em ambos os regimes.
    """
    print(f"\n[TESTE 4] Breakdown por Regime (Bull vs Bear)")
    print("-" * 50)

    predictions, actual_ret, close = compute_signal_and_returns(bars)
    timestamps = pd.to_datetime(bars["timestamp"])

    # Dividir em janelas de WF_WINDOW_BARS
    n = len(bars)
    start = RET_WINDOW + SAVGOL_WINDOW
    bull_sharpes = []
    bear_sharpes = []
    bull_returns = []
    bear_returns = []
    all_windows = []

    while start + WF_WINDOW_BARS <= n:
        end = start + WF_WINDOW_BARS
        slc = slice(start, end)

        pred_w = predictions[slc]
        ret_w = compute_strategy_returns(pred_w, actual_ret[slc], FEE_TAKER, FEE_MODE)
        sr = sharpe(ret_w)
        total_ret = np.prod(1 + ret_w) - 1
        bh_ret = (close[end - 1] / close[start]) - 1

        regime = "bull" if bh_ret > 0 else "bear"
        if regime == "bull":
            bull_sharpes.append(sr)
            bull_returns.append(total_ret)
        else:
            bear_sharpes.append(sr)
            bear_returns.append(total_ret)

        all_windows.append({
            "regime": regime, "sharpe": sr,
            "return": total_ret, "bh_return": bh_ret,
            "ts_start": timestamps.iloc[start],
            "ts_end": timestamps.iloc[end - 1],
        })
        start = end

    n_bull = len(bull_sharpes)
    n_bear = len(bear_sharpes)
    bull_pos = sum(1 for s in bull_sharpes if s > 0)
    bear_pos = sum(1 for s in bear_sharpes if s > 0)

    print(f"  Janelas Bull: {n_bull} | SR > 0: {bull_pos}/{n_bull} "
          f"({bull_pos/max(n_bull,1)*100:.1f}%)")
    print(f"    SR medio: {np.mean(bull_sharpes):.4f} +/- {np.std(bull_sharpes):.4f}")
    print(f"    Ret medio: {np.mean(bull_returns)*100:+.2f}%")

    print(f"  Janelas Bear: {n_bear} | SR > 0: {bear_pos}/{n_bear} "
          f"({bear_pos/max(n_bear,1)*100:.1f}%)")
    print(f"    SR medio: {np.mean(bear_sharpes):.4f} +/- {np.std(bear_sharpes):.4f}")
    print(f"    Ret medio: {np.mean(bear_returns)*100:+.2f}%")

    # Teste: momentum funciona em ambos? (t-test)
    if n_bull >= 2 and n_bear >= 2:
        t_bull, p_bull = stats.ttest_1samp(bull_sharpes, 0)
        t_bear, p_bear = stats.ttest_1samp(bear_sharpes, 0)
        print(f"  t-test Bull SR > 0: t={t_bull:.3f}, p={p_bull:.4f} "
              f"({'SIG' if p_bull < 0.05 else 'NS'})")
        print(f"  t-test Bear SR > 0: t={t_bear:.3f}, p={p_bear:.4f} "
              f"({'SIG' if p_bear < 0.05 else 'NS'})")
    else:
        p_bull = p_bear = 1.0

    # --- Plot ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    if bull_sharpes:
        ax.hist(bull_sharpes, bins=max(5, n_bull // 3), alpha=0.7,
                color="#4CAF50", edgecolor="black", linewidth=0.5, label="Bull")
    if bear_sharpes:
        ax.hist(bear_sharpes, bins=max(5, n_bear // 3), alpha=0.7,
                color="#F44336", edgecolor="black", linewidth=0.5, label="Bear")
    ax.axvline(0, color="black", lw=1)
    if bull_sharpes:
        ax.axvline(np.mean(bull_sharpes), color="#2E7D32", ls="--", lw=1.5,
                   label=f"Bull avg={np.mean(bull_sharpes):.3f}")
    if bear_sharpes:
        ax.axvline(np.mean(bear_sharpes), color="#C62828", ls="--", lw=1.5,
                   label=f"Bear avg={np.mean(bear_sharpes):.3f}")
    ax.set_xlabel("Sharpe Ratio")
    ax.set_ylabel("Frequencia")
    ax.set_title("Sharpe por Regime")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    data_plot = []
    labels = []
    if bull_sharpes:
        data_plot.append(bull_sharpes)
        labels.append(f"Bull\n(n={n_bull})")
    if bear_sharpes:
        data_plot.append(bear_sharpes)
        labels.append(f"Bear\n(n={n_bear})")
    if data_plot:
        bp = ax.boxplot(data_plot, labels=labels, patch_artist=True)
        colors_bp = ["#C8E6C9", "#FFCDD2"]
        for patch, color in zip(bp["boxes"], colors_bp[:len(data_plot)]):
            patch.set_facecolor(color)
    ax.axhline(0, color="red", ls=":", lw=1)
    ax.set_ylabel("Sharpe Ratio")
    ax.set_title("Distribuicao de Sharpe: Bull vs Bear")
    ax.grid(True, alpha=0.3)

    fig.suptitle(f"Regime Breakdown — sign(ret_{RET_WINDOW})", fontsize=13, fontweight="bold")
    plt.tight_layout()
    _save(fig, "regime_breakdown.png")

    return {
        "n_bull": n_bull, "n_bear": n_bear,
        "bull_pct_positive": bull_pos / max(n_bull, 1) * 100,
        "bear_pct_positive": bear_pos / max(n_bear, 1) * 100,
        "bull_mean_sr": np.mean(bull_sharpes) if bull_sharpes else 0,
        "bear_mean_sr": np.mean(bear_sharpes) if bear_sharpes else 0,
        "p_bull": p_bull, "p_bear": p_bear,
    }


# ═══════════════════════════════════════════════════════════════════
# RELATORIO CONSOLIDADO
# ═══════════════════════════════════════════════════════════════════
def save_consolidated_report(wf, perm, ac, regime):
    lines = []
    lines.append("MOMENTUM ROBUSTNESS REPORT")
    lines.append("=" * 60)
    lines.append(f"  Sinal testado: sign(ret_{RET_WINDOW}) com SavGol causal")
    lines.append(f"  Fees: {FEE_TAKER*100:.4f}% taker | mode = {FEE_MODE}")
    lines.append("")

    lines.append("  [1] WALK-FORWARD")
    lines.append(f"      Janelas: {wf['n_total']} x {WF_WINDOW_BARS} barras")
    lines.append(f"      Sharpe > 0: {wf['n_positive_sr']}/{wf['n_total']} "
                 f"({wf['pct_positive']:.1f}%)")
    lines.append(f"      SR medio: {wf['mean_sharpe']:.4f} +/- {wf['std_sharpe']:.4f}")
    lines.append("")

    lines.append("  [2] PERMUTATION TEST")
    lines.append(f"      Sharpe real: {perm['real_sharpe']:.6f}")
    lines.append(f"      Sharpe nulo: {perm['null_mean']:.6f} +/- {perm['null_std']:.6f}")
    lines.append(f"      p-value: {perm['p_value']:.6f}")
    sig = "SIM (p < 0.01)" if perm['p_value'] < 0.01 else \
          "MARGINAL (p < 0.05)" if perm['p_value'] < 0.05 else "NAO"
    lines.append(f"      Significativo: {sig}")
    lines.append("")

    lines.append("  [3] AUTOCORRELACAO")
    lines.append(f"      AC(1): {ac['ac_1']:+.4f}")
    lines.append(f"      AC(20): {ac['ac_20']:+.4f}")
    lines.append(f"      Sum AC(1-20): {ac['ac_cum_20']:+.4f}")
    lines.append(f"      Ljung-Box Q(20): {ac['ljung_box_Q']:.2f} (p={ac['ljung_box_p']:.6f})")
    lines.append(f"      IID rejeitado: {'SIM' if ac['ljung_box_p'] < 0.05 else 'NAO'}")
    lines.append("")

    lines.append("  [4] REGIME BREAKDOWN")
    lines.append(f"      Bull: {regime['n_bull']} janelas | "
                 f"SR > 0: {regime['bull_pct_positive']:.1f}% | "
                 f"SR medio: {regime['bull_mean_sr']:.4f} | "
                 f"p = {regime['p_bull']:.4f}")
    lines.append(f"      Bear: {regime['n_bear']} janelas | "
                 f"SR > 0: {regime['bear_pct_positive']:.1f}% | "
                 f"SR medio: {regime['bear_mean_sr']:.4f} | "
                 f"p = {regime['p_bear']:.4f}")
    lines.append("")

    # Veredicto
    lines.append("  VEREDICTO CONSOLIDADO")
    lines.append("  " + "-" * 40)
    score = 0
    reasons = []

    if wf["pct_positive"] >= 60:
        score += 1
        reasons.append(f"  [+] Walk-forward: {wf['pct_positive']:.0f}% janelas positivas")
    else:
        reasons.append(f"  [-] Walk-forward: apenas {wf['pct_positive']:.0f}% janelas positivas")

    if perm["p_value"] < 0.05:
        score += 1
        reasons.append(f"  [+] Permutation: p={perm['p_value']:.4f} — sinal significativo")
    else:
        reasons.append(f"  [-] Permutation: p={perm['p_value']:.4f} — pode ser acaso")

    if ac["ljung_box_p"] < 0.05:
        score += 1
        reasons.append(f"  [+] Autocorrelacao: Ljung-Box rejeita IID (p={ac['ljung_box_p']:.4f})")
    else:
        reasons.append(f"  [-] Autocorrelacao: sem evidencia de dependencia serial")

    if regime["bull_pct_positive"] >= 50 and regime["bear_pct_positive"] >= 50:
        score += 1
        reasons.append(f"  [+] Regime: funciona em bull ({regime['bull_pct_positive']:.0f}%) "
                       f"E bear ({regime['bear_pct_positive']:.0f}%)")
    else:
        reasons.append(f"  [-] Regime: nao funciona em ambos os regimes")

    for r in reasons:
        lines.append(r)

    lines.append("")
    if score >= 4:
        lines.append("  >>> MOMENTUM E ROBUSTO (4/4 testes positivos)")
    elif score >= 3:
        lines.append("  >>> MOMENTUM E PROVAVEL (3/4 testes positivos)")
    elif score >= 2:
        lines.append("  >>> EVIDENCIA MISTA (2/4 — cautela necessaria)")
    else:
        lines.append(f"  >>> EVIDENCIA FRACA ({score}/4 — possivelmente sorte)")

    path = os.path.join(SAVE_DIR, "robustness_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  Relatorio salvo em {path}")

    # Imprimir tambem no terminal
    print("\n" + "\n".join(lines))


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, DATA_DIR)
    global SAVE_DIR
    SAVE_DIR = os.path.join(script_dir, SAVE_DIR)
    os.makedirs(SAVE_DIR, exist_ok=True)

    btc_path = os.path.join(data_dir, "btcusdt_1m.csv")

    print("MOMENTUM ROBUSTNESS VALIDATION")
    print("=" * 60)

    print(f"\n[0] Carregando dados de {btc_path}")
    btc_df = pd.read_csv(btc_path, parse_dates=["timestamp"])
    print(f"  Linhas 1-min: {len(btc_df):,}")

    print("\n    Construindo dollar bars")
    bars = build_dollar_bars(btc_df)

    # Rodar os 4 testes
    wf_results = test_walk_forward(bars)
    perm_results = test_permutation(bars)
    ac_results = test_autocorrelation(bars)
    regime_results = test_regime_breakdown(bars)

    # Relatorio consolidado
    save_consolidated_report(wf_results, perm_results, ac_results, regime_results)


if __name__ == "__main__":
    main()
