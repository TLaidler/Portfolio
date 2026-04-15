"""
=============================================================================
PPO-Based RL Trading — BTC/USDT
=============================================================================

Trains a Proximal Policy Optimization agent to trade BTC/USDT using
the same feature pipeline as regime_detection_advanced.py.

Usage:
    python neural_test/main.py
    python neural_test/main.py --config '{"lr": 1e-4}'
    python neural_test/main.py --inference-only

Output: save_point_neural/ (metrics, plots, trained model)
"""

import sys
import os
import json
import argparse
import time

# Add parent directory to path (same pattern as t8_mod3_test.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)

import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")

from regime_detection_advanced import (
    DollarBarBuilder,
    FeatureRegistry,
    ModelEvaluator,
    DEFAULT_CONFIG,
)

from neural_test.config import PPO_CONFIG, get_config
from neural_test.utils import (
    FeatureNormalizer,
    TrainingLogger,
    set_all_seeds,
    compute_sharpe_ratio,
)
from neural_test.model import ActorCritic
from neural_test.trainer import WalkForwardPPOTrainer
from neural_test.backtest import BacktestEngine, BacktestVisualizer


# ===========================================================================
# Data Loading (mirrors AdvancedPipeline._load_data + stages 2-3)
# ===========================================================================

def _load_optional_csv(data_dir: str, filename: str, label: str):
    """Load optional CSV; returns None if missing."""
    path = os.path.join(data_dir, filename)
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["timestamp"])
        print(f"    {label} loaded: {df.shape}")
        return df
    print(f"    [SKIP] {label} not found (optional)")
    return None


def load_and_preprocess(config: dict):
    """
    Reuse existing pipeline for data loading, dollar bars, and feature computation.

    Steps:
        1. Load btcusdt_1m.csv (+ optional exogenous CSVs)
        2. Build dollar bars with DollarBarBuilder
        3. Compute features with FeatureRegistry.compute_all()
        4. Drop NaN warmup rows
        5. Apply correlation filter

    Returns (df_features, feature_names)
    """
    data_dir = os.path.join(PARENT_DIR, config["data_dir"])

    # --- 1. Load data ---
    btc_path = os.path.join(data_dir, "btcusdt_1m.csv")
    if not os.path.exists(btc_path):
        print("    [ERROR] btcusdt_1m.csv not found. Run fetch_binance_data.py first.")
        raise FileNotFoundError(f"Data not found: {btc_path}")

    btc_df = pd.read_csv(btc_path, parse_dates=["timestamp"])
    print(f"    BTC 1-min loaded: {btc_df.shape}")

    fng_df = _load_optional_csv(data_dir, "fear_greed.csv", "Fear & Greed")
    funding_rate_df = _load_optional_csv(data_dir, "funding_rate.csv", "Funding Rate")
    vix_df = _load_optional_csv(data_dir, "vix.csv", "VIX")
    dxy_df = _load_optional_csv(data_dir, "dxy.csv", "DXY")

    # --- 2. Dollar bars ---
    bar_builder = DollarBarBuilder(
        calibration_days=config["dollar_bar_calibration_days"],
        bars_per_day=config["dollar_bars_per_day"],
    )
    bar_builder.calibrate_threshold(btc_df)
    dollar_bars = bar_builder.transform(btc_df)
    print(f"    Dollar bars: {len(dollar_bars)}")

    # --- 3. Feature engineering ---
    registry = FeatureRegistry()
    registry.register_defaults()

    feat_config = {
        **config,
        "_fng_df": fng_df,
        "_funding_rate_df": funding_rate_df,
        "_vix_df": vix_df,
        "_dxy_df": dxy_df,
    }
    df_feat, feature_names = registry.compute_all(dollar_bars, feat_config)

    # Drop warmup NaNs
    df_feat = df_feat.dropna(subset=feature_names).reset_index(drop=True)
    print(f"    Features computed: {len(feature_names)} columns, {len(df_feat)} bars")
    print(f"    Features: {feature_names}")

    # --- 4. Correlation filter (same as pipeline lines 2790-2813) ---
    corr_threshold = config.get("corr_drop_threshold", 0.85)
    if len(feature_names) > 1:
        corr_matrix = df_feat[feature_names].corr().abs()
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape, dtype=bool), k=1)
        )
        to_drop = set()
        for col in upper.columns:
            high_corr = upper.index[upper[col] > corr_threshold].tolist()
            for hc in high_corr:
                # Keep the one with higher variance
                if df_feat[col].var() >= df_feat[hc].var():
                    to_drop.add(hc)
                else:
                    to_drop.add(col)
        if to_drop:
            print(f"    Correlation filter: dropping {to_drop}")
            feature_names = [f for f in feature_names if f not in to_drop]

    return df_feat, feature_names


