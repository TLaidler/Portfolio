"""
Shared utilities for PPO-based RL trading module.

Provides feature normalization, metric wrappers (delegating to
ModelEvaluator where possible), reproducibility seeding, and
a training logger for tracking iteration metrics.
"""

import os
import sys
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Parent directory import for ModelEvaluator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from regime_detection_advanced import ModelEvaluator


# ===========================================================================
# Feature Normalization
# ===========================================================================

class FeatureNormalizer:
    """
    Z-score normalization fitted on training data only (anti-leakage).

    Clips transformed values to [-5, 5] to prevent observation explosions
    in the neural network.
    """

    def __init__(self, clip_range: float = 5.0):
        self.clip_range = clip_range
        self.mean_: Optional[np.ndarray] = None
        self.std_: Optional[np.ndarray] = None

    def fit(self, X_train: np.ndarray) -> "FeatureNormalizer":
        """Compute per-feature mean/std from training data."""
        self.mean_ = np.nanmean(X_train, axis=0)
        self.std_ = np.nanstd(X_train, axis=0)
        # Prevent division by zero for constant features
        self.std_[self.std_ < 1e-12] = 1.0
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply training statistics. Clip to [-clip_range, clip_range]."""
        if self.mean_ is None:
            raise RuntimeError("FeatureNormalizer not fitted. Call fit() first.")
        X_norm = (X - self.mean_) / self.std_
        return np.clip(X_norm, -self.clip_range, self.clip_range)

    def fit_transform(self, X_train: np.ndarray) -> np.ndarray:
        return self.fit(X_train).transform(X_train)


# ===========================================================================
# Metrics (wrappers around ModelEvaluator + new)
# ===========================================================================

def compute_sharpe_ratio(returns: np.ndarray) -> float:
    """SR = mean/std (per-bar, no annualization). Matches existing convention."""
    returns = returns[~np.isnan(returns)]
    if len(returns) < 2:
        return 0.0
    std = np.std(returns, ddof=1)
    if std < 1e-12:
        return 0.0
    return float(np.mean(returns) / std)


def compute_max_drawdown(equity_curve: np.ndarray) -> float:
    """
    Max drawdown from equity curve (array of portfolio values).
    Returns negative float (e.g., -0.15 = 15% drawdown).
    """
    if len(equity_curve) < 2:
        return 0.0
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / np.maximum(peak, 1e-12)
    return float(np.min(drawdown))


def compute_win_rate(strategy_returns: np.ndarray, actions: np.ndarray) -> float:
    """Fraction of positive-return bars among bars with active position."""
    active = actions != 0
    if active.sum() == 0:
        return 0.0
    active_returns = strategy_returns[active]
    return float((active_returns > 0).sum() / len(active_returns))


def compute_trade_count(actions: np.ndarray) -> int:
    """Number of position changes (each entry or exit counts)."""
    changes = np.diff(actions) != 0
    return int(changes.sum())


def compute_avg_trade_duration(actions: np.ndarray) -> float:
    """Mean number of bars per contiguous position (excluding flat)."""
    durations = []
    current_pos = 0
    current_len = 0
    for a in actions:
        if a != 0:
            if a == current_pos:
                current_len += 1
            else:
                if current_len > 0:
                    durations.append(current_len)
                current_pos = a
                current_len = 1
        else:
            if current_len > 0:
                durations.append(current_len)
                current_pos = 0
                current_len = 0
    if current_len > 0:
        durations.append(current_len)
    return float(np.mean(durations)) if durations else 0.0


def compute_profit_factor(strategy_returns: np.ndarray) -> float:
    """Gross profit / gross loss. Returns inf if no losses."""
    gains = strategy_returns[strategy_returns > 0].sum()
    losses = abs(strategy_returns[strategy_returns < 0].sum())
    if losses < 1e-12:
        return float("inf") if gains > 0 else 0.0
    return float(gains / losses)


def compute_psr(returns: np.ndarray, sr_benchmark: float = 0.0) -> float:
    """Delegate to ModelEvaluator.probabilistic_sharpe_ratio()."""
    return ModelEvaluator.probabilistic_sharpe_ratio(returns, sr_benchmark)


def compute_dsr(returns: np.ndarray, n_trials: int) -> float:
    """Delegate to ModelEvaluator.deflated_sharpe_ratio()."""
    return ModelEvaluator.deflated_sharpe_ratio(returns, n_trials)


def compute_strategy_returns(
    predictions: np.ndarray,
    actual_returns: np.ndarray,
    fee_maker: float = 0.0,
    fee_taker: float = 0.0,
    fee_mode: str = "pessimistic",
) -> np.ndarray:
    """Delegate to ModelEvaluator.compute_strategy_returns()."""
    return ModelEvaluator.compute_strategy_returns(
        predictions, actual_returns, fee_maker, fee_taker, fee_mode
    )


# ===========================================================================
# Reproducibility
# ===========================================================================

def set_all_seeds(seed: int) -> None:
    """Set seeds for numpy, torch, random, and configure deterministic behavior."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


# ===========================================================================
# Training Logger
# ===========================================================================

class TrainingLogger:
    """
    Tracks training metrics across iterations for plotting and reporting.

    Usage:
        logger = TrainingLogger()
        logger.log(fold=0, update=1, train_reward=0.5, val_sr=0.12, ...)
        df = logger.to_dataframe()
        logger.to_txt("training_log.txt")
    """

    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def log(self, **metrics: Any) -> None:
        """Append one iteration's metrics."""
        self.records.append(metrics)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert log to DataFrame."""
        return pd.DataFrame(self.records)

    def to_txt(self, path: str) -> None:
        """Save human-readable training log."""
        df = self.to_dataframe()
        with open(path, "w", encoding="utf-8") as f:
            f.write("PPO TRAINING LOG\n")
            f.write("=" * 70 + "\n\n")
            if len(df) == 0:
                f.write("No records.\n")
                return
            f.write(df.to_string(index=False))
            f.write("\n")
