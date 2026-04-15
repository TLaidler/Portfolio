#!/usr/bin/env python3
# coding: utf-8
"""
=============================================================================
T8 Full Pipeline Null Model — The Definitive Test
=============================================================================

Tests whether the COMPLETE pipeline (features + RF + meta-label) generates
statistically significant SR on real BTC data vs random walks.

Previous T8 tested features individually (ret_20_savgol → p=0.80, artifact).
This test asks the harder question: does the COMBINATION of features inside
the RF + meta-label produce genuine alpha, even if individual features are
artifacts?

Methodology:
  For each simulation:
    1. Replace dollar bar close/high/low with synthetic prices (random walk)
    2. Keep real volume and intra-bar volatility structure
    3. Compute the SAME 9 features selected by MDA
    4. Apply triple-barrier labeling on synthetic prices
    5. Train meta-label (80/20 temporal split) with SAME RF config
    6. Compute SR on test set
  Compare distribution of null SRs to real SR.

Two null models:
  A. Random Walk (drift=0): tests if pipeline creates SR from pure noise
  B. Shuffled Returns: preserves return distribution, destroys time structure

Output: relatorios/t8_full_pipeline.md + relatorios/pngs/t8fp_*.png
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

N_SIMULATIONS = 30  # increase for more power (each sim ~40 sec)

# Same features the real model selected
SELECTED_FEATURES = [
    "sg_velocity_51", "tstat_50", "volatility_20", "volatility_50",
    "tstat_20", "ffd_close", "tstat_10", "btc_dxy_spread", "volatility_10",
]


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

    Modes:
      - "random_walk": drift=0, sigma calibrated from real bar returns
      - "shuffled": real returns in random order

    Intra-bar structure preserved: high/low ratios relative to close
    are taken from real data so triple-barrier sees realistic ranges.
    """
    rng = np.random.RandomState(seed)
    bars = bars_real.copy()

    close_real = bars["close"].values.astype(np.float64)
    high_real = bars["high"].values.astype(np.float64)
    low_real = bars["low"].values.astype(np.float64)
    n = len(close_real)

    bar_returns = pd.Series(close_real).pct_change().dropna().values
    sigma = np.std(bar_returns)

    # Generate synthetic returns
    if mode == "random_walk":
        syn_returns = sigma * rng.randn(n - 1)
    elif mode == "shuffled":
        syn_returns = bar_returns.copy()
        rng.shuffle(syn_returns)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Build synthetic close
    syn_close = np.cumprod(np.concatenate([[close_real[0]], 1 + syn_returns]))

    # Preserve intra-bar volatility structure
    # high_ratio = how much high exceeds close (fractional)
    # low_ratio = how much low is below close (fractional)
    safe_close = np.where(close_real > 1e-12, close_real, 1.0)
    high_ratio = (high_real - close_real) / safe_close
    low_ratio = (close_real - low_real) / safe_close

    # Clip ratios to avoid extreme values at edges
    high_ratio = np.clip(high_ratio, 0, 0.05)
    low_ratio = np.clip(low_ratio, 0, 0.05)

    syn_high = syn_close * (1 + high_ratio)
    syn_low = syn_close * (1 - low_ratio)

    # Open = previous close (approximate)
    syn_open = np.concatenate([[syn_close[0]], syn_close[:-1]])

    bars["close"] = syn_close
    bars["high"] = syn_high
    bars["low"] = syn_low
    bars["open"] = syn_open
    # volume stays real

    return bars


