"""Data loaders. Reads the .csv files in data/ and new_data/ into clean
DataFrames / Series with UTC DatetimeIndex.
"""
from __future__ import annotations

import json
import urllib.request
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


def fetch_bacen_cdi(
    start: pd.Timestamp,
    end: pd.Timestamp,
    cache_path: Path | None = None,
    series_code: int = 12,
) -> pd.Series:
    """Daily CDI (% per business day) from Bacen SGS API.

    Série 12 = Taxa CDI diária em percentual (ex.: 0.043739 ≈ 0.0437%/dia,
    equivalente a ~11.63% a.a. em base 252). A série é indexada por dia útil
    em UTC. Valores estão em **percentual diário**. Usa cache local em CSV
    quando `cache_path` é fornecido.
    """
    start = pd.Timestamp(start).tz_convert("UTC") if pd.Timestamp(start).tzinfo else pd.Timestamp(start).tz_localize("UTC")
    end = pd.Timestamp(end).tz_convert("UTC") if pd.Timestamp(end).tzinfo else pd.Timestamp(end).tz_localize("UTC")

    if cache_path and Path(cache_path).exists():
        cached = pd.read_csv(cache_path, parse_dates=["date"])
        cached["date"] = pd.to_datetime(cached["date"], utc=True)
        cached = cached.set_index("date").sort_index()
        if cached.index.min() <= start and cached.index.max() >= end:
            return cached["cdi_daily_pct"].loc[start:end]

    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados"
        f"?formato=json&dataInicial={start:%d/%m/%Y}&dataFinal={end:%d/%m/%Y}"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["data"], dayfirst=True).dt.tz_localize("UTC")
    df["cdi_daily_pct"] = df["valor"].astype(float)
    df = df.set_index("date").sort_index()[["cdi_daily_pct"]]

    if cache_path:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        df.reset_index().to_csv(cache_path, index=False)
    return df["cdi_daily_pct"]


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
