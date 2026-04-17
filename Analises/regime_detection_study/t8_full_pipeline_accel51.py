#!/usr/bin/env python3
# coding: utf-8
"""
=============================================================================
T8 Full Pipeline Null Model — sg_acceleration_51 Variant
=============================================================================

Same as t8_full_pipeline.py, but REPLACES sg_velocity_51 with sg_acceleration_51
(SavGol analytical 2nd derivative at scale 51).

Hypothesis: acceleration (2nd derivative) is an even WEAKER artifact than
velocity (1st derivative). If velocity at scale 51 was weak enough to allow
genuine features to shine (GENUINE, p=0.000), acceleration should be at least
as good — potentially better, since it captures curvature (regime transitions)
rather than direction.

sg_acceleration_51 was removed 2026-03-25 as ARTIFACT by feature_null_model.py,
but the full pipeline test showed that weak artifacts can produce GENUINE alpha
in combination with genuine features (tstat, volatility).

Output: relatorios/t8_full_pipeline_accel51.md + relatorios/pngs/t8fp_accel51_*.png
"""

import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as sp_stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

from utils.savgol import savgol_causal, savgol_causal_deriv
from regime_detection_advanced import (
    DollarBarBuilder,
    TripleBarrierLabeler,
    MetaLabeler,
    ModelEvaluator,
    FeatureRegistry,
    CPCV,
    DEFAULT_CONFIG,
    LIMITE_DECISORIO,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ==========================================================================
# CONFIG
# ==========================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
REPORT_DIR = os.path.join(SCRIPT_DIR, "relatorios")
PNG_DIR = os.path.join(REPORT_DIR, "pngs")
os.makedirs(PNG_DIR, exist_ok=True)

N_SIMULATIONS = 30

# Same features as real model, but REPLACING sg_velocity_51 with sg_acceleration_51
SELECTED_FEATURES = [
    "sg_acceleration_51", "tstat_50", "volatility_20", "volatility_50",
    "tstat_20", "ffd_close", "tstat_10", "btc_dxy_spread", "volatility_10",
]

SG_POLY = DEFAULT_CONFIG["savgol_polyorder"]  # 3


# ==========================================================================
# DATA LOADING (same as main pipeline)
# ==========================================================================
def load_data():
    """Load BTC 1-min data + optional auxiliary data."""
    path = os.path.join(DATA_DIR, "btcusdt_1m.csv")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    print(f"  BTC 1-min: {df.shape}")
    return df


def build_dollar_bars(df_1m):
    """Build dollar bars using same config as main pipeline."""
    builder = DollarBarBuilder(
        calibration_days=DEFAULT_CONFIG["dollar_bar_calibration_days"],
        bars_per_day=DEFAULT_CONFIG["dollar_bars_per_day"],
    )
    bars = builder.transform(df_1m)
    threshold = builder.threshold
    print(f"  Dollar bars: {len(bars)}, threshold: ${threshold:,.0f}")
    return bars, threshold


# ==========================================================================
# SYNTHETIC PRICE GENERATION
# ==========================================================================
def generate_synthetic_bars(bars_real, mode="random_walk", seed=0):
    """
    Replace close/high/low with synthetic prices, keep real volume + structure.
    """
    rng = np.random.RandomState(seed)
    bars = bars_real.copy()

    close_real = bars["close"].values.astype(np.float64)
    high_real = bars["high"].values.astype(np.float64)
    low_real = bars["low"].values.astype(np.float64)
    n = len(close_real)

    bar_returns = pd.Series(close_real).pct_change().dropna().values
    sigma = np.std(bar_returns)

    if mode == "random_walk":
        syn_returns = sigma * rng.randn(n - 1)
    elif mode == "shuffled":
        syn_returns = bar_returns.copy()
        rng.shuffle(syn_returns)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    syn_close = np.cumprod(np.concatenate([[close_real[0]], 1 + syn_returns]))

    safe_close = np.where(close_real > 1e-12, close_real, 1.0)
    high_ratio = (high_real - close_real) / safe_close
    low_ratio = (close_real - low_real) / safe_close
    high_ratio = np.clip(high_ratio, 0, 0.05)
    low_ratio = np.clip(low_ratio, 0, 0.05)

    syn_high = syn_close * (1 + high_ratio)
    syn_low = syn_close * (1 - low_ratio)
    syn_open = np.concatenate([[syn_close[0]], syn_close[:-1]])

    bars["close"] = syn_close
    bars["high"] = syn_high
    bars["low"] = syn_low
    bars["open"] = syn_open

    return bars


# ==========================================================================
# FEATURE COMPUTATION (reuse FeatureRegistry + manual sg_acceleration_51)
# ==========================================================================
def compute_features(bars, config, verbose=False):
    """Compute all features using FeatureRegistry + manual sg_acceleration_51."""
    import io
    from contextlib import redirect_stdout

    registry = FeatureRegistry()
    registry.register_defaults()
    if verbose:
        df_feat, all_feature_names = registry.compute_all(bars.copy(), config)
    else:
        f_buf = io.StringIO()
        with redirect_stdout(f_buf):
            df_feat, all_feature_names = registry.compute_all(bars.copy(), config)

    # Manually compute sg_acceleration_51 (removed from FeatureRegistry)
    # Uses savgol_causal_deriv with deriv=2 (analytical 2nd derivative)
    close_raw = df_feat["close"].values.astype(np.float64)
    accel_51 = savgol_causal_deriv(close_raw, 51, SG_POLY, deriv=2)

    # Normalize: divide by price (scale-invariant) and by vol_50 (z-score-like)
    price_safe = np.where(close_raw > 1e-12, close_raw, np.nan)
    accel_51_norm = accel_51 / price_safe

    ret_sg = pd.Series(
        savgol_causal(close_raw, DEFAULT_CONFIG.get("savgol_window", 21), SG_POLY),
        index=df_feat.index,
    ).pct_change()
    vol_50 = ret_sg.rolling(50, min_periods=50).std().values
    vol_50_safe = np.where(vol_50 > 1e-12, vol_50, np.nan)

    df_feat["sg_acceleration_51"] = pd.Series(
        accel_51_norm / vol_50_safe, index=df_feat.index, name="sg_acceleration_51"
    )
    if "sg_acceleration_51" not in all_feature_names:
        all_feature_names.append("sg_acceleration_51")

    return df_feat, all_feature_names


# ==========================================================================
# SINGLE PIPELINE RUN (train meta-label, get test SR)
# ==========================================================================
def run_pipeline_once(bars, config, selected_features, verbose=False):
    """
    Run the core pipeline on given bars:
      1. Compute features
      2. Triple-barrier labeling
      3. 80/20 temporal split
      4. Train meta-label
      5. Return test set SR + metrics
    """
    df_feat, all_features = compute_features(bars, config, verbose=False)

    available = [f for f in selected_features if f in df_feat.columns]
    if len(available) < 2:
        return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                "accuracy": np.nan, "psr": np.nan}

    df_feat = df_feat.dropna(subset=available).reset_index(drop=True)

    if len(df_feat) < 200:
        return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                "accuracy": np.nan, "psr": np.nan}

    import io
    from contextlib import redirect_stdout

    labeler = TripleBarrierLabeler(config)
    f_buf = io.StringIO()
    with redirect_stdout(f_buf):
        df_labeled = labeler.apply_barriers(df_feat)

    if len(df_labeled) < 200:
        return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                "accuracy": np.nan, "psr": np.nan}

    feature_cols = [f for f in available if f in df_labeled.columns]
    X = df_labeled[feature_cols].values.astype(np.float64)
    y = df_labeled["label"].values.astype(int)
    close = df_labeled["close"].values.astype(np.float64)

    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    split_idx = int(len(X) * config.get("train_ratio", 0.80))
    if split_idx < 100 or (len(X) - split_idx) < 50:
        return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                "accuracy": np.nan, "psr": np.nan}

    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    close_test = close[split_idx:]

    meta = MetaLabeler(config)
    with redirect_stdout(f_buf):
        try:
            meta.fit(X_train, y_train)
            final_preds, meta_probs, primary_preds = meta.predict(X_test)
        except Exception:
            return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                    "accuracy": np.nan, "psr": np.nan}

    actual_ret = np.diff(close_test, prepend=close_test[0]) / np.maximum(
        close_test, 1e-12
    )
    strat_ret = ModelEvaluator.compute_strategy_returns(
        final_preds, actual_ret,
        fee_maker=config["fee_maker"],
        fee_taker=config["fee_taker"],
        fee_mode=config["fee_mode"],
    )

    sr = (np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)
          if len(strat_ret) > 1 else 0.0)
    psr = ModelEvaluator.probabilistic_sharpe_ratio(strat_ret)

    active_mask = final_preds != 0
    n_active = int(np.sum(active_mask))
    if n_active > 10:
        active_ret = strat_ret[active_mask]
        sr_active = (np.mean(active_ret) / max(np.std(active_ret, ddof=1), 1e-12)
                     if len(active_ret) > 1 else 0.0)
    else:
        sr_active = np.nan

    acc = accuracy_score(y_test, final_preds) if len(y_test) > 0 else np.nan

    return {
        "sr": sr,
        "sr_active": sr_active,
        "n_active": n_active,
        "n_test": len(y_test),
        "accuracy": acc,
        "psr": psr,
        "skewness": float(sp_stats.skew(strat_ret)) if len(strat_ret) > 2 else np.nan,
    }