# ==========================================================================
# FEATURE COMPUTATION (reuse FeatureRegistry)
# ==========================================================================
def compute_features(bars, config, verbose=False):
    """Compute all features using the standard FeatureRegistry."""
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

    Uses fixed feature set (no MDA selection) for fair comparison.
    """
    # 1. Features
    df_feat, all_features = compute_features(bars, config, verbose=False)

    # Check which selected features are available
    available = [f for f in selected_features if f in df_feat.columns]
    if len(available) < 2:
        return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                "accuracy": np.nan, "psr": np.nan}

    # Drop NaN rows for available features
    df_feat = df_feat.dropna(subset=available).reset_index(drop=True)

    if len(df_feat) < 200:
        return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                "accuracy": np.nan, "psr": np.nan}

    # 2. Triple-barrier labeling
    labeler = TripleBarrierLabeler(config)
    # Suppress print
    import io
    from contextlib import redirect_stdout
    f_buf = io.StringIO()
    with redirect_stdout(f_buf):
        df_labeled = labeler.apply_barriers(df_feat)

    if len(df_labeled) < 200:
        return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                "accuracy": np.nan, "psr": np.nan}

    # 3. Prepare X, y
    feature_cols = [f for f in available if f in df_labeled.columns]
    X = df_labeled[feature_cols].values.astype(np.float64)
    y = df_labeled["label"].values.astype(int)
    close = df_labeled["close"].values.astype(np.float64)
    t0 = df_labeled["t0"].values
    t1 = df_labeled["t1"].values

    # Handle any remaining NaN/inf in X
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    # 4. Temporal split 80/20
    split_idx = int(len(X) * config.get("train_ratio", 0.80))
    if split_idx < 100 or (len(X) - split_idx) < 50:
        return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                "accuracy": np.nan, "psr": np.nan}

    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    close_test = close[split_idx:]

    # 5. Meta-labeling
    meta = MetaLabeler(config)
    with redirect_stdout(f_buf):
        try:
            meta.fit(X_train, y_train)
            final_preds, meta_probs, primary_preds = meta.predict(X_test)
        except Exception:
            return {"sr": np.nan, "sr_active": np.nan, "n_active": 0,
                    "accuracy": np.nan, "psr": np.nan}

    # 6. Compute SR
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

    # Active trades only
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
# CPCV NULL MODEL (bonus: test CPCV mean SR too)
# ==========================================================================
def run_cpcv_once(bars, config, selected_features):
    """
    Run CPCV (without meta-label) on given bars.
    Returns mean SR across 15 paths.
    """
    import io
    from contextlib import redirect_stdout

    df_feat, all_features = compute_features(bars, config, verbose=False)
    available = [f for f in selected_features if f in df_feat.columns]
    if len(available) < 2:
        return np.nan

    df_feat = df_feat.dropna(subset=available).reset_index(drop=True)
    if len(df_feat) < 200:
        return np.nan

    labeler = TripleBarrierLabeler(config)
    f_buf = io.StringIO()
    with redirect_stdout(f_buf):
        df_labeled = labeler.apply_barriers(df_feat)

    if len(df_labeled) < 200:
        return np.nan

    feature_cols = [f for f in available if f in df_labeled.columns]
    X = df_labeled[feature_cols].values.astype(np.float64)
    y = df_labeled["label"].values.astype(int)
    close = df_labeled["close"].values.astype(np.float64)
    t0 = df_labeled["t0"].values
    t1 = df_labeled["t1"].values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    cpcv = CPCV(config)

    def model_factory():
        return RandomForestClassifier(
            n_estimators=config.get("rf_n_estimators", 500),
            max_depth=config.get("rf_max_depth", 6),
            min_samples_leaf=config.get("rf_min_samples_leaf", 50),
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=config.get("rng_seed", 42),
        )

    with redirect_stdout(f_buf):
        try:
            results = cpcv.cross_validate(model_factory, X, y, t0, t1, close)
        except Exception:
            return np.nan

    return results["mean_sharpe"]


# ==========================================================================
# MAIN
# ==========================================================================
def main():
    print("=" * 70)
    print("  T8 FULL PIPELINE NULL MODEL — The Definitive Test")
    print("=" * 70)
    t_start = time.time()

    # ── Load real data ─────────────────────────────────────────────────
    print("\n[1/5] Loading data...")
    df_1m = load_data()
    bars_real, threshold = build_dollar_bars(df_1m)

    # ── Run real pipeline ──────────────────────────────────────────────
    print("\n[2/5] Running pipeline on REAL data...")
    # First run with verbose to see feature computation
    registry = FeatureRegistry()
    registry.register_defaults()
    df_check, fnames_check = registry.compute_all(bars_real.copy(), DEFAULT_CONFIG)
    avail = [f for f in SELECTED_FEATURES if f in df_check.columns]
    print(f"  Available features: {avail}")
    missing = [f for f in SELECTED_FEATURES if f not in df_check.columns]
    if missing:
        print(f"  Missing (no external data): {missing}")

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

    # Skip CPCV (too expensive, ~8 min); use save_point value as reference
    sr_cpcv_real = 0.1211  # from save_point_advanced/cpcv_sharpe_distribution.txt
    print(f"  SR_CPCV_real (from save_point): {sr_cpcv_real:.6f}")

    # ── Null Model A: Random Walk (drift=0) ────────────────────────────
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

    # ── Null Model B: Shuffled Returns ─────────────────────────────────
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

    # ── Analysis ───────────────────────────────────────────────────────
    print("\n[5/5] Analysis & Report...")

    # P-values
    pval_rw = (np.mean(sr_null_rw_clean >= sr_real)
               if len(sr_null_rw_clean) > 0 else 1.0)
    pval_shuf = (np.mean(sr_null_shuf_clean >= sr_real)
                 if len(sr_null_shuf_clean) > 0 else 1.0)

    # Two-sided p-values (does |SR_real| exceed null?)
    pval_rw_abs = (np.mean(np.abs(sr_null_rw_clean) >= abs(sr_real))
                   if len(sr_null_rw_clean) > 0 else 1.0)

    # Percentiles
    if len(sr_null_rw_clean) > 0:
        p5_rw, p50_rw, p95_rw = np.percentile(sr_null_rw_clean, [5, 50, 95])
    else:
        p5_rw = p50_rw = p95_rw = np.nan

    if len(sr_null_shuf_clean) > 0:
        p5_shuf, p50_shuf, p95_shuf = np.percentile(sr_null_shuf_clean,
                                                      [5, 50, 95])
    else:
        p5_shuf = p50_shuf = p95_shuf = np.nan

    # Verdict
    if pval_rw < 0.05 and pval_shuf < 0.05:
        verdict = "GENUINE"
    elif pval_rw < 0.05 or pval_shuf < 0.05:
        verdict = "MARGINAL"
    else:
        verdict = "ARTIFACT"

    # Active trades analysis
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

    # N_active distribution
    n_active_rw_arr = np.array(n_active_null_rw)
    n_active_shuf_arr = np.array(n_active_null_shuf)

    elapsed_total = time.time() - t_start

    # ── Summary ────────────────────────────────────────────────────────
    print(f"\n  {'='*60}")
    print(f"  T8 FULL PIPELINE — RESULTS")
    print(f"  {'='*60}")
    print(f"  SR_real (meta-label, all bars):  {sr_real:.6f}")
    print(f"  SR_real (active trades only):    {sr_active_real:.6f}")
    print(f"  SR_CPCV_real (mean 15 paths):    {sr_cpcv_real:.6f}")
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

    # ── Plots ──────────────────────────────────────────────────────────

    # Plot 1: SR distributions (main result)
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
        f"T8 Full Pipeline Null Model — Verdict: {verdict}\n"
        f"SR_real={sr_real:.4f} | N_sims={N_SIMULATIONS} | "
        f"Features: {len(SELECTED_FEATURES)}",
        fontsize=13, fontweight="bold",
        color=verdict_color.get(verdict, "black"),
    )
    plt.tight_layout()
    path1 = os.path.join(PNG_DIR, "t8fp_sr_distributions.png")
    plt.savefig(path1, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Plot: {path1}")

    # Plot 2: Active trades SR + N_active comparison
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

    fig.suptitle("T8 Full Pipeline — Active Trades & Distribution Analysis",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    path2 = os.path.join(PNG_DIR, "t8fp_active_analysis.png")
    plt.savefig(path2, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot: {path2}")

    # Plot 3: SR real vs null (combined box + scatter)
    fig, ax = plt.subplots(figsize=(10, 6))
    positions = [1, 2]
    bp = ax.boxplot([sr_null_rw_clean, sr_null_shuf_clean],
                    positions=positions, widths=0.4,
                    patch_artist=True,
                    boxprops=dict(facecolor="lightblue", alpha=0.7),
                    medianprops=dict(color="navy", lw=2))

    # Overlay individual points
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
    ax.set_title(f"T8 Full Pipeline: Real SR vs Null Distributions\n"
                 f"Verdict: {verdict} | "
                 f"p_rw={pval_rw:.4f}, p_shuf={pval_shuf:.4f}")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    path3 = os.path.join(PNG_DIR, "t8fp_boxplot.png")
    plt.savefig(path3, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot: {path3}")

    # ── Report ─────────────────────────────────────────────────────────
    report = f"""# T8 Full Pipeline Null Model — The Definitive Test

