"""
Momentum Grid Search — Janelas Otimas para sign(ret_N)
=======================================================

Grid sobre janelas de retorno (com e sem SavGol) para identificar
quais janelas sao otimas para captura de momentum em dollar bars BTC.

Testa em ambos os datasets (treino e OOS) para separar in-sample vs
out-of-sample e detectar overfitting de janela.

Uso:
  python momentum_grid.py
"""

import os
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.savgol import savgol_causal
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACAO
# ═══════════════════════════════════════════════════════════════════
DATA_DIR = "../data"                   # treino (~4.5 anos)
NEW_DATA_DIR = "../new_data"           # OOS bear (ago/2025-mar/2026)
SAVE_DIR = "save_point_grid"

DOLLAR_BARS_PER_DAY = 10
CALIBRATION_DAYS = 30

SAVGOL_WINDOW = 21
SAVGOL_POLYORDER = 3

FEE_TAKER = 0.0270 / 100
FEE_MODE = "pessimistic"

# Grid de janelas a testar
RET_WINDOWS = [3, 5, 7, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]

# Testar com e sem SavGol
SAVGOL_MODES = [True, False]

# Walk-forward para robustez por janela
WF_WINDOW_BARS = 500


# ═══════════════════════════════════════════════════════════════════
# FUNCOES UTILITARIAS
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

    typical_price = (df["high"].values + df["low"].values + df["close"].values) / 3.0
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
# GRID: UMA JANELA, TODAS AS METRICAS
# ═══════════════════════════════════════════════════════════════════
def evaluate_window(bars: pd.DataFrame, ret_window: int, use_savgol: bool) -> dict:
    """Avalia sign(ret_N) para uma janela especifica."""
    close = bars["close"].values.astype(np.float64)

    if use_savgol:
        close_filtered = savgol_causal(close, SAVGOL_WINDOW, SAVGOL_POLYORDER)
    else:
        close_filtered = close.copy()

    ret_n = pd.Series(close_filtered).pct_change(ret_window).values
    predictions = np.sign(ret_n)
    predictions = np.nan_to_num(predictions, nan=0.0)

    actual_ret = np.diff(close, prepend=close[0]) / np.maximum(close, 1e-12)
    strat_ret = compute_strategy_returns(predictions, actual_ret, FEE_TAKER, FEE_MODE)

    equity = np.cumprod(1 + strat_ret)
    total_ret = equity[-1] - 1
    bh_ret = (close[-1] / close[0]) - 1

    # Max drawdown
    running_max = np.maximum.accumulate(equity)
    drawdowns = (equity - running_max) / running_max
    max_dd = drawdowns.min()

    # Sharpe
    sr_all = sharpe(strat_ret)

    # Position changes
    pos_changes = int(np.sum(np.diff(predictions) != 0))

    # Skewness / Kurtosis dos retornos ativos
    active_mask = predictions != 0
    active_ret = strat_ret[active_mask]
    skew = float(pd.Series(active_ret).skew()) if len(active_ret) > 2 else 0.0
    kurt = float(pd.Series(active_ret).kurtosis()) if len(active_ret) > 2 else 0.0
    sr_active = sharpe(active_ret)

    # Walk-forward: % janelas com Sharpe > 0
    n = len(bars)
    warmup = ret_window + (SAVGOL_WINDOW if use_savgol else 0)
    wf_positive = 0
    wf_total = 0
    wf_sharpes = []
    start = warmup
    while start + WF_WINDOW_BARS <= n:
        end = start + WF_WINDOW_BARS
        slc = slice(start, end)
        pred_w = predictions[slc]
        ret_w = compute_strategy_returns(pred_w, actual_ret[slc], FEE_TAKER, FEE_MODE)
        sr_w = sharpe(ret_w)
        wf_sharpes.append(sr_w)
        if sr_w > 0:
            wf_positive += 1
        wf_total += 1
        start = end

    wf_pct = wf_positive / max(wf_total, 1) * 100
    wf_sr_mean = np.mean(wf_sharpes) if wf_sharpes else 0.0
    wf_sr_std = np.std(wf_sharpes) if wf_sharpes else 0.0
    wf_sr_min = np.min(wf_sharpes) if wf_sharpes else 0.0

    ts = pd.to_datetime(bars["timestamp"])
    n_days = (ts.iloc[-1] - ts.iloc[0]).total_seconds() / 86400

    return {
        "window": ret_window,
        "savgol": use_savgol,
        "label": f"ret_{ret_window}" + ("_sg" if use_savgol else "_raw"),
        "total_ret": total_ret,
        "bh_ret": bh_ret,
        "alpha": total_ret - bh_ret,
        "sharpe_all": sr_all,
        "sharpe_active": sr_active,
        "max_dd": max_dd,
        "pos_changes": pos_changes,
        "skew": skew,
        "kurt": kurt,
        "wf_pct_positive": wf_pct,
        "wf_n_windows": wf_total,
        "wf_sr_mean": wf_sr_mean,
        "wf_sr_std": wf_sr_std,
        "wf_sr_min": wf_sr_min,
        "n_days": n_days,
        "n_bars": len(bars),
        "equity": equity,
        "strat_ret": strat_ret,
        "predictions": predictions,
    }