def split_data(df: pd.DataFrame, feature_names: list, config: dict):
    """
    Temporal train/val/test split. NEVER shuffle.

    Returns dict with keys "train", "val", "test", each containing:
        features, close, timestamps, returns
    """
    n = len(df)
    train_end = int(n * config["train_ratio"])
    val_end = int(n * (config["train_ratio"] + config["val_ratio"]))

    splits = {}
    for name, start, end in [
        ("train", 0, train_end),
        ("val", train_end, val_end),
        ("test", val_end, n),
    ]:
        slc = df.iloc[start:end].reset_index(drop=True)
        close = slc["close"].values.astype(np.float64)
        splits[name] = {
            "features": slc[feature_names].values.astype(np.float32),
            "close": close,
            "timestamps": slc["timestamp"].values if "timestamp" in slc.columns else None,
        }

    return splits


# ===========================================================================
# CLI
# ===========================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="PPO RL Trading — BTC/USDT")
    parser.add_argument(
        "--config", type=str, default="{}",
        help="JSON string with config overrides",
    )
    parser.add_argument(
        "--inference-only", action="store_true",
        help="Skip training, load model and run backtest only",
    )
    return parser.parse_args()


# ===========================================================================
# Main
# ===========================================================================

def main():
    args = parse_args()
    overrides = json.loads(args.config)
    config = get_config(overrides)

    set_all_seeds(config["rng_seed"])

    save_dir = os.path.join(SCRIPT_DIR, config["save_dir"])
    os.makedirs(save_dir, exist_ok=True)

    t_start = time.time()
    device = torch.device("cpu")

    # =================================================================
    # STEP 1: Load & Preprocess
    # =================================================================
    print("\n" + "=" * 70)
    print("  STEP 1: Loading data and computing features")
    print("=" * 70)
    df_feat, feature_names = load_and_preprocess(config)

    # =================================================================
    # STEP 2: Temporal Split
    # =================================================================
    print("\n" + "=" * 70)
    print("  STEP 2: Temporal split (train/val/test)")
    print("=" * 70)
    splits = split_data(df_feat, feature_names, config)
    for name, data in splits.items():
        print(f"    {name}: {len(data['close'])} bars")

    # =================================================================
    # STEP 3: Normalize Features
    # =================================================================
    print("\n" + "=" * 70)
    print("  STEP 3: Normalizing features (fit on train only)")
    print("=" * 70)
    normalizer = FeatureNormalizer()
    splits["train"]["features"] = normalizer.fit_transform(splits["train"]["features"])
    splits["val"]["features"] = normalizer.transform(splits["val"]["features"])
    splits["test"]["features"] = normalizer.transform(splits["test"]["features"])
    print(f"    Normalization stats computed on {len(splits['train']['close'])} training bars")

    if not args.inference_only:
        # =============================================================
        # STEP 4: Walk-Forward PPO Training
        # =============================================================
        print("\n" + "=" * 70)
        print("  STEP 4: Walk-forward PPO training")
        print("=" * 70)

        # Combine train + val for walk-forward (trainer handles the split)
        wf_features = np.concatenate(
            [splits["train"]["features"], splits["val"]["features"]], axis=0
        )
        wf_close = np.concatenate(
            [splits["train"]["close"], splits["val"]["close"]], axis=0
        )

        logger = TrainingLogger()
        trainer = WalkForwardPPOTrainer(
            features=wf_features,
            close_prices=wf_close,
            config=config,
            logger=logger,
        )
        train_results = trainer.train()

        # Save model
        model_path = os.path.join(save_dir, "ppo_model.pt")
        torch.save({
            "state_dict": train_results["best_state"],
            "obs_dim": train_results["obs_dim"],
            "n_actions": config["n_actions"],
            "hidden_dims": config["hidden_dims"],
            "dropout_rate": config["dropout_rate"],
            "use_layer_norm": config["use_layer_norm"],
            "feature_names": feature_names,
            "normalizer_mean": normalizer.mean_,
            "normalizer_std": normalizer.std_,
            "config": {k: v for k, v in config.items() if not k.startswith("_")},
        }, model_path)
        print(f"    Model saved: {model_path}")

        # Save training log
        logger.to_txt(os.path.join(save_dir, "training_log.txt"))

    else:
        # =============================================================
        # Load existing model
        # =============================================================
        print("\n" + "=" * 70)
        print("  STEP 4: Loading pre-trained model (inference-only)")
        print("=" * 70)
        model_path = os.path.join(save_dir, "ppo_model.pt")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No trained model found at {model_path}")

        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        train_results = {
            "best_state": checkpoint["state_dict"],
            "obs_dim": checkpoint["obs_dim"],
        }
        logger = TrainingLogger()
        print(f"    Model loaded from: {model_path}")

    # =================================================================
    # STEP 5: Backtest on Test Set
    # =================================================================
    print("\n" + "=" * 70)
    print("  STEP 5: Backtesting on test set")
    print("=" * 70)

    # Reconstruct model from best state
    obs_dim = train_results["obs_dim"]
    model = ActorCritic(
        obs_dim=obs_dim,
        n_actions=config["n_actions"],
        hidden_dims=config["hidden_dims"],
        dropout_rate=config["dropout_rate"],
        use_layer_norm=config["use_layer_norm"],
    ).to(device)
    model.load_state_dict(train_results["best_state"])
    model.eval()

    print(f"    Model parameters: {model.count_parameters()}")

    engine = BacktestEngine(config)
    results = engine.run(
        model,
        splits["test"]["features"],
        splits["test"]["close"],
        timestamps=splits["test"]["timestamps"],
        device=device,
    )
    engine.save_report(results, save_dir)

    # =================================================================
    # STEP 6: Visualizations
    # =================================================================
    print("\n" + "=" * 70)
    print("  STEP 6: Generating visualizations")
    print("=" * 70)

    viz = BacktestVisualizer(save_dir)
    viz.plot_equity_curve(results)
    viz.plot_action_distribution(results)
    viz.plot_feature_importance(model, feature_names, splits["test"]["features"], device)
    viz.plot_train_val_curves(logger)
    viz.plot_drawdown(results)

    # =================================================================
    # STEP 7: Save Config
    # =================================================================
    config_txt = "PPO NEURAL TEST CONFIGURATION\n" + "=" * 60 + "\n\n"
    for k, v in sorted(config.items()):
        if not k.startswith("_"):
            config_txt += f"  {k}: {v}\n"
    config_path = os.path.join(save_dir, "config.txt")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_txt)
    print(f"    Config saved: {config_path}")

    # =================================================================
    # Summary
    # =================================================================
    elapsed = time.time() - t_start
    m = results["metrics"]
    print(f"\n{'=' * 70}")
    print(f"  COMPLETE in {elapsed:.1f}s")
    print(f"  Results saved to: {save_dir}")
    print(f"{'=' * 70}")
    print(f"\n  Strategy SR:  {m['sharpe_ratio']:.4f}  |  B&H SR: {m['bh_sharpe_ratio']:.4f}")
    print(f"  Strategy Ret: {m['cumulative_return']*100:+.2f}%  |  B&H Ret: {m['bh_cumulative_return']*100:+.2f}%")
    print(f"  Max DD:       {m['max_drawdown']*100:.2f}%  |  Trades: {m['n_trades']}")
    print(f"  PSR:          {m['psr']:.4f}  |  Alpha: {m['alpha']*100:+.2f}%")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
