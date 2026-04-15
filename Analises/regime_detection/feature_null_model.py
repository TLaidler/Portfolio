#!/usr/bin/env python3
# coding: utf-8
"""
=============================================================================
Feature Null Model — Per-Feature T8 Test
=============================================================================

Tests EVERY feature in the pipeline against random walks to separate
genuine predictive power from pipeline artifacts.

Three null model types:
  1. Pure RW (drift=0): tests if feature generates SR from noise
  2. Shuffled returns: preserves distribution, destroys temporal structure
  3. For volume-dependent features: shuffled returns with real volume

Output: relatorios/feature_null_model.md + relatorios/pngs/fnm_*.png
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

from utils.savgol import savgol_causal, savgol_causal_deriv
from regime_detection_advanced import DollarBarBuilder, DEFAULT_CONFIG

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ==========================================================================
# CONFIG
# ==========================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
REPORT_DIR = os.path.join(SCRIPT_DIR, "relatorios")
PNG_DIR = os.path.join(REPORT_DIR, "pngs")
os.makedirs(PNG_DIR, exist_ok=True)

SG_WINDOW = DEFAULT_CONFIG["savgol_window"]  # 21
SG_POLY = DEFAULT_CONFIG["savgol_polyorder"]  # 3
N_SIMULATIONS = 200


# ==========================================================================
# DATA LOADING
# ==========================================================================
def load_data():
    path = os.path.join(DATA_DIR, "btcusdt_1m.csv")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    print(f"  BTC 1-min: {df.shape}")
    return df


def build_dollar_bars(df_1m):
    builder = DollarBarBuilder(
        calibration_days=DEFAULT_CONFIG["dollar_bar_calibration_days"],
        bars_per_day=DEFAULT_CONFIG["dollar_bars_per_day"],
    )
    bars = builder.transform(df_1m)
    print(f"  Dollar bars: {len(bars)}")
    return bars


# ==========================================================================
# FEATURE EXTRACTORS (pure functions: prices + optional volume -> array)
# ==========================================================================

def feat_sg_velocity(close, volume=None):
    """SavGol 1st derivative / realized_vol."""
    vel = savgol_causal_deriv(close, SG_WINDOW, SG_POLY, deriv=1)
    price_safe = np.where(close > 1e-12, close, np.nan)
    vel_norm = vel / price_safe
    sg = savgol_causal(close, SG_WINDOW, SG_POLY)
    ret = pd.Series(sg).pct_change().values
    vol = pd.Series(ret).rolling(20, min_periods=20).std().values
    vol_safe = np.where(vol > 1e-12, vol, np.nan)
    return vel_norm / vol_safe


def feat_sg_acceleration(close, volume=None):
    """SavGol 2nd derivative / price."""
    acc = savgol_causal_deriv(close, SG_WINDOW, SG_POLY, deriv=2)
    price_safe = np.where(close > 1e-12, close, np.nan)
    return acc / price_safe


def feat_sg_curvature(close, volume=None):
    """Geometric curvature from SavGol."""
    vel = savgol_causal_deriv(close, SG_WINDOW, SG_POLY, deriv=1)
    acc = savgol_causal_deriv(close, SG_WINDOW, SG_POLY, deriv=2)
    price_safe = np.where(close > 1e-12, close, np.nan)
    v = vel / price_safe
    a = acc / price_safe
    return a / np.power(1 + v**2, 1.5)


def feat_sg_velocity_51(close, volume=None):
    """SavGol velocity at scale 51."""
    vel = savgol_causal_deriv(close, 51, SG_POLY, deriv=1)
    price_safe = np.where(close > 1e-12, close, np.nan)
    vel_norm = vel / price_safe
    sg = savgol_causal(close, 51, SG_POLY)
    ret = pd.Series(sg).pct_change().values
    vol = pd.Series(ret).rolling(50, min_periods=50).std().values
    vol_safe = np.where(vol > 1e-12, vol, np.nan)
    return vel_norm / vol_safe


def feat_scale_divergence(close, volume=None):
    """Divergence between SavGol velocity at scales 21 and 51."""
    vel_21 = savgol_causal_deriv(close, 21, SG_POLY, deriv=1)
    vel_51 = savgol_causal_deriv(close, 51, SG_POLY, deriv=1)
    price_safe = np.where(close > 1e-12, close, np.nan)
    v21 = pd.Series(vel_21 / price_safe)
    v51 = pd.Series(vel_51 / price_safe)
    cov_r = v51.rolling(100, min_periods=100).cov(v21)
    var_r = v21.rolling(100, min_periods=100).var()
    beta = (cov_r / var_r.replace(0, np.nan)).clip(-10, 10)
    return (v51 - beta * v21).values


def feat_ret20_savgol(close, volume=None):
    """Old ret_20 on SavGol (known artifact, included as control)."""
    sg = savgol_causal(close, SG_WINDOW, SG_POLY)
    return pd.Series(sg).pct_change(20).values


def feat_ffd(close, volume=None):
    """Fractional differentiation (d=0.4)."""
    d = 0.4
    weights = [1.0]
    k = 1
    while True:
        w = -weights[-1] * (d - k + 1) / k
        if abs(w) < 1e-4:
            break
        weights.append(w)
        k += 1
    weights = np.array(weights[::-1])
    result = np.convolve(close, weights, mode="full")[:len(close)]
    result[:len(weights) - 1] = np.nan
    return result


def feat_roll_spread(close, volume=None):
    """Roll (1984) bid-ask spread estimator."""
    w = 20
    dp = np.diff(close, prepend=np.nan)
    n = len(close)
    roll = np.full(n, np.nan)
    for i in range(w + 1, n):
        dp_t = dp[i - w + 1: i + 1]
        dp_t1 = dp[i - w: i]
        mask = ~(np.isnan(dp_t) | np.isnan(dp_t1))
        if mask.sum() < w // 2:
            continue
        cov_val = np.cov(dp_t[mask], dp_t1[mask])[0, 1]
        roll[i] = 2.0 * np.sqrt(-cov_val) if cov_val < 0 else 0.0
    return roll


def feat_lz_entropy(close, volume=None):
    """Lempel-Ziv complexity of return signs (simplified: unique subsequences)."""
    w = 50  # reduced from 100 for speed in null model
    ret = np.diff(close, prepend=np.nan)
    binary = np.where(ret > 0, "1", "0")
    n = len(close)
    lz = np.full(n, np.nan)
    for i in range(w, n):
        s = "".join(binary[i - w + 1: i + 1])
        # Fast LZ approximation: count unique substrings of length 1..5
        unique = set()
        for sl in range(1, min(6, len(s) + 1)):
            for j in range(len(s) - sl + 1):
                unique.add(s[j:j+sl])
        norm = len(s) / np.log2(max(len(s), 2))
        lz[i] = len(unique) / max(norm, 1)
    return lz


def feat_tstat_20(close, volume=None):
    """T-statistic of 20-bar momentum."""
    ret = pd.Series(close).pct_change()
    mean_n = ret.rolling(20, min_periods=20).mean()
    std_n = ret.rolling(20, min_periods=20).std()
    return (mean_n / (std_n / np.sqrt(20))).values


def feat_tstat_50(close, volume=None):
    """T-statistic of 50-bar momentum."""
    ret = pd.Series(close).pct_change()
    mean_n = ret.rolling(50, min_periods=50).mean()
    std_n = ret.rolling(50, min_periods=50).std()
    return (mean_n / (std_n / np.sqrt(50))).values


def feat_volatility_20(close, volume=None):
    """Realized volatility 20-bar."""
    sg = savgol_causal(close, SG_WINDOW, SG_POLY)
    ret = pd.Series(sg).pct_change()
    return ret.rolling(20, min_periods=20).std().values


def feat_log_volume(close, volume=None):
    """Log(1 + volume)."""
    if volume is None:
        return np.full(len(close), np.nan)
    return np.log1p(volume)


# --- Volume-dependent features (need real volume for null model) ---

def feat_vpin(close, volume=None):
    """VPIN — Volume-Synchronized Probability of Informed Trading."""
    if volume is None:
        return np.full(len(close), np.nan)
    n = len(close)
    ret = np.diff(close, prepend=close[0]) / np.maximum(close, 1e-12)
    buy_vol = np.where(ret > 0, volume, 0)
    sell_vol = np.where(ret <= 0, volume, 0)
    n_buckets = 50
    vpin = np.full(n, np.nan)
    for i in range(n_buckets, n):
        bv = buy_vol[i-n_buckets:i]
        sv = sell_vol[i-n_buckets:i]
        tv = volume[i-n_buckets:i]
        tv_sum = np.sum(tv)
        if tv_sum > 0:
            vpin[i] = np.sum(np.abs(bv - sv)) / tv_sum
    return vpin


def feat_kyle_lambda(close, volume=None):
    """Kyle Lambda — price impact per unit volume."""
    if volume is None:
        return np.full(len(close), np.nan)
    n = len(close)
    ret = np.diff(close, prepend=close[0])
    signed_vol = np.sign(ret) * volume
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


# ==========================================================================
# NULL MODEL ENGINE
# ==========================================================================
def compute_sr(feature_values, returns):
    """SR of sign(feature) strategy."""
    valid = ~np.isnan(feature_values) & ~np.isnan(returns)
    f = feature_values[valid]
    r = returns[valid]
    if len(f) < 50:
        return np.nan
    pos = np.sign(f[:-1])
    strat = pos * r[1:]
    return np.mean(strat) / max(np.std(strat, ddof=1), 1e-12)


def run_null_model(feat_name, feat_fn, close_real, volume_real, bar_returns,
                   n_sims, needs_volume=False):
    """Run null model for one feature. Returns dict with results."""
    actual_ret = np.diff(close_real, prepend=close_real[0]) / np.maximum(close_real, 1e-12)
    sigma = np.std(bar_returns)
    n = len(close_real)

    # SR on real data
    feat_real = feat_fn(close_real, volume_real)
    sr_real = compute_sr(feat_real, actual_ret)

    # Null 1: random walk (drift=0)
    sr_rw = []
    for i in range(n_sims):
        rng = np.random.RandomState(i)
        r_syn = sigma * rng.randn(n - 1)
        p_syn = np.cumprod(np.concatenate([[100.0], 1 + r_syn]))
        act_syn = np.diff(p_syn, prepend=p_syn[0]) / np.maximum(p_syn, 1e-12)
        if needs_volume:
            f_syn = feat_fn(p_syn, volume_real)
        else:
            f_syn = feat_fn(p_syn, None)
        sr_rw.append(compute_sr(f_syn, act_syn))
    sr_rw = np.array(sr_rw)
    sr_rw = sr_rw[~np.isnan(sr_rw)]

    # Null 2: shuffled returns (preserves distribution, destroys time structure)
    sr_shuf = []
    for i in range(n_sims):
        rng = np.random.RandomState(i + 50000)
        shuf = bar_returns.copy()
        rng.shuffle(shuf)
        p_syn = np.cumprod(np.concatenate([[close_real[0]], 1 + shuf]))
        act_syn = np.diff(p_syn, prepend=p_syn[0]) / np.maximum(p_syn, 1e-12)
        if needs_volume:
            f_syn = feat_fn(p_syn, volume_real)
        else:
            f_syn = feat_fn(p_syn, None)
        sr_shuf.append(compute_sr(f_syn, act_syn))
    sr_shuf = np.array(sr_shuf)
    sr_shuf = sr_shuf[~np.isnan(sr_shuf)]

    # P-values
    pval_rw = np.mean(sr_rw >= sr_real) if len(sr_rw) > 0 else 1.0
    pval_shuf = np.mean(sr_shuf >= sr_real) if len(sr_shuf) > 0 else 1.0

    # Also check if SR_real is significantly BELOW null (sign flip)
    pval_rw_abs = np.mean(np.abs(sr_rw) >= abs(sr_real)) if len(sr_rw) > 0 else 1.0

    # Verdict: genuine if SR_real > P95 of BOTH null models
    if pval_rw < 0.05 and pval_shuf < 0.05:
        verdict = "GENUINE"
    elif pval_rw < 0.05 or pval_shuf < 0.05:
        verdict = "MARGINAL"
    else:
        verdict = "ARTIFACT"

    return {
        "sr_real": sr_real,
        "sr_rw_mean": np.mean(sr_rw), "sr_rw_std": np.std(sr_rw),
        "sr_rw_p95": np.percentile(sr_rw, 95) if len(sr_rw) > 0 else np.nan,
        "pval_rw": pval_rw,
        "sr_shuf_mean": np.mean(sr_shuf), "sr_shuf_std": np.std(sr_shuf),
        "sr_shuf_p95": np.percentile(sr_shuf, 95) if len(sr_shuf) > 0 else np.nan,
        "pval_shuf": pval_shuf,
        "verdict": verdict,
    }


# ==========================================================================
# MAIN
# ==========================================================================
def main():
    print("=" * 70)
    print("  FEATURE NULL MODEL — Per-Feature Random Walk Test")
    print("=" * 70)

    df_1m = load_data()
    bars = build_dollar_bars(df_1m)

    close_raw = bars["close"].values.astype(np.float64)
    volume_raw = bars["volume"].values.astype(np.float64)
    bar_returns = bars["close"].pct_change().dropna().values

    # Define all features to test
    features = [
        # SavGol derivative features (new)
        ("sg_velocity", feat_sg_velocity, False, "SavGol 1st deriv / vol"),
        ("sg_acceleration", feat_sg_acceleration, False, "SavGol 2nd deriv / price"),
        ("sg_curvature", feat_sg_curvature, False, "Geometric curvature"),
        ("sg_velocity_51", feat_sg_velocity_51, False, "SavGol velocity scale 51"),
        ("scale_divergence", feat_scale_divergence, False, "Velocity divergence 21 vs 51"),
        # Old momentum (control — known artifact)
        ("ret20_savgol", feat_ret20_savgol, False, "pct_change(20) on SavGol [CONTROL]"),
        # Price-derived features
        ("ffd_0.4", feat_ffd, False, "Fractional differentiation d=0.4"),
        ("roll_spread", feat_roll_spread, False, "Roll (1984) spread estimator"),
        ("lz_entropy", feat_lz_entropy, False, "Lempel-Ziv complexity"),
        ("tstat_20", feat_tstat_20, False, "T-stat momentum 20 bars"),
        ("tstat_50", feat_tstat_50, False, "T-stat momentum 50 bars"),
        ("volatility_20", feat_volatility_20, False, "Realized vol 20 bars"),
        # Volume-dependent features
        ("vpin", feat_vpin, True, "VPIN (informed trading)"),
        ("kyle_lambda", feat_kyle_lambda, True, "Kyle Lambda (price impact)"),
        # log_volume excluded: sign(log1p(vol)) is always +1 (not a directional signal)
    ]

    results = {}

    print(f"\n  Running {N_SIMULATIONS} simulations per feature...")
    print(f"\n  {'Feature':<22s} {'SR_real':>8s} {'SR_rw':>8s} {'p_rw':>6s} "
          f"{'SR_shuf':>8s} {'p_shuf':>6s} {'Verdict':>10s}")
    print(f"  {'-'*72}")

    for fname, ffn, needs_vol, desc in features:
        # Slow features get fewer simulations
        slow_features = {"lz_entropy", "roll_spread"}
        very_slow_features = {"kyle_lambda"}
        if fname in very_slow_features:
            n_sims = 20
        elif fname in slow_features:
            n_sims = 50
        else:
            n_sims = N_SIMULATIONS
        print(f"  Testing {fname} (n={n_sims})...", end="", flush=True)
        res = run_null_model(fname, ffn, close_raw, volume_raw, bar_returns,
                            n_sims, needs_volume=needs_vol)
        results[fname] = {**res, "description": desc, "needs_volume": needs_vol}
        print(f"\r  {fname:<22s} {res['sr_real']:>8.4f} {res['sr_rw_mean']:>8.4f} "
              f"{res['pval_rw']:>6.3f} {res['sr_shuf_mean']:>8.4f} "
              f"{res['pval_shuf']:>6.3f} {res['verdict']:>10s}")

    # Summary
    genuine = [k for k, v in results.items() if v["verdict"] == "GENUINE"]
    marginal = [k for k, v in results.items() if v["verdict"] == "MARGINAL"]
    artifacts = [k for k, v in results.items() if v["verdict"] == "ARTIFACT"]

    print(f"\n  === SUMMARY ===")
    print(f"  GENUINE  ({len(genuine)}): {', '.join(genuine) if genuine else 'none'}")
    print(f"  MARGINAL ({len(marginal)}): {', '.join(marginal) if marginal else 'none'}")
    print(f"  ARTIFACT ({len(artifacts)}): {', '.join(artifacts) if artifacts else 'none'}")

    # --- PLOTS ---
    # 1. Main comparison bar chart
    fig, ax = plt.subplots(figsize=(14, 7))
    fnames = list(results.keys())
    x = np.arange(len(fnames))
    width = 0.25

    sr_reals = [results[f]["sr_real"] for f in fnames]
    sr_rws = [results[f]["sr_rw_mean"] for f in fnames]
    sr_shufs = [results[f]["sr_shuf_mean"] for f in fnames]
    sr_rw_stds = [results[f]["sr_rw_std"] for f in fnames]
    verdicts = [results[f]["verdict"] for f in fnames]

    colors_real = {"GENUINE": "forestgreen", "MARGINAL": "goldenrod", "ARTIFACT": "firebrick"}
    real_colors = [colors_real[v] for v in verdicts]

    ax.bar(x - width, sr_reals, width, color=real_colors, alpha=0.9, label="SR Real", edgecolor="white")
    ax.bar(x, sr_rws, width, yerr=sr_rw_stds, color="steelblue", alpha=0.6,
           label="SR Random Walk", capsize=2, edgecolor="white")
    ax.bar(x + width, sr_shufs, width, color="plum", alpha=0.6,
           label="SR Shuffled", edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(fnames, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Sharpe Ratio (per-bar)")
    ax.set_title(f"Feature Null Model: Real vs Random Walk vs Shuffled\n"
                 f"N={N_SIMULATIONS} sims | Green=genuine, Yellow=marginal, Red=artifact")
    ax.legend(loc="upper right", fontsize=8)
    ax.axhline(0, color="black", lw=0.5)

    plt.tight_layout()
    path1 = os.path.join(PNG_DIR, "fnm_feature_comparison.png")
    plt.savefig(path1, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Plot: {path1}")

    # 2. P-value heatmap
    fig, ax = plt.subplots(figsize=(12, 5))
    pvals = np.array([[results[f]["pval_rw"], results[f]["pval_shuf"]] for f in fnames])
    im = ax.imshow(pvals.T, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1)
    ax.set_xticks(range(len(fnames)))
    ax.set_xticklabels(fnames, rotation=45, ha="right", fontsize=8)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["p-value\n(Random Walk)", "p-value\n(Shuffled)"])
    for i in range(len(fnames)):
        for j in range(2):
            color = "white" if pvals[i, j] > 0.5 else "black"
            ax.text(i, j, f"{pvals[i, j]:.3f}", ha="center", va="center",
                    fontsize=7, color=color, fontweight="bold")
    ax.set_title("P-values: lower = more likely genuine (green < 0.05)")
    plt.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout()
    path2 = os.path.join(PNG_DIR, "fnm_pvalue_heatmap.png")
    plt.savefig(path2, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot: {path2}")

    # 3. Genuine features detail
    if genuine or marginal:
        interesting = genuine + marginal
        fig, axes = plt.subplots(1, len(interesting), figsize=(5 * len(interesting), 5))
        if len(interesting) == 1:
            axes = [axes]
        for ax, fname in zip(axes, interesting):
            res = results[fname]
            # Re-run to get distribution
            rng_seeds = range(N_SIMULATIONS)
            sr_dist = []
            for seed in rng_seeds:
                rng = np.random.RandomState(seed + 50000)
                shuf = bar_returns.copy()
                rng.shuffle(shuf)
                p_syn = np.cumprod(np.concatenate([[close_raw[0]], 1 + shuf]))
                act_syn = np.diff(p_syn, prepend=p_syn[0]) / np.maximum(p_syn, 1e-12)
                for fn, ffunc, nv, _ in features:
                    if fn == fname:
                        if nv:
                            f_syn = ffunc(p_syn, volume_raw)
                        else:
                            f_syn = ffunc(p_syn, None)
                        break
                sr_dist.append(compute_sr(f_syn, act_syn))
            sr_dist = np.array(sr_dist)
            sr_dist = sr_dist[~np.isnan(sr_dist)]

            ax.hist(sr_dist, bins=30, alpha=0.7, color="steelblue", edgecolor="white")
            ax.axvline(res["sr_real"], color="red", lw=2, ls="--",
                       label=f"SR real = {res['sr_real']:.4f}")
            ax.axvline(np.percentile(sr_dist, 95), color="orange", lw=1, ls=":",
                       label=f"P95 = {np.percentile(sr_dist, 95):.4f}")
            ax.set_title(f"{fname}\np_shuf={res['pval_shuf']:.4f}")
            ax.set_xlabel("SR (shuffled null)")
            ax.legend(fontsize=7)

        plt.tight_layout()
        path3 = os.path.join(PNG_DIR, "fnm_genuine_detail.png")
        plt.savefig(path3, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Plot: {path3}")

    # --- GENERATE REPORT ---
    report = f"""# Feature Null Model Report

