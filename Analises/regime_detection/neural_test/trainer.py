"""
Walk-forward PPO trainer with early stopping on validation Sharpe.

Expanding-window walk-forward:
    Fold 0: train=[0, min_train_bars), val=[min_train_bars+embargo, min_train_bars+embargo+val_bars)
    Fold 1: train=[0, min_train_bars+step_bars), val=[...+embargo, ...+embargo+val_bars)
    ...
    Final fold uses all available training data.

Per fold:
    1. Collect rollout_steps transitions in train env
    2. Compute GAE advantages
    3. PPO update (ppo_epochs over num_minibatches)
    4. Evaluate greedy on validation -> compute SR
    5. Early stop if val SR doesn't improve for patience updates
"""

import copy
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from .environment import TradingEnv, ACTION_TO_POSITION
from .model import ActorCritic
from .utils import (
    TrainingLogger,
    compute_sharpe_ratio,
    compute_strategy_returns,
)


# ===========================================================================
# Rollout Buffer
# ===========================================================================

class RolloutBuffer:
    """
    Stores trajectory data for PPO updates and computes GAE advantages.

    All arrays are pre-allocated for rollout_steps transitions.
    """

    def __init__(self, rollout_steps: int, obs_dim: int):
        self.rollout_steps = rollout_steps
        self.obs = np.zeros((rollout_steps, obs_dim), dtype=np.float32)
        self.actions = np.zeros(rollout_steps, dtype=np.int64)
        self.log_probs = np.zeros(rollout_steps, dtype=np.float32)
        self.rewards = np.zeros(rollout_steps, dtype=np.float32)
        self.values = np.zeros(rollout_steps, dtype=np.float32)
        self.dones = np.zeros(rollout_steps, dtype=np.float32)
        self.advantages = np.zeros(rollout_steps, dtype=np.float32)
        self.returns = np.zeros(rollout_steps, dtype=np.float32)
        self.ptr = 0

    def add(
        self,
        obs: np.ndarray,
        action: int,
        log_prob: float,
        reward: float,
        value: float,
        done: bool,
    ) -> None:
        idx = self.ptr
        self.obs[idx] = obs
        self.actions[idx] = action
        self.log_probs[idx] = log_prob
        self.rewards[idx] = reward
        self.values[idx] = value
        self.dones[idx] = float(done)
        self.ptr += 1

    def compute_gae(
        self, last_value: float, gamma: float, gae_lambda: float
    ) -> None:
        """
        Compute GAE advantages and discounted returns.

        GAE: A_t = sum_{l=0}^{T-t} (gamma * lambda)^l * delta_{t+l}
        where delta_t = r_t + gamma * V(s_{t+1}) * (1-done) - V(s_t)
        """
        n = self.ptr
        gae = 0.0
        for t in reversed(range(n)):
            if t == n - 1:
                next_value = last_value
                next_non_terminal = 1.0 - self.dones[t]
            else:
                next_value = self.values[t + 1]
                next_non_terminal = 1.0 - self.dones[t]

            delta = (
                self.rewards[t]
                + gamma * next_value * next_non_terminal
                - self.values[t]
            )
            gae = delta + gamma * gae_lambda * next_non_terminal * gae
            self.advantages[t] = gae

        self.returns[: n] = self.advantages[: n] + self.values[: n]

    def get_tensors(self, device: torch.device) -> Dict[str, torch.Tensor]:
        """Convert buffer arrays to torch tensors for PPO update."""
        n = self.ptr
        return {
            "obs": torch.tensor(self.obs[:n], device=device),
            "actions": torch.tensor(self.actions[:n], device=device),
            "old_log_probs": torch.tensor(self.log_probs[:n], device=device),
            "advantages": torch.tensor(self.advantages[:n], device=device),
            "returns": torch.tensor(self.returns[:n], device=device),
        }

    def reset(self) -> None:
        self.ptr = 0


# ===========================================================================
# Walk-Forward PPO Trainer
# ===========================================================================

