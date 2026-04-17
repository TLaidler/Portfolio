"""Plotting for the pipeline (IS/OOS, distributions, decision frontiers).

All plots are saved to plots/. No plt.show() is ever called.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve

from .utils import save_fig, set_plot_style


# --------------------------------------------------------------------------
# Bars & stationarity
# --------------------------------------------------------------------------

def plot_bar_returns_hist(rets: pd.Series, out: Path, title: str) -> None:
    set_plot_style()
    fig, ax = plt.subplots()
    ax.hist(rets.dropna(), bins=80, edgecolor="black", alpha=0.75)
    ax.set_title(f"{title} — skew={rets.skew():.2f}, kurt={rets.kurt():.2f}")
    ax.set_xlabel("Return per bar")
    ax.set_ylabel("Frequency")
    save_fig(fig, out)


def plot_ffd_adf(series: pd.Series, d_values: np.ndarray, adf_stats: np.ndarray, out: Path) -> None:
    set_plot_style()
    fig, ax1 = plt.subplots()
    ax1.plot(d_values, adf_stats, "o-", color="C0", label="ADF stat")
    ax1.axhline(-2.86, color="red", ls="--", label="ADF 5% crit")
    ax1.set_xlabel("Fractional differentiation d")
    ax1.set_ylabel("ADF statistic")
    ax1.legend(loc="best")
    ax1.set_title("ADF stat vs. d (fixed-width FFD)")
    save_fig(fig, out)


# --------------------------------------------------------------------------
# Feature importance
# --------------------------------------------------------------------------

def plot_importance(
    mdi: pd.Series, mda: pd.Series, out: Path
) -> None:
    set_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    mdi.sort_values().plot.barh(ax=axes[0], color="C0")
    axes[0].set_title("Clustered MDI")
    mda.sort_values().plot.barh(ax=axes[1], color="C2")
    axes[1].axvline(0, color="k", lw=0.5)
    axes[1].set_title("Clustered MDA (log-loss delta)")
    save_fig(fig, out)


# --------------------------------------------------------------------------
# Decision boundary (precision-recall)
# --------------------------------------------------------------------------

def plot_precision_recall(
    y_true: np.ndarray, proba: np.ndarray, out: Path
) -> None:
    set_plot_style()
    prec, rec, thr = precision_recall_curve(y_true, proba)
    fig, ax = plt.subplots()
    ax.plot(thr, prec[:-1], label="Precision")
    ax.plot(thr, rec[:-1], label="Recall")
    ax.set_xlabel("Decision threshold")
    ax.set_ylabel("Score")
    ax.set_title("Precision/Recall vs. threshold (meta model)")
    ax.legend(loc="best")
    save_fig(fig, out)


# --------------------------------------------------------------------------
# Sharpe IS vs OOS, RW null distribution
# --------------------------------------------------------------------------

def plot_sharpe_is_vs_oos(sharpe_is: float, sharpe_oos: float, out: Path) -> None:
    set_plot_style()
    fig, ax = plt.subplots()
    ax.bar(["In-Sample", "Out-Of-Sample"], [sharpe_is, sharpe_oos], color=["C0", "C3"])
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("Sharpe Ratio (annualized)")
    ax.set_title(f"IS vs OOS Sharpe — {sharpe_is:+.3f} / {sharpe_oos:+.3f}")
    save_fig(fig, out)


def plot_rw_null_vs_strategy(
    strat_sharpe: float, null_sharpes: np.ndarray, p_value: float, out: Path
) -> None:
    set_plot_style()
    fig, ax = plt.subplots()
    ax.hist(null_sharpes, bins=40, alpha=0.7, edgecolor="black", label="RW null")
    ax.axvline(strat_sharpe, color="red", lw=2, label=f"Strategy ({strat_sharpe:+.3f})")
    ax.set_title(f"Strategy vs Random-Walk null (p={p_value:.4f})")
    ax.set_xlabel("Sharpe ratio")
    ax.set_ylabel("Frequency")
    ax.legend()
    save_fig(fig, out)


def plot_cpcv_path_sharpes(sharpes: List[float], out: Path) -> None:
    set_plot_style()
    fig, ax = plt.subplots()
    ax.hist(sharpes, bins=30, alpha=0.85, edgecolor="black", color="C4")
    ax.axvline(np.mean(sharpes), color="k", ls="--", label=f"mean = {np.mean(sharpes):+.3f}")
    ax.set_title(f"CPCV paths — {len(sharpes)} Sharpe realisations")
    ax.set_xlabel("Sharpe ratio")
    ax.set_ylabel("Frequency")
    ax.legend()
    save_fig(fig, out)


def plot_equity_curves(curves: Dict[str, pd.Series], out: Path, title: str = "Equity curves") -> None:
    set_plot_style()
    fig, ax = plt.subplots(figsize=(12, 5))
    for name, s in curves.items():
        ax.plot(s.index, s.values, label=name)
    ax.set_title(title)
    ax.set_ylabel("Cumulative log-return")
    ax.legend()
    save_fig(fig, out)


def plot_cumulative_returns(
    is_rets: pd.Series,
    oos_rets: pd.Series,
    out: Path,
    is_price: pd.Series | None = None,
    oos_price: pd.Series | None = None,
    title: str = "Strategy cumulative return — IS → OOS",
) -> None:
    """Compound cumulative return on one timeline, IS then OOS, with a
    boundary marker and an optional buy-and-hold benchmark.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(12, 5.5))

    is_c = (1.0 + is_rets.fillna(0.0)).cumprod() - 1.0
    oos_c = (1.0 + oos_rets.fillna(0.0)).cumprod() - 1.0
    # Chain OOS on top of the IS end-value so the line is continuous.
    oos_chained = (1.0 + is_c.iloc[-1]) * (1.0 + oos_c) - 1.0 if len(is_c) else oos_c

    ax.plot(is_c.index, is_c.values * 100, color="C0", label="IS (out-of-fold)")
    ax.plot(oos_chained.index, oos_chained.values * 100, color="C3", label="OOS")

    if is_price is not None and oos_price is not None:
        bh_is = (is_price / is_price.iloc[0] - 1.0) * 100
        bh_oos = (oos_price / is_price.iloc[0] - 1.0) * 100
        ax.plot(bh_is.index, bh_is.values, color="grey", ls="--", alpha=0.6, label="Buy&Hold (BTC)")
        ax.plot(bh_oos.index, bh_oos.values, color="grey", ls="--", alpha=0.6)

    if len(is_c):
        ax.axvline(is_c.index[-1], color="k", lw=0.8, ls=":", alpha=0.7)
        ax.text(is_c.index[-1], ax.get_ylim()[1] * 0.95, " IS→OOS",
                fontsize=9, va="top", ha="left", alpha=0.7)

    ax.axhline(0, color="k", lw=0.5)
    ax.set_title(title)
    ax.set_ylabel("Cumulative return (%)")
    ax.set_xlabel("Event close time")
    ax.legend(loc="best")
    save_fig(fig, out)
