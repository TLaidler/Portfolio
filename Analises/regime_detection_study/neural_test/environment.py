"""
Trading environment for PPO-based RL agent.

Gym-compatible interface (reset/step) without gym dependency.
Receives pre-computed, NaN-free features from FeatureRegistry and
simulates trading with realistic transaction costs matching
ModelEvaluator.compute_strategy_returns().

State: [market_features, current_position, bars_in_position_norm, unrealized_pnl_norm]
Actions: 0=Flat, 1=Long, 2=Short
Reward: incremental PnL - transaction costs - drawdown penalty - idle penalty
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# Action-to-position mapping
ACTION_TO_POSITION = {0: 0, 1: 1, 2: -1}  # flat, long, short


class TradingEnv:
    """
    Stateful trading environment for BTC dollar bars.

    The environment receives a pre-computed feature matrix and close prices.
    It steps through bars sequentially, maintaining position state and
    computing rewards that include transaction costs, drawdown penalty,
    and idle penalty.

    Parameters
    ----------
    features : np.ndarray
        Shape (T, n_features). Normalized market features (NaN-free).
    close_prices : np.ndarray
        Shape (T,). Raw close prices for PnL calculation.
    config : dict
        Configuration with fee/reward parameters.
    """

    def __init__(
        self,
        features: np.ndarray,
        close_prices: np.ndarray,
        config: Dict[str, Any],
    ):
        self.features = features.astype(np.float32)
        self.close_prices = close_prices.astype(np.float64)
        self.n_bars = len(close_prices)
        self.n_features = features.shape[1]

        # Config
        self.fee_taker = config.get("fee_taker", 0.000270)
        self.fee_maker = config.get("fee_maker", 0.000090)
        self.fee_mode = config.get("fee_mode", "pessimistic")
        self.max_holding_bars = config.get("max_holding_bars", 50)
        self.lambda_drawdown = config.get("lambda_drawdown", 0.5)
        self.drawdown_threshold = config.get("drawdown_threshold", 0.02)
        self.lambda_idle = config.get("lambda_idle", 0.0001)
        self.reward_scale = config.get("reward_scale", 100.0)

        # Pre-compute bar returns: (close[t] - close[t-1]) / close[t-1]
        self.bar_returns = np.zeros(self.n_bars, dtype=np.float64)
        self.bar_returns[1:] = np.diff(self.close_prices) / np.maximum(
            self.close_prices[:-1], 1e-12
        )

        # Pre-compute volatility proxy for idle penalty threshold.
        # Use rolling std of returns over 20 bars, matching vol_lookback=20.
        vol_window = 20
        self.volatility = np.full(self.n_bars, np.nan, dtype=np.float64)
        ret_series = self.bar_returns.copy()
        for i in range(vol_window, self.n_bars):
            self.volatility[i] = np.std(ret_series[i - vol_window : i], ddof=1)
        # Fill early NaNs with first valid value
        first_valid = vol_window
        if first_valid < self.n_bars:
            self.volatility[:first_valid] = self.volatility[first_valid]
        self.vol_median = float(np.nanmedian(self.volatility))

        # Observation and action dimensions
        # obs = [features(n_features), position(1), bars_norm(1), pnl_norm(1)]
        self.obs_dim = self.n_features + 3
        self.n_actions = 3

        # State (initialized in reset)
        self._reset_state(start_idx=0)

    @property
    def observation_shape(self) -> Tuple[int]:
        return (self.obs_dim,)

    def _reset_state(self, start_idx: int) -> None:
        """Initialize all mutable state variables."""
        self.current_step = start_idx
        self.position = 0       # flat
        self.entry_price = 0.0
        self.bars_in_position = 0
        self.equity = 1.0
        self.peak_equity = 1.0

    def reset(self, start_idx: int = 0) -> np.ndarray:
        """
        Reset environment to given start index.

        Returns initial observation.
        """
        self._reset_state(start_idx)
        return self._get_observation()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Execute one step.

        Parameters
        ----------
        action : int
            0=flat, 1=long, 2=short

        Returns
        -------
        observation : np.ndarray
        reward : float
        done : bool
        info : dict
        """
        old_position = self.position
        new_position = ACTION_TO_POSITION[action]

        # Compute bar return (realized during this bar)
        bar_ret = self.bar_returns[self.current_step]

        # --- 1. Incremental PnL ---
        # PnL from holding old_position through this bar
        r_pnl = old_position * bar_ret

        # --- 2. Transaction cost ---
        r_cost = self._compute_transaction_cost(old_position, new_position)

        # --- 3. Update equity ---
        self.equity *= (1.0 + old_position * bar_ret - r_cost)
        self.peak_equity = max(self.peak_equity, self.equity)

        # --- 4. Drawdown penalty ---
        drawdown = (self.peak_equity - self.equity) / max(self.peak_equity, 1e-12)
        excess_dd = max(0.0, drawdown - self.drawdown_threshold)
        r_drawdown = -self.lambda_drawdown * excess_dd

        # --- 5. Idle penalty (flat during high vol) ---
        r_holding = 0.0
        vol_current = self.volatility[self.current_step]
        if new_position == 0 and not np.isnan(vol_current):
            if vol_current > self.vol_median:
                r_holding = -self.lambda_idle * vol_current

        # --- Total reward ---
        reward = self.reward_scale * (r_pnl - r_cost + r_drawdown + r_holding)

        # --- Update position state ---
        if new_position != old_position:
            self.position = new_position
            self.bars_in_position = 0
            if new_position != 0:
                self.entry_price = self.close_prices[self.current_step]
            else:
                self.entry_price = 0.0
        else:
            self.bars_in_position += 1

        # Advance step
        self.current_step += 1
        done = self.current_step >= self.n_bars

        obs = self._get_observation() if not done else np.zeros(self.obs_dim, dtype=np.float32)

        info = {
            "r_pnl": r_pnl,
            "r_cost": r_cost,
            "r_drawdown": r_drawdown,
            "r_holding": r_holding,
            "equity": self.equity,
            "position": self.position,
            "drawdown": drawdown,
        }

        return obs, reward, done, info

    def _get_observation(self) -> np.ndarray:
        """
        Construct observation vector.

        Components:
            [0..n_features-1] : market features (normalized)
            [n_features]      : current_position in {-1, 0, 1}
            [n_features+1]    : bars_in_position / max_holding_bars, clipped [0, 1]
            [n_features+2]    : unrealized_pnl / 0.02, clipped [-1, 1]
        """
        obs = np.empty(self.obs_dim, dtype=np.float32)

        # Market features
        obs[: self.n_features] = self.features[self.current_step]

        # Position state
        obs[self.n_features] = float(self.position)
        obs[self.n_features + 1] = min(
            self.bars_in_position / max(self.max_holding_bars, 1), 1.0
        )

        # Unrealized PnL (normalized by typical barrier width ~2%)
        if self.position != 0 and self.entry_price > 0:
            unrealized = (
                self.close_prices[self.current_step] - self.entry_price
            ) / self.entry_price * self.position
        else:
            unrealized = 0.0
        obs[self.n_features + 2] = np.clip(unrealized / 0.02, -1.0, 1.0)

        return obs

    def _compute_transaction_cost(
        self, old_position: int, new_position: int
    ) -> float:
        """
        Compute transaction cost for position change.

        Mirrors ModelEvaluator.compute_strategy_returns() logic exactly
        (regime_detection_advanced.py lines 1911-1921).

        Cost is applied per leg:
          - Closing old position: fee_exit
          - Opening new position: fee_entry
        """
        if new_position == old_position:
            return 0.0

        if self.fee_mode == "pessimistic":
            fee_entry = self.fee_taker
            fee_exit = self.fee_taker
        else:
            fee_entry = self.fee_taker
            fee_exit = self.fee_maker

        cost = 0.0
        if old_position != 0:
            cost += fee_exit    # close old position
        if new_position != 0:
            cost += fee_entry   # open new position
        return cost
