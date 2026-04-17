"""Bench: Savitzky-Golay analytic fractional derivative vs Marcos's FFD.

Hypothesis: for d in (0,1), can we replace the discrete backshift operator
(1-B)^d (AFML 5.4.2, `fixed_width_frac_diff`) by fitting a local polynomial
(Savitzky-Golay) and taking the analytic fractional derivative of that
polynomial? Does the result preserve memory as well while achieving
stationarity?

Methods compared, per d in {0.2, 0.3, 0.4, 0.5, 0.6, 0.7}:

    M1   FFD(log_close, d)                 — baseline (AFML 5.4.2)
    M2a  Riemann-Liouville D^d on SavGol  — keeps polynomial intercept
    M2b  Caputo D^d on SavGol             — annihilates constants
    M3   FFD(SavGol(log_close, d=0), d)   — smooth then FFD

Metrics:
    ADF statistic     (more negative → more stationary)
    Pearson corr.     (with original log_close — memory preservation)

Why M2a is expected to fail: on a local fit f(τ) = Σ a_k τ^k over the window
τ ∈ [0, W-1], the RL derivative at τ=W-1 contains a term
a_0 · Γ(1)/Γ(1-d) · (W-1)^(-d) that is proportional to log-price at the left
edge — a non-stationary drift. Caputo kills constants by construction
(equivalent to setting β_0 = 0 in the monomial coefficients), so M2b is the
honest version of the proposal.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from scipy.signal import savgol_coeffs
from scipy.special import gammaln
from statsmodels.tsa.stattools import adfuller

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.features import fixed_width_frac_diff
from pipeline.utils import ProjectPaths, TxtLogger, save_fig, set_plot_style


def analytic_frac_deriv_kernel(
    window: int, polyorder: int, d: float, caputo: bool
) -> np.ndarray:
    """Linear kernel implementing D^d on a local polynomial fit.

    Fits polynomial of order `polyorder` to the last `window` samples in
    local coord τ = 0..W-1, evaluates the fractional derivative at τ=W-1.

    For monomial τ^k:  D^d τ^k = Γ(k+1)/Γ(k-d+1) · τ^(k-d)  (k ≥ 1)
    RL keeps the k=0 term (constant survives); Caputo zeros it.
    """
    A = np.vander(np.arange(window, dtype=float), polyorder + 1, increasing=True)
    A_pinv = np.linalg.pinv(A)  # (p+1, W)
    tau = float(window - 1)
    k = np.arange(polyorder + 1, dtype=float)
    log_beta = gammaln(k + 1) - gammaln(k - d + 1) + (k - d) * np.log(tau)
    beta = np.exp(log_beta)
    if caputo:
        beta[0] = 0.0
    return A_pinv.T @ beta  # shape (W,)


def apply_window_kernel(series: pd.Series, kernel: np.ndarray, name: str) -> pd.Series:
    """Apply a 1-D kernel as a strictly backward-looking convolution."""
    W = len(kernel)
    arr = series.to_numpy(dtype=float)
    out = np.full_like(arr, np.nan)
    if len(arr) < W:
        return pd.Series(out, index=series.index, name=name)
    win = sliding_window_view(arr, W)  # (N-W+1, W), aligned to right edge = i
    valid = ~np.isnan(win).any(axis=1)
    out[W - 1:][valid] = win[valid] @ kernel
    return pd.Series(out, index=series.index, name=name)


def savgol_smooth_kernel(window: int, polyorder: int) -> np.ndarray:
    """Causal SavGol smoother (deriv=0) as a 1-D kernel."""
    return savgol_coeffs(window, polyorder, deriv=0, pos=window - 1, use="dot")


def savgol_frac_deriv(
    series: pd.Series, window: int, polyorder: int, d: float, caputo: bool
) -> pd.Series:
    if window % 2 == 0:
        window += 1
    kernel = analytic_frac_deriv_kernel(window, polyorder, d, caputo=caputo)
    tag = "caputo" if caputo else "rl"
    return apply_window_kernel(series, kernel, name=f"sg_Dd{d}_{tag}_W{window}")


def savgol_smooth(series: pd.Series, window: int, polyorder: int) -> pd.Series:
    if window % 2 == 0:
        window += 1
    kernel = savgol_smooth_kernel(window, polyorder)
    return apply_window_kernel(series, kernel, name=f"sg_smooth_W{window}")


def adf_stat(s: pd.Series) -> float:
    s = s.dropna()
    if len(s) < 100:
        return float("nan")
    return float(adfuller(s.values, maxlag=20, regression="c")[0])


def run():
    paths = ProjectPaths.discover()
    log = TxtLogger(paths.resultados, "ffd_vs_savgol")

    df = pd.read_csv(paths.data / "btcusdt_1m.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="mixed")
    df = df.set_index("timestamp").sort_index()
    close = df["close"].astype(float).dropna()
    logp = np.log(close).rename("log_close")
    N_SLICE = 100_000
    if len(logp) > N_SLICE:
        logp = logp.iloc[-N_SLICE:]

    W = 101
    poly = 3
    ds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

    log.header("Bench — FFD vs SavGol fractional derivative (RL & Caputo)")
    log.write(f"n_obs = {len(logp)}  range = [{logp.index.min()}, {logp.index.max()}]")
    log.write(f"SavGol window W = {W}, polyorder = {poly}")

    adf_raw = adf_stat(logp)
    log.write(f"\nADF(raw log_close) = {adf_raw:+.3f}   (non-stationary baseline)")
    log.write("ADF 5% critical value ≈ -2.86")

    smooth_for_m3 = savgol_smooth(logp, W, poly)

    rows = []
    for d in ds:
        m1 = fixed_width_frac_diff(logp, d=d, threshold=1e-4)
        m2a = savgol_frac_deriv(logp, W, poly, d, caputo=False)
        m2b = savgol_frac_deriv(logp, W, poly, d, caputo=True)
        m3 = fixed_width_frac_diff(smooth_for_m3.dropna(), d=d, threshold=1e-4)
        m3 = m3.reindex(logp.index)

        idx = (
            m1.dropna().index
            .intersection(m2a.dropna().index)
            .intersection(m2b.dropna().index)
            .intersection(m3.dropna().index)
        )
        lp = logp.loc[idx]

        for name, series in [
            ("M1_FFD", m1), ("M2a_SG_RL", m2a),
            ("M2b_SG_Caputo", m2b), ("M3_SG_then_FFD", m3),
        ]:
            s = series.loc[idx]
            rows.append({
                "d": d,
                "method": name,
                "adf": adf_stat(s),
                "corr": float(s.corr(lp)),
                "n": int(s.notna().sum()),
            })

    df_res = pd.DataFrame(rows)
    log.write("\nADF statistic (more negative = more stationary)")
    log.table(df_res.pivot(index="d", columns="method", values="adf"))
    log.write("\nCorrelation with log_close (memory preservation)")
    log.table(df_res.pivot(index="d", columns="method", values="corr"))

    set_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    colors = {"M1_FFD": "C0", "M2a_SG_RL": "C3",
              "M2b_SG_Caputo": "C2", "M3_SG_then_FFD": "C1"}
    for name in ["M1_FFD", "M2a_SG_RL", "M2b_SG_Caputo", "M3_SG_then_FFD"]:
        sub = df_res[df_res["method"] == name].sort_values("d")
        axes[0].plot(sub["d"], sub["adf"], "o-", label=name, color=colors[name])
        axes[1].plot(sub["d"], sub["corr"], "o-", label=name, color=colors[name])
    axes[0].axhline(-2.86, color="red", ls="--", label="ADF 5% crit")
    axes[0].set_xlabel("fractional d"); axes[0].set_ylabel("ADF stat")
    axes[0].set_title(f"Stationarity vs d (W={W}, poly={poly})"); axes[0].legend()
    axes[1].set_xlabel("fractional d"); axes[1].set_ylabel("corr with log_close")
    axes[1].set_title("Memory preservation vs d"); axes[1].legend()
    save_fig(fig, paths.plots / "bench_ffd_vs_savgol.png")

    out_csv = paths.resultados / "ffd_vs_savgol.csv"
    df_res.to_csv(out_csv, index=False)
    log.write(f"\nCSV: {out_csv}")
    log.write(f"PNG: {paths.plots / 'bench_ffd_vs_savgol.png'}")


if __name__ == "__main__":
    run()