# ═══════════════════════════════════════════════════════════════════
# RODAR GRID COMPLETO
# ═══════════════════════════════════════════════════════════════════
def run_grid(bars: pd.DataFrame, dataset_label: str) -> list[dict]:
    """Roda grid completo e retorna lista de resultados."""
    print(f"\n  Rodando grid: {len(RET_WINDOWS)} janelas x {len(SAVGOL_MODES)} modos "
          f"= {len(RET_WINDOWS) * len(SAVGOL_MODES)} combinacoes")

    results = []
    for use_sg in SAVGOL_MODES:
        for w in RET_WINDOWS:
            r = evaluate_window(bars, w, use_sg)
            results.append(r)
            sr_str = f"{r['sharpe_all']:+.4f}"
            ret_str = f"{r['total_ret']:+.2%}"
            wf_str = f"{r['wf_pct_positive']:.0f}%"
            print(f"    {r['label']:>12s} | SR={sr_str} | Ret={ret_str} | "
                  f"WF+={wf_str} | DD={r['max_dd']*100:.1f}%")

    return results


# ═══════════════════════════════════════════════════════════════════
# TABELA E RANKING
# ═══════════════════════════════════════════════════════════════════
def print_ranking(results: list[dict], dataset_label: str):
    """Imprime tabela ordenada por score composto."""
    # Score composto: normaliza Sharpe, WF%, e penaliza DD
    for r in results:
        # Score = Sharpe_all * wf_pct/100 * (1 + max_dd) — penaliza drawdown
        r["score"] = r["sharpe_all"] * (r["wf_pct_positive"] / 100) * (1 + r["max_dd"])

    ranked = sorted(results, key=lambda x: x["score"], reverse=True)

    print(f"\n{'='*110}")
    print(f"  GRID RANKING — {dataset_label}")
    print(f"{'='*110}")
    print(f"  {'#':>3} {'Janela':>12} {'SR(all)':>8} {'SR(act)':>8} "
          f"{'Retorno':>10} {'Alpha':>10} {'MaxDD':>8} "
          f"{'WF+%':>6} {'WF_SR':>8} {'WF_min':>8} "
          f"{'Flips':>6} {'Score':>8}")
    print(f"  {'-'*106}")

    for i, r in enumerate(ranked):
        print(f"  {i+1:>3} {r['label']:>12} {r['sharpe_all']:>+8.4f} {r['sharpe_active']:>+8.4f} "
              f"{r['total_ret']:>+10.2%} {r['alpha']:>+10.2%} {r['max_dd']*100:>+8.1f}% "
              f"{r['wf_pct_positive']:>5.0f}% {r['wf_sr_mean']:>+8.4f} {r['wf_sr_min']:>+8.4f} "
              f"{r['pos_changes']:>6} {r['score']:>8.4f}")

    # Top 5
    print(f"\n  TOP 5 janelas:")
    for i, r in enumerate(ranked[:5]):
        print(f"    {i+1}. {r['label']} — SR={r['sharpe_all']:+.4f}, "
              f"WF={r['wf_pct_positive']:.0f}%, DD={r['max_dd']*100:.1f}%, "
              f"Ret={r['total_ret']:+.2%}")

    return ranked