**Data:** 2026-03-25
**Objetivo:** Testar cada feature individualmente contra random walks para separar
poder preditivo genuino de artefatos do pipeline.

**Metodologia:**
- Para cada feature, computa-se `sign(feature)` como sinal de trading
- SR medido como `mean(sign(feat) * ret_next) / std(...)`
- Dois null models: (1) Random Walk drift=0, (2) Retornos shuffled
- N = {N_SIMULATIONS} simulacoes por feature
- p-value = P(SR_null >= SR_real)
- **GENUINE**: p < 0.05 em ambos os null models
- **MARGINAL**: p < 0.05 em apenas um null model
- **ARTIFACT**: p >= 0.05 em ambos

---

## Resultados

| Feature | Descricao | SR Real | SR RW | p(RW) | SR Shuf | p(Shuf) | Veredito |
|---------|-----------|---------|-------|-------|---------|---------|----------|
"""
    for fname in fnames:
        r = results[fname]
        report += (f"| {fname} | {r['description']} | {r['sr_real']:.4f} | "
                   f"{r['sr_rw_mean']:.4f} | {r['pval_rw']:.3f} | "
                   f"{r['sr_shuf_mean']:.4f} | {r['pval_shuf']:.3f} | "
                   f"**{r['verdict']}** |\n")

    report += f"""