**Data:** 2026-03-26
**Objetivo:** Testar se o pipeline COMPLETO (features + RF + meta-label) gera
SR estatisticamente significativo em dados reais vs random walks.

**Diferenca do T8 original:** O T8 anterior testou features *individualmente*
(e.g., ret_20_savgol → p=0.80, artifact). Este teste avalia o *modelo completo*:
a combinacao de 9 features dentro do RF + meta-label pode gerar alpha genuino
mesmo que features individuais sejam artefatos?

---

## Metodologia

Para cada simulacao:
1. Substituir close/high/low dos dollar bars por precos sinteticos (random walk)
2. Preservar volume real e estrutura intra-bar (ratios high/low relativos ao close)
3. Computar as **mesmas 9 features** selecionadas pelo MDA no modelo real
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
| SR CPCV (media 15 paths) | {sr_cpcv_real:.6f} |
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
O pipeline extrai sinal genuino que nao e explicavel por artefatos do filtro SavGol
nem pela distribuicao empirica dos retornos.

**Implicacao:** A combinacao de features (sg_velocity_51 como contexto + tstat como
sinal direcional) dentro do RF gera alpha que nao existe em nenhuma feature individual.
O todo e maior que a soma das partes.
"""
    elif verdict == "MARGINAL":
        report += f"""O SR do modelo completo ({sr_real:.4f}) supera P95 de **um** dos null models
