"""
Momentum Grid 2D — ret_window x savgol_window
===============================================

Grid bidimensional: janela de retorno (5-80) x janela SavGol (5-80).
SavGol window deve ser impar; pares sao ajustados para impar-1.
Inclui raw (savgol_window=0) como baseline.

Produz heatmaps de Sharpe, WF%, MaxDD e Score para treino e OOS.

Uso:
  python momentum_grid2d.py
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

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACAO
# ═══════════════════════════════════════════════════════════════════
DATA_DIR = "../data"
NEW_DATA_DIR = "../new_data"
SAVE_DIR = "save_point_grid2d"

DOLLAR_BARS_PER_DAY = 10
CALIBRATION_DAYS = 30

SAVGOL_POLYORDER = 3

FEE_TAKER = 0.0270 / 100
FEE_MODE = "pessimistic"

# Grid de janelas (inteiros 5-80)
RET_WINDOWS = list(range(5, 81))
# SavGol windows: 0 = raw, depois impares de 5 a 79
SG_WINDOWS = [0] + list(range(5, 80, 2))  # 0,5,7,9,...,79

# Walk-forward
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
    thresholds_arr = np.arange(1, n_bars_max + 1) * threshold
    boundary_indices = np.searchsorted(cum_dollar, thresholds_arr, side="right")
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


def compute_strategy_returns(predictions, actual_returns, fee_taker=0.0, fee_mode="pessimistic"):
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


def sharpe(returns):
    if len(returns) < 2 or np.std(returns) == 0:
        return 0.0
    return np.mean(returns) / np.std(returns)


def _save(fig, name):
    path = os.path.join(SAVE_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"    Plot salvo: {path}")


# ═══════════════════════════════════════════════════════════════════
# AVALIAR UMA COMBINACAO (ret_window, sg_window)
# ═══════════════════════════════════════════════════════════════════
def evaluate_combo(close: np.ndarray, actual_ret: np.ndarray,
                   ret_window: int, sg_window: int, n_bars: int) -> dict:
    """Avalia sign(ret_N) com SavGol(sg_window) ou raw (sg_window=0)."""
    if sg_window > 0:
        close_f = savgol_causal(close, sg_window, SAVGOL_POLYORDER)
    else:
        close_f = close.copy()

    ret_n = pd.Series(close_f).pct_change(ret_window).values
    predictions = np.sign(ret_n)
    predictions = np.nan_to_num(predictions, nan=0.0)

    strat_ret = compute_strategy_returns(predictions, actual_ret, FEE_TAKER, FEE_MODE)

    equity = np.cumprod(1 + strat_ret)
    total_ret = equity[-1] - 1

    # Max drawdown
    running_max = np.maximum.accumulate(equity)
    drawdowns = (equity - running_max) / running_max
    max_dd = drawdowns.min()

    sr_all = sharpe(strat_ret)

    # Position changes
    pos_changes = int(np.sum(np.diff(predictions) != 0))

    # Walk-forward
    warmup = ret_window + (sg_window if sg_window > 0 else 0)
    wf_positive = 0
    wf_total = 0
    start = warmup
    while start + WF_WINDOW_BARS <= n_bars:
        end = start + WF_WINDOW_BARS
        pred_w = predictions[start:end]
        ret_w = compute_strategy_returns(pred_w, actual_ret[start:end], FEE_TAKER, FEE_MODE)
        if sharpe(ret_w) > 0:
            wf_positive += 1
        wf_total += 1
        start = end

    wf_pct = wf_positive / max(wf_total, 1) * 100

    return {
        "ret_w": ret_window,
        "sg_w": sg_window,
        "sharpe": sr_all,
        "total_ret": total_ret,
        "max_dd": max_dd,
        "wf_pct": wf_pct,
        "flips": pos_changes,
        "score": sr_all * (wf_pct / 100) * (1 + max_dd),
    }


# ═══════════════════════════════════════════════════════════════════
# RODAR GRID 2D
# ═══════════════════════════════════════════════════════════════════
def run_grid_2d(bars: pd.DataFrame, label: str):
    """Roda grid ret_window x sg_window."""
    close = bars["close"].values.astype(np.float64)
    actual_ret = np.diff(close, prepend=close[0]) / np.maximum(close, 1e-12)
    n_bars = len(bars)

    total_combos = len(RET_WINDOWS) * len(SG_WINDOWS)
    print(f"\n  Grid: {len(RET_WINDOWS)} ret x {len(SG_WINDOWS)} sg = {total_combos} combinacoes")

    # Pre-computar todas as series filtradas
    print("  Pre-computando series SavGol...")
    filtered_cache = {}
    filtered_cache[0] = close.copy()
    for sg_w in SG_WINDOWS:
        if sg_w > 0:
            filtered_cache[sg_w] = savgol_causal(close, sg_w, SAVGOL_POLYORDER)
    print(f"  Cache: {len(filtered_cache)} series")

    results = []
    done = 0
    for sg_w in SG_WINDOWS:
        close_f = filtered_cache[sg_w]
        for ret_w in RET_WINDOWS:
            # Skip se sg_window > 0 e nao e impar (ja garantido pelo range)
            # Skip se ret_window precisa de mais warmup que dados disponiveis
            warmup = ret_w + (sg_w if sg_w > 0 else 0)
            if warmup >= n_bars - WF_WINDOW_BARS:
                results.append({
                    "ret_w": ret_w, "sg_w": sg_w,
                    "sharpe": np.nan, "total_ret": np.nan,
                    "max_dd": np.nan, "wf_pct": np.nan,
                    "flips": 0, "score": np.nan,
                })
                done += 1
                continue

            # Computar inline (mais rapido que chamar evaluate_combo)
            ret_n = pd.Series(close_f).pct_change(ret_w).values
            predictions = np.sign(ret_n)
            predictions = np.nan_to_num(predictions, nan=0.0)

            strat_ret = compute_strategy_returns(predictions, actual_ret, FEE_TAKER, FEE_MODE)
            equity = np.cumprod(1 + strat_ret)

            running_max = np.maximum.accumulate(equity)
            dd = (equity - running_max) / running_max
            max_dd = dd.min()

            sr = sharpe(strat_ret)
            flips = int(np.sum(np.diff(predictions) != 0))

            # Walk-forward rapido
            wf_pos = 0
            wf_tot = 0
            s = warmup
            while s + WF_WINDOW_BARS <= n_bars:
                e = s + WF_WINDOW_BARS
                pred_w = predictions[s:e]
                ret_w_arr = compute_strategy_returns(pred_w, actual_ret[s:e], FEE_TAKER, FEE_MODE)
                if sharpe(ret_w_arr) > 0:
                    wf_pos += 1
                wf_tot += 1
                s = e

            wf_pct = wf_pos / max(wf_tot, 1) * 100

            results.append({
                "ret_w": ret_w, "sg_w": sg_w,
                "sharpe": sr, "total_ret": equity[-1] - 1,
                "max_dd": max_dd, "wf_pct": wf_pct,
                "flips": flips,
                "score": sr * (wf_pct / 100) * (1 + max_dd),
            })

            done += 1
            if done % 200 == 0:
                print(f"    {done}/{total_combos} ({done/total_combos*100:.0f}%)")

    print(f"  Grid completo: {done} combinacoes avaliadas")
    return results


# ═══════════════════════════════════════════════════════════════════
# CONSTRUIR MATRIZES PARA HEATMAP
# ═══════════════════════════════════════════════════════════════════
def build_matrix(results, metric):
    """Constroi matriz [sg_window x ret_window] para uma metrica."""
    mat = np.full((len(SG_WINDOWS), len(RET_WINDOWS)), np.nan)
    sg_idx = {w: i for i, w in enumerate(SG_WINDOWS)}
    ret_idx = {w: i for i, w in enumerate(RET_WINDOWS)}
    for r in results:
        si = sg_idx.get(r["sg_w"])
        ri = ret_idx.get(r["ret_w"])
        if si is not None and ri is not None:
            mat[si, ri] = r[metric]
    return mat


# ═══════════════════════════════════════════════════════════════════
# HEATMAPS
# ═══════════════════════════════════════════════════════════════════
def plot_heatmap(mat, title, cmap, vmin, vmax, suffix, fname,
                 fmt=".3f", label=""):
    """Heatmap generico [sg_window x ret_window]."""
    fig, ax = plt.subplots(figsize=(22, 12))

    # Labels para eixos
    ret_labels = [str(w) for w in RET_WINDOWS]
    sg_labels = ["raw" if w == 0 else str(w) for w in SG_WINDOWS]

    im = ax.imshow(mat, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax,
                   interpolation="nearest")

    ax.set_xticks(range(len(RET_WINDOWS)))
    ax.set_xticklabels(ret_labels, fontsize=6, rotation=90)
    ax.set_yticks(range(len(SG_WINDOWS)))
    ax.set_yticklabels(sg_labels, fontsize=7)

    ax.set_xlabel("Janela de Retorno (barras)", fontsize=11)
    ax.set_ylabel("Janela SavGol (0=raw)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")

    fig.colorbar(im, ax=ax, label=label, shrink=0.8)
    plt.tight_layout()
    _save(fig, fname)


def plot_heatmap_annotated(mat, title, cmap, vmin, vmax, suffix, fname,
                           fmt=".2f", label="", step_x=5, step_y=2):
    """Heatmap com anotacoes esparsas para legibilidade."""
    fig, ax = plt.subplots(figsize=(22, 12))

    ret_labels = [str(w) if (i % step_x == 0) else "" for i, w in enumerate(RET_WINDOWS)]
    sg_labels = ["raw" if w == 0 else (str(w) if i % step_y == 0 else "")
                 for i, w in enumerate(SG_WINDOWS)]

    im = ax.imshow(mat, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax,
                   interpolation="nearest")

    ax.set_xticks(range(len(RET_WINDOWS)))
    ax.set_xticklabels(ret_labels, fontsize=7, rotation=90)
    ax.set_yticks(range(len(SG_WINDOWS)))
    ax.set_yticklabels(sg_labels, fontsize=7)

    ax.set_xlabel("Janela de Retorno (barras)", fontsize=11)
    ax.set_ylabel("Janela SavGol (0=raw)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")

    fig.colorbar(im, ax=ax, label=label, shrink=0.8)
    plt.tight_layout()
    _save(fig, fname)


# ═══════════════════════════════════════════════════════════════════
# TOP N e RELATORIO
# ═══════════════════════════════════════════════════════════════════
def print_top(results, label, n=20):
    """Imprime top N combinacoes."""
    valid = [r for r in results if not np.isnan(r.get("sharpe", np.nan))]
    ranked = sorted(valid, key=lambda x: x.get("score", -999), reverse=True)

    print(f"\n{'='*90}")
    print(f"  TOP {n} — {label}")
    print(f"{'='*90}")
    print(f"  {'#':>3} {'ret':>4} {'sg':>4} {'SR':>8} {'WF%':>6} {'MaxDD':>8} {'Flips':>6} {'Score':>8}")
    print(f"  {'-'*50}")

    for i, r in enumerate(ranked[:n]):
        sg_str = "raw" if r["sg_w"] == 0 else str(r["sg_w"])
        print(f"  {i+1:>3} {r['ret_w']:>4} {sg_str:>4} "
              f"{r['sharpe']:>+8.4f} {r['wf_pct']:>5.0f}% "
              f"{r['max_dd']*100:>+7.1f}% {r['flips']:>6} {r['score']:>8.4f}")

    return ranked


def save_report(ranked_train, ranked_oos):
    lines = []
    lines.append("MOMENTUM GRID 2D REPORT — ret_window x savgol_window")
    lines.append("=" * 70)
    lines.append(f"  ret_windows: {RET_WINDOWS[0]}-{RET_WINDOWS[-1]} ({len(RET_WINDOWS)} valores)")
    lines.append(f"  sg_windows: raw + impares {SG_WINDOWS[1]}-{SG_WINDOWS[-1]} ({len(SG_WINDOWS)} valores)")
    lines.append(f"  Total combinacoes: {len(RET_WINDOWS) * len(SG_WINDOWS)}")
    lines.append(f"  Fees: {FEE_TAKER*100:.4f}% taker | mode = {FEE_MODE}")
    lines.append("")

    for tag, ranked in [("IN-SAMPLE (treino)", ranked_train),
                        ("OOS (bear)", ranked_oos)]:
        if ranked is None:
            continue
        lines.append(f"  TOP 15 — {tag}")
        lines.append(f"  {'-'*60}")
        for i, r in enumerate(ranked[:15]):
            sg_str = "raw" if r["sg_w"] == 0 else f"sg={r['sg_w']}"
            lines.append(
                f"    {i+1:>2}. ret={r['ret_w']:>2}, {sg_str:>6} | "
                f"SR={r['sharpe']:+.4f} | WF={r['wf_pct']:.0f}% | "
                f"DD={r['max_dd']*100:.1f}% | Score={r['score']:.4f}"
            )
        lines.append("")

    # Consistencia
    if ranked_oos:
        top10_train = {(r["ret_w"], r["sg_w"]) for r in ranked_train[:10]}
        top10_oos = {(r["ret_w"], r["sg_w"]) for r in ranked_oos[:10]}
        consistent = top10_train & top10_oos
        lines.append("  CONSISTENCIA top-10 treino vs OOS")
        lines.append(f"    Combinacoes consistentes: {len(consistent)}")
        for c in sorted(consistent):
            sg_str = "raw" if c[1] == 0 else f"sg={c[1]}"
            lines.append(f"      ret={c[0]}, {sg_str}")

        # Zona otima: combinacoes com score > percentil 90 em AMBOS
        train_scores = [r["score"] for r in ranked_train if not np.isnan(r["score"])]
        oos_scores = [r["score"] for r in ranked_oos if not np.isnan(r["score"])]
        p90_train = np.percentile(train_scores, 90)
        p90_oos = np.percentile(oos_scores, 90)

        train_top = {(r["ret_w"], r["sg_w"]) for r in ranked_train
                     if r["score"] >= p90_train}
        oos_top = {(r["ret_w"], r["sg_w"]) for r in ranked_oos
                   if r["score"] >= p90_oos}
        robust_zone = train_top & oos_top

        lines.append(f"\n  ZONA ROBUSTA (score > P90 em AMBOS datasets)")
        lines.append(f"    P90 treino: {p90_train:.4f} | P90 OOS: {p90_oos:.4f}")
        lines.append(f"    Combinacoes robustas: {len(robust_zone)}")
        if robust_zone:
            ret_vals = sorted(set(c[0] for c in robust_zone))
            sg_vals = sorted(set(c[1] for c in robust_zone))
            lines.append(f"    ret range: {min(ret_vals)}-{max(ret_vals)}")
            sg_raw = [c for c in robust_zone if c[1] == 0]
            sg_filtered = [c for c in robust_zone if c[1] > 0]
            if sg_raw:
                lines.append(f"    Raw: {len(sg_raw)} combinacoes "
                             f"(ret={sorted(c[0] for c in sg_raw)})")
            if sg_filtered:
                sg_range = sorted(set(c[1] for c in sg_filtered))
                lines.append(f"    Filtered: {len(sg_filtered)} combinacoes "
                             f"(sg={sg_range[0]}-{sg_range[-1]})")

    path = os.path.join(SAVE_DIR, "grid2d_report.txt")
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

    print("MOMENTUM GRID 2D — ret_window x savgol_window")
    print("=" * 60)

    ranked_train = None
    ranked_oos = None

    # --- Treino ---
    train_path = os.path.join(script_dir, DATA_DIR, "btcusdt_1m.csv")
    print(f"\n[1] TREINO: {train_path}")
    btc_train = pd.read_csv(train_path, parse_dates=["timestamp"])
    print(f"  Linhas: {len(btc_train):,}")
    bars_train = build_dollar_bars(btc_train)

    results_train = run_grid_2d(bars_train, "Treino")
    ranked_train = print_top(results_train, "Treino (4.5 anos)")

    # Heatmaps treino
    for metric, title, cmap, vmin, vmax, lbl in [
        ("sharpe", "Sharpe Ratio", "RdYlGn", -0.10, 0.50, "Sharpe"),
        ("wf_pct", "Walk-Forward % Positivo", "RdYlGn", 0, 100, "WF%"),
        ("max_dd", "Max Drawdown", "RdYlGn_r", -1.0, 0, "MaxDD"),
        ("score", "Score Composto (SR x WF% x DD)", "RdYlGn", -0.05, 0.50, "Score"),
    ]:
        mat = build_matrix(results_train, metric)
        plot_heatmap_annotated(mat, f"{title} — Treino", cmap, vmin, vmax,
                               "train", f"heatmap_{metric}_train.png", label=lbl)

    # --- OOS ---
    oos_path = os.path.join(script_dir, NEW_DATA_DIR, "btcusdt_1m.csv")
    if os.path.exists(oos_path):
        print(f"\n[2] OOS: {oos_path}")
        btc_oos = pd.read_csv(oos_path, parse_dates=["timestamp"])
        print(f"  Linhas: {len(btc_oos):,}")
        bars_oos = build_dollar_bars(btc_oos)

        results_oos = run_grid_2d(bars_oos, "OOS")
        ranked_oos = print_top(results_oos, "OOS Bear (ago/2025-mar/2026)")

        for metric, title, cmap, vmin, vmax, lbl in [
            ("sharpe", "Sharpe Ratio", "RdYlGn", -0.10, 0.50, "Sharpe"),
            ("wf_pct", "Walk-Forward % Positivo", "RdYlGn", 0, 100, "WF%"),
            ("max_dd", "Max Drawdown", "RdYlGn_r", -1.0, 0, "MaxDD"),
            ("score", "Score Composto (SR x WF% x DD)", "RdYlGn", -0.05, 0.50, "Score"),
        ]:
            mat = build_matrix(results_oos, metric)
            plot_heatmap_annotated(mat, f"{title} — OOS Bear", cmap, vmin, vmax,
                                   "oos", f"heatmap_{metric}_oos.png", label=lbl)

        # Heatmap de CONSISTENCIA (min do score treino vs oos)
        mat_train = build_matrix(results_train, "score")
        mat_oos = build_matrix(results_oos, "score")
        mat_consist = np.minimum(
            np.nan_to_num(mat_train, nan=-999),
            np.nan_to_num(mat_oos, nan=-999)
        )
        mat_consist[mat_consist <= -999] = np.nan
        plot_heatmap_annotated(mat_consist,
                               "Score Consistente (min treino, OOS)",
                               "RdYlGn", -0.05, 0.30, "consist",
                               "heatmap_score_consistent.png",
                               label="min(Score)")
    else:
        print(f"\n  [AVISO] {oos_path} nao encontrado")

    save_report(ranked_train, ranked_oos)


if __name__ == "__main__":
    main()