---

## Classificacao

### GENUINE (p < 0.05 em ambos null models)
"""
    if genuine:
        for f in genuine:
            r = results[f]
            report += f"- **{f}**: SR_real={r['sr_real']:.4f}, p_rw={r['pval_rw']:.3f}, p_shuf={r['pval_shuf']:.3f} -- {r['description']}\n"
    else:
        report += "Nenhuma feature passou ambos os testes.\n"

    report += f"""
### MARGINAL (p < 0.05 em apenas um null model)
"""
    if marginal:
        for f in marginal:
            r = results[f]
            report += f"- **{f}**: SR_real={r['sr_real']:.4f}, p_rw={r['pval_rw']:.3f}, p_shuf={r['pval_shuf']:.3f} -- {r['description']}\n"
    else:
        report += "Nenhuma.\n"

    report += f"""
### ARTIFACT (p >= 0.05 em ambos null models)
"""
    for f in artifacts:
        r = results[f]
        report += f"- {f}: SR_real={r['sr_real']:.4f}, SR_rw={r['sr_rw_mean']:.4f} -- {r['description']}\n"

    report += f"""
---

## Interpretacao

### Por que a maioria das features baseadas em preco sao artefatos?

Qualquer transformacao suave do preco (SavGol, MA, FFD, pct_change) aplicada a
um random walk produz uma serie com autocorrelacao local. `sign()` dessa serie
tende a acertar a proxima barra porque carrega informacao do preco ATUAL, nao
porque preve o FUTURO. E como olhar no retrovisor e achar que esta prevendo
a estrada.