mas nao do outro.

- p-value (Random Walk): {pval_rw:.4f} {'< 0.05 (PASS)' if pval_rw < 0.05 else '>= 0.05 (FAIL)'}
- p-value (Shuffled): {pval_shuf:.4f} {'< 0.05 (PASS)' if pval_shuf < 0.05 else '>= 0.05 (FAIL)'}

**Implicacao:** Ha evidencia parcial de sinal genuino. O pipeline pode estar capturando
estrutura temporal real (se passa no shuffled) ou superando ruido puro (se passa no RW),
mas nao ambos simultaneamente.
"""
    else:
        report += f"""O SR do modelo completo ({sr_real:.4f}) NAO supera P95 de nenhum dos null models.

- p-value (Random Walk): {pval_rw:.4f} (>= 0.05)
- p-value (Shuffled): {pval_shuf:.4f} (>= 0.05)

**Implicacao:** O pipeline completo (RF + meta-label + 9 features) NAO gera alpha
significativamente acima do que seria esperado em random walks. O retorno positivo
observado pode ser explicado por:
1. Artefatos do filtro SavGol amplificados pelo RF
2. Autocorrelacao do sinal gerando Sharpe inflado
3. O meta-label filtrando trades de forma que coincidentemente favorece periodos
   de retorno positivo

Isso NAO invalida o modelo como ferramenta de *gestao de risco* (saber quando nao
operar tem valor), mas indica que o alpha direcional e ilusorio.
"""

    report += f"""
---

## Analise Complementar

### Trades Ativos: O Pipeline Filtra Igual em Ruido?

| Cenario | N_active medio | SR_active medio |
|---------|---------------|-----------------|
| Dados reais | {n_active_real} | {sr_active_real:.4f} |
| Random Walk | {np.mean(n_active_rw_arr):.0f} +/- {np.std(n_active_rw_arr):.0f} | {np.nanmean(sr_active_rw_clean):.4f} +/- {np.nanstd(sr_active_rw_clean):.4f} |
| Shuffled | {np.mean(n_active_shuf_arr):.0f} +/- {np.std(n_active_shuf_arr):.0f} | {np.nanmean(sr_active_shuf_clean):.4f} +/- {np.nanstd(sr_active_shuf_clean):.4f} |

Se o modelo gera numero similar de trades em dados reais e sinteticos, o meta-label
nao esta usando informacao genuina para decidir *quando* operar — esta operando
com a mesma frequencia em ruido.

Se o modelo gera MAIS trades em dados reais, ha evidencia de que detecta regime.
Se gera MENOS, pode estar sendo mais cauteloso com dados reais (possivel sinal
de que reconhece incerteza genuina).

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

![SR Distributions](pngs/t8fp_sr_distributions.png)

![Active Trades Analysis](pngs/t8fp_active_analysis.png)

![Box Plot Comparison](pngs/t8fp_boxplot.png)

---

*Gerado em 2026-03-26. Predecessores: feature_null_model.md, genuinas_vs_artefatos.md,
revisao_feynman_marcos_mod7.md*
"""

    report_path = os.path.join(REPORT_DIR, "t8_full_pipeline.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n  Report: {report_path}")
    print(f"  Total time: {elapsed_total/60:.1f} min")
    print("  Done.")


if __name__ == "__main__":
    main()