class WalkForwardPPOTrainer:
    """
    Walk-forward PPO training with early stopping on validation Sharpe.

    Parameters
    ----------
    features : np.ndarray
        Shape (T, n_features). Full dataset (train+val), normalized.
    close_prices : np.ndarray
        Shape (T,). Full dataset close prices.
    config : dict
        Complete merged configuration.
    logger : TrainingLogger
        For tracking metrics across folds and updates.
    """

    def __init__(
        self,
        features: np.ndarray,
        close_prices: np.ndarray,
        config: Dict[str, Any],
        logger: TrainingLogger,
    ):
        self.features = features
        self.close_prices = close_prices
        self.config = config
        self.logger = logger

        # Device (CPU for reproducibility and small model)
        self.device = torch.device("cpu")

        # Pre-compute actual returns for evaluation
        self.actual_returns = np.zeros(len(close_prices), dtype=np.float64)
        self.actual_returns[1:] = np.diff(close_prices) / np.maximum(
            close_prices[:-1], 1e-12
        )

    def _generate_folds(
        self, n_total: int
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Generate (train_range, val_range) tuples for expanding walk-forward.

        Returns list of ((train_start, train_end), (val_start, val_end)).
        """
        min_train = self.config["min_train_bars"]
        val_bars = self.config["val_bars"]
        step_bars = self.config["step_bars"]
        embargo = self.config["embargo_bars"]

        folds = []
        train_end = min_train

        while True:
            val_start = train_end + embargo
            val_end = val_start + val_bars

            if val_end > n_total:
                # Final fold: use whatever remains for validation
                val_end = n_total
                if val_end - val_start < embargo:
                    break
                folds.append(((0, train_end), (val_start, val_end)))
                break

            folds.append(((0, train_end), (val_start, val_end)))
            train_end += step_bars

        return folds

    def _create_env(
        self, start: int, end: int
    ) -> TradingEnv:
        """Create a TradingEnv for a data segment."""
        return TradingEnv(
            features=self.features[start:end],
            close_prices=self.close_prices[start:end],
            config=self.config,
        )

    def _evaluate_greedy(
        self,
        model: ActorCritic,
        features_seg: np.ndarray,
        close_seg: np.ndarray,
    ) -> Tuple[float, np.ndarray]:
        """
        Run greedy policy on a segment. Returns (sharpe_ratio, actions).
        """
        model.eval()
        env = TradingEnv(features_seg, close_seg, self.config)
        obs = env.reset()

        actions = []
        while True:
            obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device)
            action = model.get_greedy_action(obs_t)
            actions.append(ACTION_TO_POSITION[action])

            obs, _, done, _ = env.step(action)
            if done:
                break

        actions = np.array(actions, dtype=np.float64)

        # Compute returns with realistic fees
        actual_ret = np.zeros(len(close_seg), dtype=np.float64)
        actual_ret[1:] = np.diff(close_seg) / np.maximum(close_seg[:-1], 1e-12)
        # Actions correspond to bars [0..N-2] deciding position for that bar
        # Align: strategy_returns[t] = actions[t] * actual_ret[t]
        strat_ret = compute_strategy_returns(
            actions,
            actual_ret[: len(actions)],
            fee_maker=self.config["fee_maker"],
            fee_taker=self.config["fee_taker"],
            fee_mode=self.config["fee_mode"],
        )
        sr = compute_sharpe_ratio(strat_ret)
        model.train()
        return sr, actions

    def _ppo_update(
        self,
        model: ActorCritic,
        optimizer: torch.optim.Adam,
        buffer: RolloutBuffer,
    ) -> Dict[str, float]:
        """
        Single PPO update: multiple epochs over minibatches.

        Returns dict with policy_loss, value_loss, entropy, clip_fraction.
        """
        data = buffer.get_tensors(self.device)
        obs = data["obs"]
        actions = data["actions"]
        old_log_probs = data["old_log_probs"]
        advantages = data["advantages"]
        returns = data["returns"]

        # Normalize advantages
        adv_std = advantages.std()
        if adv_std > 1e-8:
            advantages = (advantages - advantages.mean()) / adv_std

        n = len(obs)
        clip_eps = self.config["clip_epsilon"]
        entropy_coef = self.config["entropy_coef"]
        value_coef = self.config["value_coef"]
        max_grad_norm = self.config["max_grad_norm"]
        num_minibatches = self.config["num_minibatches"]
        ppo_epochs = self.config["ppo_epochs"]

        batch_size = max(n // num_minibatches, 1)

        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0
        total_clip_frac = 0.0
        n_updates = 0

        for _ in range(ppo_epochs):
            indices = torch.randperm(n, device=self.device)

            for start in range(0, n, batch_size):
                end = min(start + batch_size, n)
                mb_idx = indices[start:end]

                mb_obs = obs[mb_idx]
                mb_actions = actions[mb_idx]
                mb_old_log_probs = old_log_probs[mb_idx]
                mb_advantages = advantages[mb_idx]
                mb_returns = returns[mb_idx]

                _, new_log_probs, entropy, values = model.get_action_and_value(
                    mb_obs, mb_actions
                )

                # Policy loss (clipped surrogate)
                ratio = torch.exp(new_log_probs - mb_old_log_probs)
                surr1 = ratio * mb_advantages
                surr2 = torch.clamp(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * mb_advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                # Value loss
                value_loss = nn.functional.mse_loss(values, mb_returns)

                # Entropy bonus
                entropy_mean = entropy.mean()

                # Total loss
                loss = policy_loss + value_coef * value_loss - entropy_coef * entropy_mean

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                optimizer.step()

                # Track metrics
                with torch.no_grad():
                    clip_frac = ((ratio - 1.0).abs() > clip_eps).float().mean()

                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy_mean.item()
                total_clip_frac += clip_frac.item()
                n_updates += 1

        return {
            "policy_loss": total_policy_loss / max(n_updates, 1),
            "value_loss": total_value_loss / max(n_updates, 1),
            "entropy": total_entropy / max(n_updates, 1),
            "clip_fraction": total_clip_frac / max(n_updates, 1),
        }

    def _train_single_fold(
        self,
        fold_idx: int,
        train_range: Tuple[int, int],
        val_range: Tuple[int, int],
    ) -> Dict[str, Any]:
        """
        Train PPO on one walk-forward fold with early stopping.

        Returns dict with best model state, best val SR, histories.
        """
        tr_start, tr_end = train_range
        va_start, va_end = val_range

        print(f"\n  Fold {fold_idx}: train=[0, {tr_end}), val=[{va_start}, {va_end})")
        print(f"    Train bars: {tr_end - tr_start}, Val bars: {va_end - va_start}")

        # Create training environment
        env = self._create_env(tr_start, tr_end)

        # Create model and optimizer
        obs_dim = env.obs_dim
        model = ActorCritic(
            obs_dim=obs_dim,
            n_actions=self.config["n_actions"],
            hidden_dims=self.config["hidden_dims"],
            dropout_rate=self.config["dropout_rate"],
            use_layer_norm=self.config["use_layer_norm"],
        ).to(self.device)
        print(f"    Model parameters: {model.count_parameters()}")

        # Linear LR schedule
        lr_start = self.config["lr"]
        lr_end = self.config["lr_end"]
        max_updates = self.config["max_updates_per_fold"]
        optimizer = torch.optim.Adam(model.parameters(), lr=lr_start, eps=1e-5)

        # Buffers
        rollout_steps = self.config["rollout_steps"]
        buffer = RolloutBuffer(rollout_steps, obs_dim)

        # Early stopping state
        patience = self.config["patience"]
        best_val_sr = -np.inf
        patience_counter = 0
        best_state = None
        gamma = self.config["gamma"]
        gae_lambda = self.config["gae_lambda"]

        # Initialize environment
        obs = env.reset()
        train_rewards = []

        for update_idx in range(max_updates):
            # --- LR schedule ---
            frac = update_idx / max(max_updates - 1, 1)
            lr = lr_start + frac * (lr_end - lr_start)
            for param_group in optimizer.param_groups:
                param_group["lr"] = lr

            # --- Collect rollout ---
            model.eval()
            buffer.reset()
            episode_reward = 0.0

            for step in range(rollout_steps):
                obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device)

                with torch.no_grad():
                    action, log_prob, _, value = model.get_action_and_value(obs_t)

                action_int = action.item()
                log_prob_val = log_prob.item()
                value_val = value.item()

                next_obs, reward, done, info = env.step(action_int)
                buffer.add(obs, action_int, log_prob_val, reward, value_val, done)
                episode_reward += reward

                if done:
                    # Wrap around: restart from beginning of training segment
                    obs = env.reset()
                else:
                    obs = next_obs

            # Compute last value for GAE
            with torch.no_grad():
                obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device)
                _, last_value = model.forward(obs_t)
                last_value = last_value.item()

            buffer.compute_gae(last_value, gamma, gae_lambda)
            avg_reward = episode_reward / rollout_steps
            train_rewards.append(avg_reward)

            # --- PPO update ---
            model.train()
            update_metrics = self._ppo_update(model, optimizer, buffer)

            # --- Evaluate on validation ---
            val_sr, _ = self._evaluate_greedy(
                model,
                self.features[va_start:va_end],
                self.close_prices[va_start:va_end],
            )

            # Log
            self.logger.log(
                fold=fold_idx,
                update=update_idx,
                lr=lr,
                avg_reward=avg_reward,
                val_sr=val_sr,
                **update_metrics,
            )

            # Early stopping check
            if val_sr > best_val_sr:
                best_val_sr = val_sr
                best_state = copy.deepcopy(model.state_dict())
                patience_counter = 0
            else:
                patience_counter += 1

            # Progress print every 10 updates
            if update_idx % 10 == 0 or patience_counter >= patience:
                print(
                    f"    Update {update_idx:3d} | "
                    f"avg_rew={avg_reward:.4f} | "
                    f"val_SR={val_sr:.4f} | "
                    f"best_SR={best_val_sr:.4f} | "
                    f"entropy={update_metrics['entropy']:.4f} | "
                    f"patience={patience_counter}/{patience}"
                )

            if patience_counter >= patience:
                print(f"    Early stopping at update {update_idx}")
                break

        # If no improvement at all, save last state
        if best_state is None:
            best_state = copy.deepcopy(model.state_dict())

        return {
            "fold_idx": fold_idx,
            "best_val_sr": best_val_sr,
            "train_range": train_range,
            "val_range": val_range,
            "n_updates": update_idx + 1,
            "best_state": best_state,
            "obs_dim": obs_dim,
        }

    def train(self) -> Dict[str, Any]:
        """
        Run full walk-forward training.

        Returns dict with per-fold results and the best overall model state.
        """
        n_total = len(self.features)
        folds = self._generate_folds(n_total)

        if not folds:
            raise ValueError(
                f"Not enough data for walk-forward. "
                f"Need at least {self.config['min_train_bars'] + self.config['embargo_bars'] + 100} bars, "
                f"got {n_total}."
            )

        print(f"\n  Walk-forward: {len(folds)} folds over {n_total} bars")
        for i, (tr, va) in enumerate(folds):
            print(f"    Fold {i}: train=[{tr[0]}, {tr[1]}) val=[{va[0]}, {va[1]})")

        fold_results = []
        best_overall_sr = -np.inf
        best_overall_state = None
        best_obs_dim = None

        for fold_idx, (train_range, val_range) in enumerate(folds):
            result = self._train_single_fold(fold_idx, train_range, val_range)
            fold_results.append(result)

            if result["best_val_sr"] > best_overall_sr:
                best_overall_sr = result["best_val_sr"]
                best_overall_state = result["best_state"]
                best_obs_dim = result["obs_dim"]

        # Summary
        val_srs = [r["best_val_sr"] for r in fold_results]
        print(f"\n  Walk-forward complete:")
        print(f"    Val SRs per fold: {[f'{s:.4f}' for s in val_srs]}")
        print(f"    Mean val SR: {np.mean(val_srs):.4f}")
        print(f"    Best val SR: {best_overall_sr:.4f}")

        return {
            "fold_results": fold_results,
            "best_state": best_overall_state,
            "best_val_sr": best_overall_sr,
            "obs_dim": best_obs_dim,
            "n_folds": len(folds),
        }