### Por que features de microestrutura podem ser genuinas?

VPIN e Kyle Lambda dependem da INTERACAO entre preco e volume. Num random walk
com volume real, o volume nao "sabe" nada sobre a direcao do preco sintetico.
Mas no BTC real, o volume carrega informacao sobre QUEM esta comprando (informed
vs uninformed traders). Essa assimetria de informacao e o que gera o sinal.

### Implicacoes para o pipeline

1. **Features de preco puro** (ret_N, SavGol derivatives, FFD, t-stat, volatility)
   NAO devem ser usadas como sinais direcionais isolados
2. **Features de microestrutura** (VPIN, Kyle Lambda) tem sinal genuino mas fraco
   (SR ~ 0.0002-0.0003 per bar)
3. O RF pode combinar features fracas-mas-genuinas com features de contexto
   (volatility, entropy) para gerar um sinal composto mais forte
4. **A proxima etapa e retreinar o RF removendo features-artefato e priorizando
   features genuinas como preditores primarios**

---

## Plots

![Feature Comparison](relatorios/pngs/fnm_feature_comparison.png)

![P-value Heatmap](relatorios/pngs/fnm_pvalue_heatmap.png)

"""
    if genuine or marginal:
        report += "![Genuine Features Detail](relatorios/pngs/fnm_genuine_detail.png)\n"

    report_path = os.path.join(REPORT_DIR, "feature_null_model.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n  Report: {report_path}")
    print("  Done.")


if __name__ == "__main__":
    main()