# ═══════════════════════════════════════════════════════════════════
# PLOTS
# ═══════════════════════════════════════════════════════════════════
def plot_grid(results: list[dict], dataset_label: str, suffix: str):
    """Gera plots do grid."""

    # Separar SG vs Raw
    sg_results = [r for r in results if r["savgol"]]
    raw_results = [r for r in results if not r["savgol"]]

    # --- 1. Sharpe vs Janela (linhas SG e Raw) ---
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Sharpe
    ax = axes[0][0]
    if sg_results:
        ax.plot([r["window"] for r in sg_results],
                [r["sharpe_all"] for r in sg_results],
                "o-", color="#2196F3", lw=2, markersize=6, label="SavGol")
    if raw_results:
        ax.plot([r["window"] for r in raw_results],
                [r["sharpe_all"] for r in raw_results],
                "s--", color="#FF9800", lw=2, markersize=6, label="Raw")
    ax.axhline(0, color="black", lw=0.5)
    ax.set_xlabel("Janela (barras)")
    ax.set_ylabel("Sharpe Ratio")
    ax.set_title("Sharpe vs Janela de Retorno")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # WF % positivo
    ax = axes[0][1]
    if sg_results:
        ax.plot([r["window"] for r in sg_results],
                [r["wf_pct_positive"] for r in sg_results],
                "o-", color="#2196F3", lw=2, markersize=6, label="SavGol")
    if raw_results:
        ax.plot([r["window"] for r in raw_results],
                [r["wf_pct_positive"] for r in raw_results],
                "s--", color="#FF9800", lw=2, markersize=6, label="Raw")
    ax.axhline(50, color="red", ls=":", lw=1, label="50% (coin flip)")
    ax.set_xlabel("Janela (barras)")
    ax.set_ylabel("% Janelas WF Positivas")
    ax.set_title("Robustez Walk-Forward vs Janela")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Max Drawdown
    ax = axes[1][0]
    if sg_results:
        ax.plot([r["window"] for r in sg_results],
                [r["max_dd"] * 100 for r in sg_results],
                "o-", color="#2196F3", lw=2, markersize=6, label="SavGol")
    if raw_results:
        ax.plot([r["window"] for r in raw_results],
                [r["max_dd"] * 100 for r in raw_results],
                "s--", color="#FF9800", lw=2, markersize=6, label="Raw")
    ax.set_xlabel("Janela (barras)")
    ax.set_ylabel("Max Drawdown (%)")
    ax.set_title("Max Drawdown vs Janela")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Position changes (flips)
    ax = axes[1][1]
    if sg_results:
        ax.plot([r["window"] for r in sg_results],
                [r["pos_changes"] for r in sg_results],
                "o-", color="#2196F3", lw=2, markersize=6, label="SavGol")
    if raw_results:
        ax.plot([r["window"] for r in raw_results],
                [r["pos_changes"] for r in raw_results],
                "s--", color="#FF9800", lw=2, markersize=6, label="Raw")
    ax.set_xlabel("Janela (barras)")
    ax.set_ylabel("Flips de Posicao")
    ax.set_title("Frequencia de Trading vs Janela")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.suptitle(f"Grid de Janelas — {dataset_label}", fontsize=14, fontweight="bold")
    plt.tight_layout()
    _save(fig, f"grid_metrics_{suffix}.png")

    # --- 2. Heatmap Sharpe (janela x modo) ---
    fig, ax = plt.subplots(figsize=(14, 5))
    modes = ["SavGol", "Raw"]
    windows = RET_WINDOWS
    data = np.zeros((len(modes), len(windows)))
    for r in results:
        row = 0 if r["savgol"] else 1
        col = windows.index(r["window"])
        data[row, col] = r["sharpe_all"]

    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=-0.05, vmax=0.20)
    ax.set_xticks(range(len(windows)))
    ax.set_xticklabels([str(w) for w in windows])
    ax.set_yticks(range(len(modes)))
    ax.set_yticklabels(modes)
    ax.set_xlabel("Janela de Retorno (barras)")
    ax.set_title(f"Heatmap Sharpe — {dataset_label}")

    # Anotar valores
    for i in range(len(modes)):
        for j in range(len(windows)):
            val = data[i, j]
            color = "white" if abs(val) > 0.10 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=9, fontweight="bold", color=color)

    fig.colorbar(im, ax=ax, label="Sharpe Ratio")
    plt.tight_layout()
    _save(fig, f"grid_heatmap_sharpe_{suffix}.png")

    # --- 3. Heatmap WF% ---
    fig, ax = plt.subplots(figsize=(14, 5))
    data_wf = np.zeros((len(modes), len(windows)))
    for r in results:
        row = 0 if r["savgol"] else 1
        col = windows.index(r["window"])
        data_wf[row, col] = r["wf_pct_positive"]

    im = ax.imshow(data_wf, cmap="RdYlGn", aspect="auto", vmin=30, vmax=100)
    ax.set_xticks(range(len(windows)))
    ax.set_xticklabels([str(w) for w in windows])
    ax.set_yticks(range(len(modes)))
    ax.set_yticklabels(modes)
    ax.set_xlabel("Janela de Retorno (barras)")
    ax.set_title(f"Heatmap Walk-Forward % Positivo — {dataset_label}")

    for i in range(len(modes)):
        for j in range(len(windows)):
            val = data_wf[i, j]
            color = "white" if val < 50 else "black"
            ax.text(j, i, f"{val:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight="bold", color=color)

    fig.colorbar(im, ax=ax, label="% Janelas Positivas")
    plt.tight_layout()
    _save(fig, f"grid_heatmap_wf_{suffix}.png")

    # --- 4. Heatmap Score composto ---
    fig, ax = plt.subplots(figsize=(14, 5))
    data_score = np.zeros((len(modes), len(windows)))
    for r in results:
        row = 0 if r["savgol"] else 1
        col = windows.index(r["window"])
        data_score[row, col] = r.get("score", 0)

    im = ax.imshow(data_score, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(windows)))
    ax.set_xticklabels([str(w) for w in windows])
    ax.set_yticks(range(len(modes)))
    ax.set_yticklabels(modes)
    ax.set_xlabel("Janela de Retorno (barras)")
    ax.set_title(f"Heatmap Score Composto (SR x WF% x DD) — {dataset_label}")

    for i in range(len(modes)):
        for j in range(len(windows)):
            val = data_score[i, j]
            color = "white" if abs(val) > 0.05 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=9, fontweight="bold", color=color)

    fig.colorbar(im, ax=ax, label="Score")
    plt.tight_layout()
    _save(fig, f"grid_heatmap_score_{suffix}.png")

    # --- 5. Equity curves top 5 ---
    ranked = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    top5 = ranked[:5]

    fig, ax = plt.subplots(figsize=(14, 7))
    ts = pd.to_datetime(bars["timestamp"]) if "bars" in dir() else None
    colors = ["#2196F3", "#FF9800", "#4CAF50", "#9C27B0", "#F44336"]
    for idx, r in enumerate(top5):
        ax.plot(r["equity"],
                label=f"{r['label']} (SR={r['sharpe_all']:.3f}, Ret={r['total_ret']:+.1%})",
                lw=1.2, color=colors[idx])

    # BTC B&H
    bh_equity = np.cumprod(1 + np.diff(
        results[0]["equity"] / results[0]["equity"],  # dummy
        prepend=0
    ))
    # Use first result's BTC return
    close = None
    ax.axhline(1.0, color="black", lw=0.5, ls=":")
    ax.set_xlabel("Barra (indice)")
    ax.set_ylabel("Equity (base 1.0)")
    ax.set_title(f"Top 5 Janelas — Equity Curves | {dataset_label}")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, f"grid_top5_equity_{suffix}.png")

    return ranked


