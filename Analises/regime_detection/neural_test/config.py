"""
Centralized configuration for PPO-based RL trading module.

Extends DEFAULT_CONFIG from regime_detection_advanced.py with
RL-specific hyperparameters. Use get_config() to merge at runtime.
"""

from typing import Any, Dict, Optional


PPO_CONFIG: Dict[str, Any] = {
    # ===== Network Architecture =====
    "hidden_dims": [64, 64],          # Shared encoder layers (~5k params total)
    "dropout_rate": 0.10,             # Dropout on hidden layers (off during eval)
    "use_layer_norm": True,           # LayerNorm before each hidden layer

    # ===== PPO Hyperparameters =====
    "gamma": 0.99,                    # Discount factor (~100-bar effective horizon)
    "gae_lambda": 0.95,              # GAE bias-variance tradeoff
    "clip_epsilon": 0.2,             # PPO clipping parameter
    "entropy_coef": 0.01,            # Entropy bonus (exploration)
    "value_coef": 0.5,               # Value loss weight
    "max_grad_norm": 0.5,            # Gradient clipping
    "ppo_epochs": 4,                 # PPO update epochs per rollout
    "num_minibatches": 4,            # Minibatches per PPO epoch
    "lr": 3e-4,                      # Initial learning rate (Adam)
    "lr_end": 1e-5,                  # Final learning rate (linear decay)
    "rollout_steps": 512,            # Transitions per rollout (~25 trading days)

    # ===== Walk-Forward Validation =====
    "min_train_bars": 3600,          # Minimum training bars (~6 months at 20 bars/day)
    "val_bars": 1800,                # Validation window (~3 months)
    "step_bars": 1800,               # Step forward between folds (~3 months)
    "embargo_bars": 50,              # Embargo gap (same as max_holding_bars)

    # ===== Early Stopping =====
    "patience": 15,                  # Updates without val SR improvement
    "max_updates_per_fold": 200,     # Hard cap per walk-forward fold

    # ===== Reward Shaping =====
    "lambda_drawdown": 0.5,          # Drawdown penalty coefficient
    "drawdown_threshold": 0.02,      # 2% drawdown tolerance before penalty
    "lambda_idle": 0.0001,           # Idle penalty when flat + high vol
    "reward_scale": 100.0,           # Scale reward for PPO stability

    # ===== Data Splits =====
    "train_ratio": 0.60,             # 60% train (walk-forward needs val set)
    "val_ratio": 0.20,               # 20% validation
    "test_ratio": 0.20,              # 20% final test (never touched during training)

    # ===== Environment =====
    "n_actions": 3,                  # 0=flat, 1=long, 2=short
    "max_holding_bars": 50,          # For position-state normalization

    # ===== Output =====
    "save_dir": "save_point_neural",

    # ===== Reproducibility =====
    "rng_seed": 42,
}


def get_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Merge DEFAULT_CONFIG + PPO_CONFIG + optional overrides.

    Import of DEFAULT_CONFIG is deferred to avoid circular imports
    when config.py is imported from other modules.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from regime_detection_advanced import DEFAULT_CONFIG

    merged = {**DEFAULT_CONFIG, **PPO_CONFIG}
    if overrides:
        merged.update(overrides)
    return merged
