"""Data loaders. Reads the .csv files in data/ and new_data/ into clean
DataFrames / Series with UTC DatetimeIndex.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


def _to_utc_index(df: pd.DataFrame, col: str = "timestamp") -> pd.DataFrame:
    df[col] = pd.to_datetime(df[col], utc=True, format="mixed")
    return df.set_index(col).sort_index()


def load_minute_bars(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return _to_utc_index(df)


def load_single_value(csv_path: Path, value_col: str) -> pd.Series:
    df = pd.read_csv(csv_path)
    df = _to_utc_index(df)
    return df[value_col].astype(float).dropna().rename(csv_path.stem)


def load_exogenous(folder: Path) -> Dict[str, pd.Series]:
    """Return {name: series} for vix, dxy, fear_greed, funding_rate."""
    out: Dict[str, pd.Series] = {}
    files = {
        "vix":          ("vix.csv", "close"),
        "dxy":          ("dxy.csv", "close"),
        "fear_greed":   ("fear_greed.csv", "fear_greed"),
        "funding_rate": ("funding_rate.csv", "funding_rate"),
        "etf_volume":   ("etf_btc_volume.csv", "volume"),
    }
    for name, (fname, col) in files.items():
        p = folder / fname
        if p.exists():
            try:
                out[name] = load_single_value(p, col)
            except Exception as e:
                print(f"[io] skipping {fname}: {e}")
    return out
