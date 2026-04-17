# Regime Detection Pipeline — CLAUDE.md

## Architecture

Monolithic ML pipeline (`regime_detection_advanced.py`, ~2744 lines, 28 classes)
implementing AFML/MLAM methodology for BTC/USDT regime detection.

Key components: DollarBarBuilder, TripleBarrierLabeler, CPCV, MDAFeatureSelector,
MetaLabeler, AdvancedPipeline (orchestrator).

## Critical Rules

- **savgol_causal**: ONLY import from `utils/savgol.py`. Do NOT redefine locally.
  The canonical version uses edge-padding to avoid zero-padding artifacts.
- **No look-ahead**: All features must be causal. SavGol uses `pos=window-1`.
- **Anti-leakage**: CPCV with purging + embargo. Never use future data in features.

## How to Run

```bash
# Main pipeline (trains model, generates save_point_advanced/)
python regime_detection_advanced.py

# Hypothesis testing (T1-T7+, generates relatorios/)
python hypothesis_testing.py

# Benchmarks (from benchmarking/ dir)
cd benchmarking && python momentum_benchmark.py
```

## Data

- `data/btcusdt_1m.csv` (~148MB, 2021-03 to 2025-07) — not in git, fetch via:
  ```bash
  python fetch_binance_data.py
  ```
- `data/*.xlsx` — SP500, DXY, IBOV (also gitignored)
- `new_data/` — OOS bear market data (aug/2025-mar/2026)

## Directory Structure

```
regime_detection_advanced.py   # Main pipeline (monolith, do NOT split yet)
hypothesis_testing.py          # Scientific validation (T1-T11)
rd_adv_application.py          # OOS application script
utils/savgol.py                # Canonical savgol_causal (SINGLE SOURCE OF TRUTH)
benchmarking/                  # Momentum benchmarks and grid searches
archive/                       # Legacy scripts (marcos.py, regime_detection_rf.py)
relatorios/                    # Reports (.md) and plots (pngs/, gitignored)
data/                          # Market data (gitignored)
```

## Current Research Status

- Discovery: dollar bars + SavGol causal generate adaptive momentum (SR~0.18 across
  BTC, SP500, IBOV)
- Validation needed: T8 (random walk null), T9 (independent trade SR),
  T10 (bear market), T11 (SavGol-as-instrument)
- SavGol edge-padding bug fixed 2026-03-25 (all previous models may need retraining)
