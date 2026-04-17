"""
Deterministic backtesting engine and visualizer for trained PPO agent.

BacktestEngine: runs greedy policy, computes metrics, generates reports.
BacktestVisualizer: equity curves, action distributions, feature importance,
                    training curves, drawdown plots.

Follows existing project conventions: 150 DPI, Agg backend, save_point_* output.
"""

import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

from .environment import TradingEnv, ACTION_TO_POSITION
from .model import ActorCritic
from .utils import (
    compute_sharpe_ratio,
    compute_max_drawdown,
    compute_win_rate,
    compute_trade_count,
    compute_avg_trade_duration,
    compute_profit_factor,
    compute_psr,
    compute_dsr,
    compute_strategy_returns,
    TrainingLogger,
)


# ===========================================================================
# Backtest Engine
# ===========================================================================

class BacktestEngine:
    """
    Deterministic backtest for a trained PPO agent.

    Runs greedy policy (argmax) bar-by-bar. Tracks full equity curve,
    position history, and per-trade statistics. Uses the SAME fee structure
    as the existing pipeline for direct comparison with Random Forest baseline.
    """

    def __init__(self, config: Dict[str, Any]):
        self.fee_maker = config.get("fee_maker", 0.000090)
        self.fee_taker = config.get("fee_taker", 0.000270)
        self.fee_mode = config.get("fee_mode", "pessimistic")

    def run(
        self,
        model: ActorCritic,
        features: np.ndarray,
        close_prices: np.ndarray,
        timestamps: Optional[np.ndarray] = None,
        device: torch.device = torch.device("cpu"),
    ) -> Dict[str, Any]:
        """
        Execute deterministic backtest.

        Parameters
        ----------
        model : ActorCritic
            Trained model (will be set to eval mode).
        features : np.ndarray
            Shape (T, n_features). Normalized features.
        close_prices : np.ndarray
            Shape (T,). Raw close prices.
        timestamps : np.ndarray or None
            Shape (T,). Optional datetime timestamps.
        device : torch.device

        Returns
        -------
        dict with keys: actions, strategy_returns, benchmark_returns,
                        equity_strategy, equity_benchmark, metrics, etc.
        """
        model.eval()
        n_bars = len(close_prices)

        # Compute actual bar returns
        actual_ret = np.zeros(n_bars, dtype=np.float64)
        actual_ret[1:] = np.diff(close_prices) / np.maximum(close_prices[:-1], 1e-12)

        # Run greedy policy
        env = TradingEnv(features, close_prices, self._env_config())
        obs = env.reset()
        actions = np.zeros(n_bars, dtype=np.float64)

        for t in range(n_bars):
            obs_t = torch.tensor(obs, dtype=torch.float32, device=device)
            action = model.get_greedy_action(obs_t)
            actions[t] = ACTION_TO_POSITION[action]

            obs, _, done, _ = env.step(action)
            if done:
                break

        # Compute strategy returns with fees
        strategy_returns = compute_strategy_returns(
            actions, actual_ret,
            self.fee_maker, self.fee_taker, self.fee_mode,
        )

        # Buy & Hold returns (position=+1 always, single entry fee)
        bh_actions = np.ones(n_bars, dtype=np.float64)
        benchmark_returns = compute_strategy_returns(
            bh_actions, actual_ret,
            self.fee_maker, self.fee_taker, self.fee_mode,
        )

        # Equity curves
        equity_strategy = np.cumprod(1.0 + strategy_returns)
        equity_benchmark = np.cumprod(1.0 + benchmark_returns)

        results = {
            "actions": actions,
            "strategy_returns": strategy_returns,
            "benchmark_returns": benchmark_returns,
            "actual_returns": actual_ret,
            "equity_strategy": equity_strategy,
            "equity_benchmark": equity_benchmark,
            "close_prices": close_prices,
            "timestamps": timestamps,
        }

        results["metrics"] = self._compute_metrics(results)
        return results

    def _env_config(self) -> Dict[str, Any]:
        """Minimal config dict for TradingEnv during backtest."""
        return {
            "fee_taker": self.fee_taker,
            "fee_maker": self.fee_maker,
            "fee_mode": self.fee_mode,
            "max_holding_bars": 50,
            "lambda_drawdown": 0.0,    # No reward shaping during backtest
            "drawdown_threshold": 1.0,
            "lambda_idle": 0.0,
            "reward_scale": 1.0,
        }

    def _compute_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compute all backtest metrics."""
        strat_ret = results["strategy_returns"]
        bench_ret = results["benchmark_returns"]
        actions = results["actions"]
        eq_strat = results["equity_strategy"]
        eq_bench = results["equity_benchmark"]

        return {
            # Strategy metrics
            "cumulative_return": float(eq_strat[-1] - 1.0),
            "sharpe_ratio": compute_sharpe_ratio(strat_ret),
            "psr": compute_psr(strat_ret),
            "dsr": compute_dsr(strat_ret, n_trials=1),
            "max_drawdown": compute_max_drawdown(eq_strat),
            "win_rate": compute_win_rate(strat_ret, actions),
            "n_trades": compute_trade_count(actions),
            "avg_trade_duration": compute_avg_trade_duration(actions),
            "profit_factor": compute_profit_factor(strat_ret),
            # Benchmark metrics
            "bh_cumulative_return": float(eq_bench[-1] - 1.0),
            "bh_sharpe_ratio": compute_sharpe_ratio(bench_ret),
            "bh_max_drawdown": compute_max_drawdown(eq_bench),
            # Alpha
            "alpha": float(eq_strat[-1] - eq_bench[-1]),
        }

    def print_report(self, results: Dict[str, Any]) -> str:
        """Format human-readable backtest report."""
        m = results["metrics"]
        lines = [
            "=" * 60,
            "  PPO BACKTEST REPORT",
            "=" * 60,
            "",
            "  STRATEGY PERFORMANCE",
            "  " + "-" * 40,
            f"    Cumulative Return:   {m['cumulative_return']:+.4f} ({m['cumulative_return']*100:+.2f}%)",
            f"    Sharpe Ratio:        {m['sharpe_ratio']:.4f}",
            f"    PSR:                 {m['psr']:.4f}",
            f"    DSR:                 {m['dsr']:.4f}",
            f"    Max Drawdown:        {m['max_drawdown']:.4f} ({m['max_drawdown']*100:.2f}%)",
            f"    Win Rate:            {m['win_rate']:.4f} ({m['win_rate']*100:.1f}%)",
            f"    Trades:              {m['n_trades']}",
            f"    Avg Trade Duration:  {m['avg_trade_duration']:.1f} bars",
            f"    Profit Factor:       {m['profit_factor']:.2f}",
            "",
            "  BUY & HOLD BENCHMARK",
            "  " + "-" * 40,
            f"    Cumulative Return:   {m['bh_cumulative_return']:+.4f} ({m['bh_cumulative_return']*100:+.2f}%)",
            f"    Sharpe Ratio:        {m['bh_sharpe_ratio']:.4f}",
            f"    Max Drawdown:        {m['bh_max_drawdown']:.4f} ({m['bh_max_drawdown']*100:.2f}%)",
            "",
            "  ALPHA",
            "  " + "-" * 40,
            f"    Alpha (Strategy - BH): {m['alpha']:+.4f}",
            "",
            "=" * 60,
        ]
        report = "\n".join(lines)
        print(report)
        return report

    def save_report(self, results: Dict[str, Any], save_dir: str) -> None:
        """Save backtest_report.txt to save_dir."""
        report = self.print_report(results)
        path = os.path.join(save_dir, "backtest_report.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"    Report saved: {path}")


# ===========================================================================
# Backtest Visualizer
# ===========================================================================

class BacktestVisualizer:
    """
    Generates all backtest-related plots.

    Follows existing project conventions: 150 DPI, Agg backend, figsize=(14, 7).
    """

    def __init__(self, save_dir: str):
        self.save_dir = save_dir

    def _save(self, fig: plt.Figure, name: str) -> None:
        path = os.path.join(self.save_dir, name)
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"    Plot saved: {path}")

    def plot_equity_curve(self, results: Dict[str, Any]) -> None:
        """Strategy vs Buy & Hold equity curve with annotation box."""
        m = results["metrics"]
        eq_s = results["equity_strategy"]
        eq_b = results["equity_benchmark"]
        ts = results.get("timestamps")

        fig, ax = plt.subplots(figsize=(14, 7))

        x = ts if ts is not None else np.arange(len(eq_s))
        ax.plot(x, eq_s, label="PPO Strategy", color="steelblue", linewidth=1.5)
        ax.plot(x, eq_b, label="Buy & Hold", color="gray", linewidth=1.0, alpha=0.7)

        # Annotation box
        text = (
            f"SR: {m['sharpe_ratio']:.4f}\n"
            f"PSR: {m['psr']:.4f}\n"
            f"Max DD: {m['max_drawdown']*100:.1f}%\n"
            f"Cum Ret: {m['cumulative_return']*100:.1f}%\n"
            f"Trades: {m['n_trades']}\n"
            f"Alpha: {m['alpha']*100:.1f}%"
        )
        props = dict(boxstyle="round,pad=0.5", facecolor="wheat", alpha=0.8)
        ax.text(
            0.02, 0.98, text, transform=ax.transAxes,
            fontsize=9, verticalalignment="top", bbox=props,
        )

        ax.set_title("PPO Strategy vs Buy & Hold — Equity Curve")
        ax.set_xlabel("Bar Index" if ts is None else "Date")
        ax.set_ylabel("Equity (starting at 1.0)")
        ax.legend(loc="lower right")
        ax.grid(True, alpha=0.3)

        self._save(fig, "equity_curve.png")

    def plot_action_distribution(self, results: Dict[str, Any]) -> None:
        """Price with colored actions + rolling action proportion."""
        actions = results["actions"]
        close = results["close_prices"]
        ts = results.get("timestamps")
        x = ts if ts is not None else np.arange(len(actions))

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[2, 1])

        # Top: price with colored scatter
        ax1.plot(x, close, color="gray", linewidth=0.5, alpha=0.5)
        colors = {1: "green", -1: "red", 0: "gold"}
        labels = {1: "Long", -1: "Short", 0: "Flat"}
        for pos, color in colors.items():
            mask = actions == pos
            if mask.any():
                ax1.scatter(
                    x[mask] if ts is not None else np.where(mask)[0],
                    close[mask], c=color, s=3, alpha=0.5, label=labels[pos],
                )
        ax1.set_title("Actions Over Time")
        ax1.set_ylabel("Close Price")
        ax1.legend(loc="upper left", markerscale=5)
        ax1.grid(True, alpha=0.3)

        # Bottom: rolling action proportion (100-bar window)
        window = min(100, len(actions) // 5)
        if window > 1:
            long_frac = pd.Series((actions == 1).astype(float)).rolling(window).mean()
            short_frac = pd.Series((actions == -1).astype(float)).rolling(window).mean()
            flat_frac = pd.Series((actions == 0).astype(float)).rolling(window).mean()

            ax2.fill_between(range(len(actions)), 0, long_frac, color="green", alpha=0.5, label="Long")
            ax2.fill_between(range(len(actions)), long_frac, long_frac + flat_frac, color="gold", alpha=0.5, label="Flat")
            ax2.fill_between(range(len(actions)), long_frac + flat_frac, 1.0, color="red", alpha=0.5, label="Short")
            ax2.set_ylabel("Action Proportion")
            ax2.set_xlabel("Bar Index")
            ax2.legend(loc="upper right")
            ax2.set_ylim(0, 1)
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        self._save(fig, "action_distribution.png")

    def plot_feature_importance(
        self,
        model: ActorCritic,
        feature_names: List[str],
        sample_features: np.ndarray,
        device: torch.device = torch.device("cpu"),
    ) -> None:
        """
        Gradient-based feature importance proxy.

        Computes mean |d(policy_logits)/d(input)| over a sample of observations.
        Only considers the market feature dimensions (excludes position state).
        """
        model.eval()
        n_market = len(feature_names)
        n_sample = min(1000, len(sample_features))
        indices = np.linspace(0, len(sample_features) - 1, n_sample, dtype=int)

        importances = np.zeros(n_market, dtype=np.float64)

        for idx in indices:
            # Build a dummy observation with zero position state
            obs = np.zeros(model.encoder[0].normalized_shape[0] if hasattr(model.encoder[0], 'normalized_shape') else sample_features.shape[1] + 3, dtype=np.float32)
            obs[:n_market] = sample_features[idx, :n_market]

            obs_t = torch.tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            obs_t.requires_grad_(True)

            dist, _ = model.forward(obs_t)
            # Sum of all logits as proxy for sensitivity
            logits_sum = dist.logits.sum()
            logits_sum.backward()

            grad = obs_t.grad[0, :n_market].abs().detach().numpy()
            importances += grad

        importances /= n_sample

        # Sort by importance
        order = np.argsort(importances)[::-1]
        sorted_names = [feature_names[i] for i in order]
        sorted_imp = importances[order]

        fig, ax = plt.subplots(figsize=(10, max(6, len(feature_names) * 0.4)))
        y_pos = np.arange(len(sorted_names))
        ax.barh(y_pos, sorted_imp, color="steelblue", alpha=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(sorted_names)
        ax.invert_yaxis()
        ax.set_xlabel("Mean |Gradient| (policy sensitivity)")
        ax.set_title("Feature Importance (Gradient-Based)")
        ax.grid(True, alpha=0.3, axis="x")

        plt.tight_layout()
        self._save(fig, "feature_importance.png")

    def plot_train_val_curves(self, logger: TrainingLogger) -> None:
        """Training reward and validation SR over updates, per fold."""
        df = logger.to_dataframe()
        if len(df) == 0:
            return

        folds = df["fold"].unique()
        n_folds = len(folds)

        fig, axes = plt.subplots(n_folds, 1, figsize=(14, 4 * n_folds), squeeze=False)

        for i, fold_id in enumerate(folds):
            fold_df = df[df["fold"] == fold_id]
            ax = axes[i, 0]

            ax2 = ax.twinx()
            ax.plot(fold_df["update"], fold_df["avg_reward"], color="steelblue", alpha=0.7, label="Avg Reward")
            ax2.plot(fold_df["update"], fold_df["val_sr"], color="darkorange", linewidth=1.5, label="Val SR")

            # Mark best val SR
            best_idx = fold_df["val_sr"].idxmax()
            if not np.isnan(fold_df.loc[best_idx, "val_sr"]):
                ax2.axvline(
                    fold_df.loc[best_idx, "update"],
                    color="red", linestyle="--", alpha=0.5, label="Best Val SR",
                )

            ax.set_xlabel("Update")
            ax.set_ylabel("Avg Reward", color="steelblue")
            ax2.set_ylabel("Validation SR", color="darkorange")
            ax.set_title(f"Fold {fold_id} — Training Curves")
            ax.grid(True, alpha=0.3)

            # Combined legend
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

        plt.tight_layout()
        self._save(fig, "train_val_sharpe.png")

    def plot_drawdown(self, results: Dict[str, Any]) -> None:
        """Underwater plot: drawdown % over time."""
        eq = results["equity_strategy"]
        ts = results.get("timestamps")
        x = ts if ts is not None else np.arange(len(eq))

        peak = np.maximum.accumulate(eq)
        drawdown = (eq - peak) / np.maximum(peak, 1e-12) * 100  # in %

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.fill_between(x, drawdown, 0, color="red", alpha=0.3)
        ax.plot(x, drawdown, color="red", linewidth=0.8)
        ax.set_title("Strategy Drawdown")
        ax.set_xlabel("Bar Index" if ts is None else "Date")
        ax.set_ylabel("Drawdown (%)")
        ax.grid(True, alpha=0.3)
        ax.set_ylim(min(drawdown) * 1.1, 1)

        self._save(fig, "drawdown.png")
