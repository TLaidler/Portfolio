"""Scientifically-honest backtesting (AFML Ch. 11-15).

Components:
  - CPCV path reconstruction -> many near-independent backtest trajectories.
  - Random Walk null: shuffle returns to generate a distribution under the
    null hypothesis of no signal and compare the strategy's Sharpe to it.
  - Probabilistic Sharpe Ratio (PSR) and Deflated Sharpe Ratio (DSR) correct
    for skew/kurtosis and selection bias under multiple testing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm, skew, kurtosis


# --------------------------------------------------------------------------
# Sharpe statistics
# --------------------------------------------------------------------------

def sharpe_ratio(returns: np.ndarray, ppy: int = 252) -> float:
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 2 or r.std() == 0:
        return 0.0
    return float(r.mean() / r.std() * np.sqrt(ppy))


def probabilistic_sharpe_ratio(
    returns: np.ndarray, sr_benchmark: float = 0.0, ppy: int = 252
) -> float:
    """PSR: probability that true SR > benchmark given skew/kurtosis.

    AFML 14.2. Returns a value in [0, 1].
    """
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    n = len(r)
    if n < 3:
        return float("nan")
    sr = sharpe_ratio(r, ppy=ppy) / np.sqrt(ppy)  # per-period SR
    sk = float(skew(r, bias=False))
    ku = float(kurtosis(r, fisher=True, bias=False))
    denom = np.sqrt((1 - sk * sr + ((ku) / 4.0) * sr ** 2) / (n - 1))
    z = (sr - sr_benchmark / np.sqrt(ppy)) / max(denom, 1e-12)
    return float(norm.cdf(z))


def deflated_sharpe_ratio(
    sr_hat: float,
    sr_trials: np.ndarray,
    returns: np.ndarray,
    ppy: int = 252,
) -> float:
    """Deflated Sharpe Ratio (Bailey & López de Prado, 2014).

    Expected max SR under the null (given N trials with observed SR
    variance V) is:
        E[max SR] ≈ sqrt(V) * ( (1-γ)·Φ⁻¹(1 - 1/N) + γ·Φ⁻¹(1 - 1/(N·e)) )
    where γ is the Euler-Mascheroni constant. We then feed this as the
    benchmark to PSR. All SR here are expressed in the same unit; since
    `sharpe_ratio()` returns annualised SR, so do `sr_trials`, so the
    benchmark is annualised too and can be passed directly to PSR which
    de-annualises internally.
    """
    trials = np.asarray(sr_trials, dtype=float)
    trials = trials[~np.isnan(trials)]
    n_trials = int(max(2, len(trials)))
    v = float(np.var(trials, ddof=1)) if len(trials) > 1 else 0.0
    if v <= 0:
        return probabilistic_sharpe_ratio(returns, 0.0, ppy)
    euler = 0.5772156649015329
    expected_max_sr = np.sqrt(v) * (
        (1 - euler) * norm.ppf(1 - 1.0 / n_trials)
        + euler * norm.ppf(1 - 1.0 / (n_trials * np.e))
    )
    # expected_max_sr is already in the same (annualised) unit as sr_trials
    return probabilistic_sharpe_ratio(returns, float(expected_max_sr), ppy)


# --------------------------------------------------------------------------
# CPCV paths: reconstruct distinct backtest trajectories
# --------------------------------------------------------------------------

def cpcv_paths(
    test_predictions: List[Tuple[np.ndarray, np.ndarray, Tuple[int, ...]]],
    returns: pd.Series,
    n_groups: int,
) -> List[pd.Series]:
    """Reconstruct unique backtest paths from a CPCV predictions list.

    Each group is used in several test splits; we stack predictions for the
    same group to produce multiple paths. Input is a list of
    (test_index, predicted_signal, combo).
    """
    # bucket prediction series by group
    buckets: Dict[int, List[pd.Series]] = {g: [] for g in range(n_groups)}
    for test_idx, preds, combo in test_predictions:
        idx_ret = returns.iloc[test_idx]
        s = pd.Series(preds, index=idx_ret.index)
        # distribute the prediction across the groups it covers
        for g in combo:
            buckets[g].append(s)

    # A path = pick the i-th realisation from each group (if present) and
    # concatenate in time order.
    max_runs = max((len(v) for v in buckets.values()), default=0)
    paths: List[pd.Series] = []
    for i in range(max_runs):
        parts = []
        for g in range(n_groups):
            if i < len(buckets[g]):
                parts.append(buckets[g][i])
        if parts:
            parts = sorted(parts, key=lambda s: s.index[0])
            paths.append(pd.concat(parts).sort_index())
    return paths


# --------------------------------------------------------------------------
# Random Walk null via Monte Carlo
# --------------------------------------------------------------------------

def random_walk_null_distribution(
    returns: pd.Series, n_sims: int = 1000, block: int = 20, random_state: int = 0
) -> np.ndarray:
    """Moving-block bootstrap of the return series to estimate the null SR."""
    rng = np.random.default_rng(random_state)
    r = returns.dropna().to_numpy()
    n = len(r)
    if n < block:
        return np.zeros(n_sims)

    n_blocks = int(np.ceil(n / block))
    sr_null = np.empty(n_sims)
    for s in range(n_sims):
        starts = rng.integers(0, n - block, size=n_blocks)
        draws = np.concatenate([r[st:st + block] for st in starts])[:n]
        # random sign per block: this is the RW/no-drift null
        signs = rng.choice([-1, 1], size=n_blocks)
        signed = np.concatenate([
            s_ * r[st:st + block] for s_, st in zip(signs, starts)
        ])[:n]
        sr_null[s] = sharpe_ratio(signed)
    return sr_null


# --------------------------------------------------------------------------
# Strategy returns from meta-label predictions
# --------------------------------------------------------------------------

def strategy_returns(
    side: pd.Series,
    meta_prob: pd.Series,
    ret: pd.Series,
    threshold: float = 0.5,
) -> pd.Series:
    """Bet side when the meta model is confident enough.

    side in {-1, 0, +1}, meta_prob in [0, 1], ret is per-event realised return.
    Bet size is 1 if meta_prob >= threshold else 0.
    """
    bet = (meta_prob >= threshold).astype(float)
    return (side * bet * ret).rename("strategy_ret")


@dataclass
class BacktestReport:
    sharpe_is: float
    sharpe_oos: float
    psr: float
    dsr: float
    rw_null_mean: float
    rw_null_std: float
    rw_p_value: float
    n_trials: int

    def to_text(self) -> str:
        return (
            f"Sharpe (IS)         : {self.sharpe_is:+.4f}\n"
            f"Sharpe (OOS)        : {self.sharpe_oos:+.4f}\n"
            f"Probabilistic SR    : {self.psr:.4f}\n"
            f"Deflated SR         : {self.dsr:.4f}\n"
            f"RW-null SR mean/std : {self.rw_null_mean:+.4f} / {self.rw_null_std:.4f}\n"
            f"RW-null p-value     : {self.rw_p_value:.4f}\n"
            f"N trials            : {self.n_trials}\n"
        )