def plot_grid_with_bars(results: list[dict], bars: pd.DataFrame,
                        dataset_label: str, suffix: str):
    """Equity curves top 5 com timestamps e BTC B&H."""
    ranked = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    top5 = ranked[:5]

    ts = pd.to_datetime(bars["timestamp"])
    close = bars["close"].values.astype(np.float64)
    bh_equity = close / close[0]

    fig, ax = plt.subplots(figsize=(14, 7))
    colors = ["#2196F3", "#FF9800", "#4CAF50", "#9C27B0", "#F44336"]
    for idx, r in enumerate(top5):
        ax.plot(ts, r["equity"],
                label=f"{r['label']} (SR={r['sharpe_all']:.3f}, {r['total_ret']:+.1%})",
                lw=1.2, color=colors[idx])
    ax.plot(ts, bh_equity,
            label=f"BTC B&H ({(bh_equity[-1]-1)*100:+.1f}%)",
            lw=1.2, color="gray", ls="--")
    ax.axhline(1.0, color="black", lw=0.5, ls=":")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.set_xlabel("Data")
    ax.set_ylabel("Equity (base 1.0)")
    ax.set_title(f"Top 5 Janelas — Portfolio Equity | {dataset_label}")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.3)

    # Max drawdown info
    txt_lines = []
    for i, r in enumerate(top5):
        txt_lines.append(f"{i+1}. {r['label']}: DD={r['max_dd']*100:.1f}%, "
                         f"WF={r['wf_pct_positive']:.0f}%")
    txt = "\n".join(txt_lines)
    ax.text(0.02, 0.05, txt, transform=ax.transAxes, fontsize=8,
            verticalalignment="bottom", family="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

    plt.tight_layout()
    _save(fig, f"grid_top5_portfolio_{suffix}.png")


# ═══════════════════════════════════════════════════════════════════
# SALVAR REPORT
# ═══════════════════════════════════════════════════════════════════
def save_grid_report(ranked_train: list[dict], ranked_oos: list[dict] | None):
    lines = []
    lines.append("MOMENTUM GRID SEARCH REPORT")
    lines.append("=" * 60)
    lines.append(f"  Janelas testadas: {RET_WINDOWS}")
    lines.append(f"  Modos: SavGol + Raw")
    lines.append(f"  Fees: {FEE_TAKER*100:.4f}% taker | mode = {FEE_MODE}")
    lines.append(f"  Walk-forward: {WF_WINDOW_BARS} barras/janela")
    lines.append("")

    lines.append("  RANKING IN-SAMPLE (treino ~4.5 anos)")
    lines.append("  " + "-" * 50)
    for i, r in enumerate(ranked_train[:10]):
        lines.append(f"    {i+1:>2}. {r['label']:>12} | SR={r['sharpe_all']:+.4f} | "
                     f"WF={r['wf_pct_positive']:.0f}% | DD={r['max_dd']*100:.1f}% | "
                     f"Ret={r['total_ret']:+.2%} | Score={r.get('score',0):.4f}")
    lines.append("")

    if ranked_oos:
        lines.append("  RANKING OOS (bear market ~7 meses)")
        lines.append("  " + "-" * 50)
        for i, r in enumerate(ranked_oos[:10]):
            lines.append(f"    {i+1:>2}. {r['label']:>12} | SR={r['sharpe_all']:+.4f} | "
                         f"WF={r['wf_pct_positive']:.0f}% | DD={r['max_dd']*100:.1f}% | "
                         f"Ret={r['total_ret']:+.2%} | Score={r.get('score',0):.4f}")
        lines.append("")

        # Consistencia: janelas que estao no top 5 em ambos
        top5_train = {r["label"] for r in ranked_train[:5]}
        top5_oos = {r["label"] for r in ranked_oos[:5]}
        consistent = top5_train & top5_oos
        lines.append("  CONSISTENCIA IN-SAMPLE vs OOS")
        lines.append("  " + "-" * 50)
        lines.append(f"    Top 5 treino: {sorted(top5_train)}")
        lines.append(f"    Top 5 OOS:    {sorted(top5_oos)}")
        if consistent:
            lines.append(f"    Consistentes: {sorted(consistent)}")
            lines.append(f"    >>> {len(consistent)} janela(s) no top 5 em AMBOS datasets")
        else:
            lines.append(f"    >>> NENHUMA janela consistente no top 5 — risco de overfitting!")
        lines.append("")

        # Correlacao de ranking
        train_labels = [r["label"] for r in ranked_train]
        oos_labels = [r["label"] for r in ranked_oos]
        # Rank de cada label no OOS
        train_ranks = {r["label"]: i for i, r in enumerate(ranked_train)}
        oos_ranks = {r["label"]: i for i, r in enumerate(ranked_oos)}
        common = set(train_ranks.keys()) & set(oos_ranks.keys())
        if len(common) > 2:
            from scipy.stats import spearmanr
            t_r = [train_ranks[k] for k in sorted(common)]
            o_r = [oos_ranks[k] for k in sorted(common)]
            rho, p_rho = spearmanr(t_r, o_r)
            lines.append(f"    Spearman rho (ranking): {rho:.3f} (p={p_rho:.4f})")
            if rho > 0.5 and p_rho < 0.05:
                lines.append(f"    >>> Rankings CORRELACIONADOS — janelas otimas sao estaveis")
            elif rho > 0:
                lines.append(f"    >>> Correlacao positiva fraca — alguma estabilidade")
            else:
                lines.append(f"    >>> Sem correlacao — ranking instavel entre datasets")

    path = os.path.join(SAVE_DIR, "grid_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  Relatorio salvo em {path}")
    print("\n" + "\n".join(lines))


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    global SAVE_DIR
    SAVE_DIR = os.path.join(script_dir, SAVE_DIR)
    os.makedirs(SAVE_DIR, exist_ok=True)

    print("MOMENTUM GRID SEARCH")
    print("=" * 60)

    # --- Dataset treino ---
    train_path = os.path.join(script_dir, DATA_DIR, "btcusdt_1m.csv")
    print(f"\n[1] DATASET TREINO")
    print(f"    {train_path}")
    btc_train = pd.read_csv(train_path, parse_dates=["timestamp"])
    print(f"    Linhas: {len(btc_train):,}")
    print("    Construindo dollar bars...")
    bars_train = build_dollar_bars(btc_train)

    results_train = run_grid(bars_train, "Treino (4.5 anos)")
    ranked_train = print_ranking(results_train, "Treino (4.5 anos)")
    plot_grid(results_train, "Treino (4.5 anos)", "train")
    plot_grid_with_bars(results_train, bars_train, "Treino (4.5 anos)", "train")

    # --- Dataset OOS ---
    oos_path = os.path.join(script_dir, NEW_DATA_DIR, "btcusdt_1m.csv")
    ranked_oos = None
    if os.path.exists(oos_path):
        print(f"\n[2] DATASET OOS")
        print(f"    {oos_path}")
        btc_oos = pd.read_csv(oos_path, parse_dates=["timestamp"])
        print(f"    Linhas: {len(btc_oos):,}")
        print("    Construindo dollar bars...")
        bars_oos = build_dollar_bars(btc_oos)

        results_oos = run_grid(bars_oos, "OOS Bear (ago/2025-mar/2026)")
        ranked_oos = print_ranking(results_oos, "OOS Bear (ago/2025-mar/2026)")
        plot_grid(results_oos, "OOS Bear (ago/2025-mar/2026)", "oos")
        plot_grid_with_bars(results_oos, bars_oos, "OOS Bear (ago/2025-mar/2026)", "oos")
    else:
        print(f"\n  [AVISO] {oos_path} nao encontrado, pulando OOS")

    # Relatorio consolidado
    save_grid_report(ranked_train, ranked_oos)


if __name__ == "__main__":
    main()
