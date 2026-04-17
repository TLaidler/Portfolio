"""Information-driven bars (AFML Ch. 2).

Time bars oversample low-activity periods and undersample fast ones, which
produces heteroscedastic returns. Dollar bars sample by accumulated traded
value, which restores partial normality and adapts to regimes of volatility.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass
class DollarBarBuilder:
    """Aggregate 1-minute OHLCV into dollar bars.

    Parameters
    ----------
    bars_per_day : target number of dollar bars per day. The threshold is
        calibrated from the first 20% of the training data as
        mean(dollar_volume_per_day) / bars_per_day.
    """

    bars_per_day: int = 100
    calibration_fraction: float = 0.2

    def _calibrate_threshold(self, df: pd.DataFrame) -> float:
        sample = df.iloc[: max(1, int(len(df) * self.calibration_fraction))]
        daily_dv = (sample["close"] * sample["volume"]).groupby(
            sample.index.floor("D")
        ).sum()
        return float(daily_dv.mean() / self.bars_per_day)

    def build(self, minute_df: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame indexed by bar close time with OHLCV columns.

        Input must have columns {open, high, low, close, volume} and a
        datetime index. Vectorised by cumulative dollar-volume: bar k ends
        at the first minute where cumulative dollar volume crosses
        k * threshold.
        """
        df = minute_df.sort_index()
        threshold = self._calibrate_threshold(df)

        closes = df["close"].to_numpy()
        volumes = df["volume"].to_numpy()
        cum_dv = np.cumsum(closes * volumes)

        n_bars = int(cum_dv[-1] // threshold)
        if n_bars < 2:
            raise ValueError("Threshold too large — got fewer than 2 dollar bars.")
        bar_ends = np.searchsorted(cum_dv, np.arange(1, n_bars + 1) * threshold)
        bar_ends = np.clip(bar_ends, 0, len(df) - 1)

        opens, highs_, lows_, closes_, vols_, dv_, ts_ = [], [], [], [], [], [], []
        start = 0
        opens_arr = df["open"].to_numpy()
        highs_arr = df["high"].to_numpy()
        lows_arr = df["low"].to_numpy()
        for end in bar_ends:
            if end < start:
                continue
            opens.append(opens_arr[start])
            highs_.append(highs_arr[start:end + 1].max())
            lows_.append(lows_arr[start:end + 1].min())
            closes_.append(closes[end])
            vols_.append(volumes[start:end + 1].sum())
            dv_.append(cum_dv[end] - (cum_dv[start - 1] if start > 0 else 0.0))
            ts_.append(df.index[end])
            start = end + 1

        bars = pd.DataFrame({
            "open": opens, "high": highs_, "low": lows_, "close": closes_,
            "volume": vols_, "dollar_volume": dv_,
        }, index=pd.DatetimeIndex(ts_, name="timestamp"))
        bars.attrs["threshold"] = threshold
        return bars


def summarize_bars(bars: pd.DataFrame) -> dict:
    rets = bars["close"].pct_change().dropna()
    return {
        "n_bars": int(len(bars)),
        "threshold_dollars": float(bars.attrs.get("threshold", np.nan)),
        "bars_per_day_mean": float(
            bars.groupby(bars.index.floor("D")).size().mean()
        ),
        "ret_mean": float(rets.mean()),
        "ret_std": float(rets.std()),
        "ret_skew": float(rets.skew()),
        "ret_kurt": float(rets.kurt()),
        "start": str(bars.index.min()),
        "end": str(bars.index.max()),
    }