# ==========================================================================
# MAIN
# ==========================================================================
def main():
    print("=" * 70)
    print("  T8 FULL PIPELINE NULL MODEL — sg_acceleration_51 Variant")
    print("=" * 70)
    t_start = time.time()

    # -- Load real data
    print("\n[1/5] Loading data...")
    df_1m = load_data()
    bars_real, threshold = build_dollar_bars(df_1m)

    # -- Run real pipeline
    print("\n[2/5] Running pipeline on REAL data...")
    registry = FeatureRegistry()
    registry.register_defaults()
    df_check, fnames_check = registry.compute_all(bars_real.copy(), DEFAULT_CONFIG)
    avail = [f for f in SELECTED_FEATURES if f in df_check.columns]
    print(f"  Available features from registry: {avail}")
    missing = [f for f in SELECTED_FEATURES if f not in df_check.columns]
    if missing:
        print(f"  Will compute manually: {[f for f in missing if 'accel' in f]}")
        print(f"  Missing (no external data): {[f for f in missing if 'accel' not in f]}")

    real_meta = run_pipeline_once(bars_real, DEFAULT_CONFIG, SELECTED_FEATURES,
                                 verbose=True)
    sr_real = real_meta["sr"]
    sr_active_real = real_meta["sr_active"]
    n_active_real = real_meta["n_active"]
    psr_real = real_meta["psr"]
    skew_real = real_meta.get("skewness", np.nan)

    print(f"  SR_real (all bars): {sr_real:.6f}")
    print(f"  SR_real (active):   {sr_active_real:.6f}")
    print(f"  N_active:           {n_active_real}")
    print(f"  PSR_real:           {psr_real:.4f}")
    print(f"  Skewness_real:      {skew_real:.4f}")

    sr_cpcv_real = 0.1211  # reference from save_point_advanced

    # -- Null Model A: Random Walk
    print(f"\n[3/5] Null Model A: Random Walk (drift=0), N={N_SIMULATIONS}...")
    sr_null_rw = []
    sr_active_null_rw = []
    n_active_null_rw = []
    skew_null_rw = []

    for i in range(N_SIMULATIONS):
        t0_sim = time.time()
        bars_syn = generate_synthetic_bars(bars_real, mode="random_walk", seed=i)
        res = run_pipeline_once(bars_syn, DEFAULT_CONFIG, SELECTED_FEATURES)
        sr_null_rw.append(res["sr"])
        sr_active_null_rw.append(res["sr_active"])
        n_active_null_rw.append(res["n_active"])
        skew_null_rw.append(res.get("skewness", np.nan))
        elapsed = time.time() - t0_sim
        print(f"\r  RW sim {i+1}/{N_SIMULATIONS}: SR={res['sr']:.4f}, "
              f"N_active={res['n_active']}, "
              f"time={elapsed:.1f}s", end="", flush=True)
    print()

    sr_null_rw = np.array(sr_null_rw)
    sr_null_rw_clean = sr_null_rw[~np.isnan(sr_null_rw)]

    # -- Null Model B: Shuffled Returns
    print(f"\n[4/5] Null Model B: Shuffled Returns, N={N_SIMULATIONS}...")
    sr_null_shuf = []
    sr_active_null_shuf = []
    n_active_null_shuf = []
    skew_null_shuf = []

    for i in range(N_SIMULATIONS):
        t0_sim = time.time()
        bars_syn = generate_synthetic_bars(bars_real, mode="shuffled",
                                           seed=i + 50000)
        res = run_pipeline_once(bars_syn, DEFAULT_CONFIG, SELECTED_FEATURES)
        sr_null_shuf.append(res["sr"])
        sr_active_null_shuf.append(res["sr_active"])
        n_active_null_shuf.append(res["n_active"])
        skew_null_shuf.append(res.get("skewness", np.nan))
        elapsed = time.time() - t0_sim
        print(f"\r  Shuf sim {i+1}/{N_SIMULATIONS}: SR={res['sr']:.4f}, "
              f"N_active={res['n_active']}, "
              f"time={elapsed:.1f}s", end="", flush=True)
    print()

    sr_null_shuf = np.array(sr_null_shuf)
    sr_null_shuf_clean = sr_null_shuf[~np.isnan(sr_null_shuf)]

    # -- Analysis
    print("\n[5/5] Analysis & Report...")

    pval_rw = (np.mean(sr_null_rw_clean >= sr_real)
               if len(sr_null_rw_clean) > 0 else 1.0)
    pval_shuf = (np.mean(sr_null_shuf_clean >= sr_real)
                 if len(sr_null_shuf_clean) > 0 else 1.0)

    if len(sr_null_rw_clean) > 0:
        p5_rw, p50_rw, p95_rw = np.percentile(sr_null_rw_clean, [5, 50, 95])
    else:
        p5_rw = p50_rw = p95_rw = np.nan

    if len(sr_null_shuf_clean) > 0:
        p5_shuf, p50_shuf, p95_shuf = np.percentile(sr_null_shuf_clean,
                                                      [5, 50, 95])
    else:
        p5_shuf = p50_shuf = p95_shuf = np.nan

    if pval_rw < 0.05 and pval_shuf < 0.05:
        verdict = "GENUINE"
    elif pval_rw < 0.05 or pval_shuf < 0.05:
        verdict = "MARGINAL"
    else:
        verdict = "ARTIFACT"

    sr_active_rw = np.array(sr_active_null_rw)
    sr_active_rw_clean = sr_active_rw[~np.isnan(sr_active_rw)]
    pval_active_rw = (np.mean(sr_active_rw_clean >= sr_active_real)
                      if len(sr_active_rw_clean) > 0 and not np.isnan(sr_active_real)
                      else 1.0)

    sr_active_shuf = np.array(sr_active_null_shuf)
    sr_active_shuf_clean = sr_active_shuf[~np.isnan(sr_active_shuf)]
    pval_active_shuf = (np.mean(sr_active_shuf_clean >= sr_active_real)
                        if len(sr_active_shuf_clean) > 0 and not np.isnan(sr_active_real)
                        else 1.0)

    n_active_rw_arr = np.array(n_active_null_rw)
    n_active_shuf_arr = np.array(n_active_null_shuf)

    elapsed_total = time.time() - t_start

    # -- Summary
    print(f"\n  {'='*60}")
    print(f"  T8 FULL PIPELINE ACCEL51 — RESULTS")
    print(f"  {'='*60}")
    print(f"  SR_real (meta-label, all bars):  {sr_real:.6f}")
    print(f"  SR_real (active trades only):    {sr_active_real:.6f}")
    print(f"")
    print(f"  Random Walk null (N={len(sr_null_rw_clean)}):")
    print(f"    Mean: {np.mean(sr_null_rw_clean):.6f} +/- {np.std(sr_null_rw_clean):.6f}")
    print(f"    P5/P50/P95: {p5_rw:.6f} / {p50_rw:.6f} / {p95_rw:.6f}")
    print(f"    p-value (SR_null >= SR_real): {pval_rw:.4f}")
    print(f"    p-value (active): {pval_active_rw:.4f}")
    print(f"")
    print(f"  Shuffled null (N={len(sr_null_shuf_clean)}):")
    print(f"    Mean: {np.mean(sr_null_shuf_clean):.6f} +/- {np.std(sr_null_shuf_clean):.6f}")
    print(f"    P5/P50/P95: {p5_shuf:.6f} / {p50_shuf:.6f} / {p95_shuf:.6f}")
    print(f"    p-value (SR_null >= SR_real): {pval_shuf:.4f}")
    print(f"    p-value (active): {pval_active_shuf:.4f}")
    print(f"")
    print(f"  VERDICT: **{verdict}**")
    print(f"  Time: {elapsed_total/60:.1f} min")

    # -- Plots

    # Plot 1: SR distributions
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    ax.hist(sr_null_rw_clean, bins=25, alpha=0.6, color="steelblue",
            edgecolor="white", label=f"RW null (N={len(sr_null_rw_clean)})")
    ax.axvline(sr_real, color="red", lw=2.5, ls="--",
               label=f"SR_real = {sr_real:.4f}")
    if len(sr_null_rw_clean) > 0:
        ax.axvline(p95_rw, color="orange", lw=1.5, ls=":",
                   label=f"P95 = {p95_rw:.4f}")
    ax.set_xlabel("Sharpe Ratio (meta-label, all bars)")
    ax.set_ylabel("Count")
    ax.set_title(f"Null A: Random Walk (drift=0)\np-value = {pval_rw:.4f}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.hist(sr_null_shuf_clean, bins=25, alpha=0.6, color="plum",
            edgecolor="white", label=f"Shuffled null (N={len(sr_null_shuf_clean)})")
    ax.axvline(sr_real, color="red", lw=2.5, ls="--",
               label=f"SR_real = {sr_real:.4f}")
    if len(sr_null_shuf_clean) > 0:
        ax.axvline(p95_shuf, color="orange", lw=1.5, ls=":",
                   label=f"P95 = {p95_shuf:.4f}")
    ax.set_xlabel("Sharpe Ratio (meta-label, all bars)")
    ax.set_ylabel("Count")
    ax.set_title(f"Null B: Shuffled Returns\np-value = {pval_shuf:.4f}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    verdict_color = {"GENUINE": "green", "MARGINAL": "goldenrod",
                     "ARTIFACT": "red"}
    fig.suptitle(
        f"T8 Full Pipeline Null Model (sg_acceleration_51) — Verdict: {verdict}\n"
        f"SR_real={sr_real:.4f} | N_sims={N_SIMULATIONS} | "
        f"Features: {len(SELECTED_FEATURES)}",
        fontsize=13, fontweight="bold",
        color=verdict_color.get(verdict, "black"),
    )
    plt.tight_layout()
    path1 = os.path.join(PNG_DIR, "t8fp_accel51_sr_distributions.png")
    plt.savefig(path1, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Plot: {path1}")

    # Plot 2: Active trades analysis
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    ax = axes[0]
    if len(sr_active_rw_clean) > 0:
        ax.hist(sr_active_rw_clean, bins=20, alpha=0.6, color="steelblue",
                edgecolor="white", label="RW null")
    if len(sr_active_shuf_clean) > 0:
        ax.hist(sr_active_shuf_clean, bins=20, alpha=0.5, color="plum",
                edgecolor="white", label="Shuffled null")
    if not np.isnan(sr_active_real):
        ax.axvline(sr_active_real, color="red", lw=2.5, ls="--",
                   label=f"SR_active_real = {sr_active_real:.4f}")
    ax.set_xlabel("SR (active trades only)")
    ax.set_title(f"Active Trades SR\np_rw={pval_active_rw:.3f}, "
                 f"p_shuf={pval_active_shuf:.3f}")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.hist(n_active_rw_arr, bins=20, alpha=0.6, color="steelblue",
            edgecolor="white", label="RW null")
    ax.hist(n_active_shuf_arr, bins=20, alpha=0.5, color="plum",
            edgecolor="white", label="Shuffled null")
    ax.axvline(n_active_real, color="red", lw=2.5, ls="--",
               label=f"N_active_real = {n_active_real}")
    ax.set_xlabel("N active trades")
    ax.set_title("Trade Frequency")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    skew_rw_arr = np.array(skew_null_rw)
    skew_shuf_arr = np.array(skew_null_shuf)
    skew_rw_clean = skew_rw_arr[~np.isnan(skew_rw_arr)]
    skew_shuf_clean = skew_shuf_arr[~np.isnan(skew_shuf_arr)]
    if len(skew_rw_clean) > 0:
        ax.hist(skew_rw_clean, bins=20, alpha=0.6, color="steelblue",
                edgecolor="white", label="RW null")
    if len(skew_shuf_clean) > 0:
        ax.hist(skew_shuf_clean, bins=20, alpha=0.5, color="plum",
                edgecolor="white", label="Shuffled null")
    if not np.isnan(skew_real):
        ax.axvline(skew_real, color="red", lw=2.5, ls="--",
                   label=f"Skew_real = {skew_real:.2f}")
    ax.set_xlabel("Skewness")
    ax.set_title("Return Skewness Distribution")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    fig.suptitle("T8 Full Pipeline (sg_acceleration_51) — Active Trades & Distribution",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    path2 = os.path.join(PNG_DIR, "t8fp_accel51_active_analysis.png")
    plt.savefig(path2, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot: {path2}")

    # Plot 3: Box plot comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    positions = [1, 2]
    bp = ax.boxplot([sr_null_rw_clean, sr_null_shuf_clean],
                    positions=positions, widths=0.4,
                    patch_artist=True,
                    boxprops=dict(facecolor="lightblue", alpha=0.7),
                    medianprops=dict(color="navy", lw=2))

    for pos, data in zip(positions, [sr_null_rw_clean, sr_null_shuf_clean]):
        jitter = 0.05 * np.random.randn(len(data))
        ax.scatter(pos + jitter, data, alpha=0.3, s=15, color="steelblue",
                   zorder=3)

    ax.axhline(sr_real, color="red", lw=2.5, ls="--",
               label=f"SR_real = {sr_real:.4f}", zorder=5)
    ax.set_xticks(positions)
    ax.set_xticklabels(["Random Walk\n(drift=0)",
                        "Shuffled\nReturns"])
    ax.set_ylabel("Sharpe Ratio")
    ax.set_title(f"T8 Full Pipeline (sg_acceleration_51): Real SR vs Null\n"
                 f"Verdict: {verdict} | "
                 f"p_rw={pval_rw:.4f}, p_shuf={pval_shuf:.4f}")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    path3 = os.path.join(PNG_DIR, "t8fp_accel51_boxplot.png")
    plt.savefig(path3, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot: {path3}")

    # -- Report
    report = f"""# T8 Full Pipeline Null Model — sg_acceleration_51 Variant

**Data:** 2026-03-26
**Objetivo:** Testar se o pipeline completo com **sg_acceleration_51** (2a derivada
SavGol, escala 51) substituindo sg_velocity_51 gera alpha genuino.

**Hipotese:** A aceleracao (2a derivada) e um artefato ainda mais fraco que a
velocidade (1a derivada). Se sg_velocity_51 foi fraca o suficiente para permitir
alpha genuino (T8 GENUINE, p=0.000), a aceleracao deve ser pelo menos tao boa.

---

## Metodologia

Para cada simulacao:
1. Substituir close/high/low dos dollar bars por precos sinteticos (random walk)
2. Preservar volume real e estrutura intra-bar (ratios high/low relativos ao close)
3. Computar as **mesmas 9 features** (sg_acceleration_51 no lugar de sg_velocity_51)
4. Aplicar triple-barrier labeling nos precos sinteticos
5. Treinar meta-label (80/20 split temporal) com **mesma config** do RF
6. Computar SR no test set

**Features testadas:** {', '.join(SELECTED_FEATURES)}
**N simulacoes:** {N_SIMULATIONS}
**Config RF:** {DEFAULT_CONFIG['rf_n_estimators']} trees, depth={DEFAULT_CONFIG['rf_max_depth']}, min_leaf={DEFAULT_CONFIG['rf_min_samples_leaf']}
**LIMITE_DECISORIO:** {LIMITE_DECISORIO}
**Fees:** taker={DEFAULT_CONFIG['fee_taker']*100:.4f}% (pessimistic mode)

---

## Resultados

### SR do Modelo Real

| Metrica | Valor |
|---------|-------|
| SR (meta-label, todas barras) | **{sr_real:.6f}** |
| SR (apenas trades ativos) | **{sr_active_real:.6f}** |
| N trades ativos (teste) | {n_active_real} |
| PSR | {psr_real:.4f} |
| Skewness | {skew_real:.4f} |

### Null Model A: Random Walk (drift=0)

| Metrica | Valor |
|---------|-------|
| N simulacoes validas | {len(sr_null_rw_clean)} |
| SR medio | {np.mean(sr_null_rw_clean):.6f} +/- {np.std(sr_null_rw_clean):.6f} |
| P5 / P50 / P95 | {p5_rw:.6f} / {p50_rw:.6f} / {p95_rw:.6f} |
| **p-value (todas barras)** | **{pval_rw:.4f}** |
| **p-value (active trades)** | **{pval_active_rw:.4f}** |
| N_active medio | {np.mean(n_active_rw_arr):.0f} +/- {np.std(n_active_rw_arr):.0f} |

### Null Model B: Shuffled Returns

| Metrica | Valor |
|---------|-------|
| N simulacoes validas | {len(sr_null_shuf_clean)} |
| SR medio | {np.mean(sr_null_shuf_clean):.6f} +/- {np.std(sr_null_shuf_clean):.6f} |
| P5 / P50 / P95 | {p5_shuf:.6f} / {p50_shuf:.6f} / {p95_shuf:.6f} |
| **p-value (todas barras)** | **{pval_shuf:.4f}** |
| **p-value (active trades)** | **{pval_active_shuf:.4f}** |
| N_active medio | {np.mean(n_active_shuf_arr):.0f} +/- {np.std(n_active_shuf_arr):.0f} |

---

## Veredito

### **{verdict}**

"""
    if verdict == "GENUINE":
        report += f"""O SR do modelo completo ({sr_real:.4f}) supera P95 de **ambos** os null models.
A aceleracao SavGol na escala 51 e um artefato fraco o suficiente para complementar
features genuinas (tstat, volatility) sem dominar o RF.

**Implicacao:** sg_acceleration_51 e uma alternativa viavel a sg_velocity_51 como
feature de contexto. Ambas sao artefatos fracos que permitem alpha genuino emergir
da combinacao com features genuinas.
"""
    elif verdict == "MARGINAL":
        report += f"""O SR do modelo completo ({sr_real:.4f}) supera P95 de **um** dos null models
mas nao do outro.

- p-value (Random Walk): {pval_rw:.4f} {'< 0.05 (PASS)' if pval_rw < 0.05 else '>= 0.05 (FAIL)'}
- p-value (Shuffled): {pval_shuf:.4f} {'< 0.05 (PASS)' if pval_shuf < 0.05 else '>= 0.05 (FAIL)'}

**Implicacao:** Evidencia parcial. A aceleracao pode ser fraca demais para contribuir
como contexto, ou estar no limite do que e util.
"""
    else:
        report += f"""O SR do modelo completo ({sr_real:.4f}) NAO supera P95 de nenhum dos null models.

- p-value (Random Walk): {pval_rw:.4f} (>= 0.05)
- p-value (Shuffled): {pval_shuf:.4f} (>= 0.05)

**Implicacao:** sg_acceleration_51 nao contribui o suficiente como feature de contexto.
Possiveis razoes:
1. A aceleracao e fraca demais — nao fornece contexto util ao RF
2. O RF ignora a feature (MDA provavelmente baixo) e o modelo degenera
3. Sem uma feature de contexto adequada, as features genuinas sozinhas nao bastam
"""

    report += f"""
---

## Comparacao: Tres Variantes do T8 Full Pipeline

| Variante | SR real | SR null (RW) | p-value RW | p-value Shuf | Veredito |
|----------|---------|-------------|-----------|-------------|---------|
| sg_velocity_51 | 0.0518 | -0.046 +/- 0.037 | 0.0000 | 0.0000 | **GENUINE** |
| ret_20_savgol | ~0.082 | ~+0.074 (prelim) | >>0.05 | - | **ARTIFACT** |
| sg_acceleration_51 | {sr_real:.4f} | {np.mean(sr_null_rw_clean):.4f} +/- {np.std(sr_null_rw_clean):.4f} | {pval_rw:.4f} | {pval_shuf:.4f} | **{verdict}** |

---

## Analise Complementar

### Trades Ativos: O Pipeline Filtra Igual em Ruido?

| Cenario | N_active medio | SR_active medio |
|---------|---------------|-----------------|
| Dados reais | {n_active_real} | {sr_active_real:.4f} |
| Random Walk | {np.mean(n_active_rw_arr):.0f} +/- {np.std(n_active_rw_arr):.0f} | {np.nanmean(sr_active_rw_clean):.4f} +/- {np.nanstd(sr_active_rw_clean):.4f} |
| Shuffled | {np.mean(n_active_shuf_arr):.0f} +/- {np.std(n_active_shuf_arr):.0f} | {np.nanmean(sr_active_shuf_clean):.4f} +/- {np.nanstd(sr_active_shuf_clean):.4f} |

### Skewness: O Pipeline Distorce a Distribuicao?

| Cenario | Skewness media |
|---------|---------------|
| Dados reais | {skew_real:.4f} |
| Random Walk | {np.nanmean(skew_rw_clean):.4f} +/- {np.nanstd(skew_rw_clean):.4f} |
| Shuffled | {np.nanmean(skew_shuf_clean):.4f} +/- {np.nanstd(skew_shuf_clean):.4f} |

---

## Tempo de Execucao

- Total: {elapsed_total/60:.1f} minutos
- Por simulacao (media): {elapsed_total/N_SIMULATIONS/2:.1f} segundos

---

## Plots

![SR Distributions](pngs/t8fp_accel51_sr_distributions.png)

![Active Trades Analysis](pngs/t8fp_accel51_active_analysis.png)

![Box Plot Comparison](pngs/t8fp_accel51_boxplot.png)

---

*Gerado em 2026-03-26. Predecessores: t8_full_pipeline.md, t8_full_pipeline_ret20.md,
genuinas_vs_artefatos.md*
"""

    report_path = os.path.join(REPORT_DIR, "t8_full_pipeline_accel51.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n  Report: {report_path}")
    print(f"  Total time: {elapsed_total/60:.1f} min")
    print("  Done.")


if __name__ == "__main__":
    main()
