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


def plot_fund_nav(
    is_rets: pd.Series,
    oos_rets: pd.Series,
    is_close: pd.Series,
    oos_close: pd.Series,
    out: Path,
    cdi_daily_pct: pd.Series | None = None,
    cdi_annual: float = 0.15,
    trading_days_per_year: int = 252,
    title: str = "Cota (início = 1) — Modelo vs. Buy&Hold vs. CDI",
) -> None:
    """Fund-style NAV plot: cota inicial = 1, comparando

    - o modelo (retornos do meta-label IS out-of-fold + OOS, encadeados),
    - Buy & Hold do BTC (fechamentos concatenados, normalizados),
    - CDI — se `cdi_daily_pct` for dado (série diária Bacen série 12, %/dia),
      compõe dia a dia com a taxa histórica; caso contrário, usa `cdi_annual`
      constante.

    As três curvas compartilham o mesmo eixo temporal; uma linha pontilhada
    marca a fronteira IS→OOS.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(12, 5.5))

    # --- Buy&Hold NAV (cota=1 no primeiro close IS) ---
    close = pd.concat([is_close, oos_close]).sort_index()
    close = close[~close.index.duplicated(keep="first")].dropna()
    bh_nav = close / close.iloc[0]
    start, end = bh_nav.index.min(), bh_nav.index.max()
    tz = bh_nav.index.tz

    # --- Strategy NAV ---
    # Os retornos vêm por *evento* do triple-barrier, com horizonte ~20 barras
    # e sobreposição alta. Compor todos em série trataria cada bet como se
    # usasse 100% do capital sequencialmente, o que inflaria a cota
    # artificialmente. Para refletir o que um fundo veria (alocação
    # equal-weight entre bets concorrentes), reamostramos para retorno *médio
    # diário* sobre os eventos que fecharam naquele dia, e compomos dia a dia.
    strat_rets = pd.concat([is_rets.fillna(0.0), oos_rets.fillna(0.0)]).sort_index()
    strat_rets = strat_rets[~strat_rets.index.duplicated(keep="first")]
    strat_daily = strat_rets.resample("1D").mean().fillna(0.0)
    if len(strat_daily) == 0 or strat_daily.index.min() > start:
        strat_daily = pd.concat([pd.Series([0.0], index=[start.normalize()]), strat_daily])
    if strat_daily.index.max() < end:
        strat_daily = pd.concat([strat_daily, pd.Series([0.0], index=[end.normalize()])])
    strat_daily = strat_daily.sort_index()
    strat_nav = (1.0 + strat_daily).cumprod()

    # --- CDI NAV: compõe no dia útil ---
    if cdi_daily_pct is not None and len(cdi_daily_pct):
        cdi = cdi_daily_pct.copy()
        if cdi.index.tz is None:
            cdi.index = cdi.index.tz_localize("UTC")
        elif tz is not None:
            cdi.index = cdi.index.tz_convert(tz)
        cdi = cdi.sort_index()
        cdi = cdi[(cdi.index >= start) & (cdi.index <= end)]
        daily_factors = 1.0 + cdi / 100.0
        cdi_nav = daily_factors.cumprod()
        cdi_nav = cdi_nav / cdi_nav.iloc[0]
        mean_daily = float(cdi.mean())
        mean_ann = ((1.0 + mean_daily / 100.0) ** trading_days_per_year - 1.0) * 100.0
        cdi_label = f"CDI Bacen (~{mean_ann:.2f}% a.a. médio)"
    else:
        daily_rate = (1 + cdi_annual) ** (1.0 / trading_days_per_year) - 1.0
        bps = daily_rate * 10_000
        bday_idx = pd.date_range(start.normalize(), end.normalize(), freq="B", tz=tz)
        cdi_nav = pd.Series(
            (1 + daily_rate) ** np.arange(len(bday_idx)),
            index=bday_idx,
        )
        cdi_label = f"CDI {cdi_annual*100:.0f}% a.a. (~{bps:.1f} bps/dia útil)"

    # --- Plot ---
    ax.plot(bh_nav.index, bh_nav.values, color="grey", lw=1.1, alpha=0.75, label="Buy & Hold BTC")
    ax.plot(cdi_nav.index, cdi_nav.values, color="C2", lw=1.3, ls="--",
            label=cdi_label)
    ax.plot(strat_nav.index, strat_nav.values, color="C0", lw=1.8, label="Modelo (meta-labelled)")

    # Fronteira IS → OOS (último evento IS)
    if len(is_rets):
        boundary = is_rets.index.max()
        ax.axvline(boundary, color="k", lw=0.8, ls=":", alpha=0.6)
        ymax = ax.get_ylim()[1]
        ax.text(boundary, ymax * 0.97, "  IS → OOS", fontsize=9, va="top", ha="left", alpha=0.7)

    ax.axhline(1.0, color="k", lw=0.5, alpha=0.5)
    ax.set_ylabel("Cota (início = 1)")
    ax.set_xlabel("Data")
    ax.set_title(title)
    ax.legend(loc="best")
    save_fig(fig, out)
