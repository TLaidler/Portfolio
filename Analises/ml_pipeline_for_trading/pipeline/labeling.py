"""Triple-Barrier labeling and Meta-Labeling (AFML Ch. 3).

Instead of fixed horizon returns, we label each event by which of three
barriers is touched first: profit-taking, stop-loss, or a vertical (time)
barrier. Horizontal barriers are scaled to each point's ex-ante volatility
estimate so the experiment is scale-invariant across regimes.

Meta-labels layer a secondary ML model on top of a primary rule to decide
only the bet *size* (or whether to bet), inheriting the primary's direction.
This resolves the precision/recall trade-off cleanly (AFML 3.6).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------
# Ex-ante daily volatility (AFML 3.1)
# --------------------------------------------------------------------------

def daily_volatility(close: pd.Series, span: int = 100) -> pd.Series:
    """EWMA std of ~1-day returns, aligned to bar times (AFML 3.1).

    No back-fill: the earliest observations (before we have a lookback of
    1 day) remain NaN so they cannot silently inherit future variance —
    `build_events` treats NaN `trgt` as "no event" via the `vol > min_ret`
    mask.
    """
    pos = close.index.searchsorted(close.index - pd.Timedelta(days=1))
    valid = pos > 0
    ret = pd.Series(np.nan, index=close.index)
    ret.iloc[np.where(valid)[0]] = (
        close.iloc[np.where(valid)[0]].values
        / close.iloc[pos[valid] - 1].values - 1.0
    )
    return ret.ewm(span=span).std()


# --------------------------------------------------------------------------
# Triple barrier
# --------------------------------------------------------------------------

@dataclass
class BarrierConfig:
    pt_sl: tuple = (1.0, 1.0)       # profit-taking / stop-loss multiples of vol
    vertical_bars: int = 20         # vertical barrier horizon, in bars
    min_ret: float = 0.0            # drop events with vol below this
    sample_every: int = 1           # CUSUM-like thinning not applied here


def vertical_barriers(close: pd.Series, horizon_bars: int) -> pd.Series:
    """For each event at t, return t + horizon_bars (bar-time) or NaT."""
    shifted = close.index.to_series().shift(-horizon_bars)
    return shifted


def apply_triple_barrier(
    close: pd.Series,
    events: pd.DataFrame,
    pt_sl: tuple = (1.0, 1.0),
) -> pd.DataFrame:
    """For each event row (t0 -> t1, target=vol, side=+1/-1), find first touch.

    Returns a DataFrame with columns {t1, ret, bin, touch}. Uses integer
    positions to avoid repeated datetime lookups on large indices.
    """
    idx = close.index
    pos_of = {ts: i for i, ts in enumerate(idx)}
    prices = close.to_numpy()

    out = pd.DataFrame(
        index=events.index,
        data={"t1": events["t1"], "ret": np.nan, "bin": 0, "touch": "vertical"},
    )

    for t0, row in events.iterrows():
        if pd.isna(row["t1"]):
            continue
        i0 = pos_of.get(t0)
        i1 = pos_of.get(row["t1"])
        if i0 is None or i1 is None or i1 <= i0:
            continue
        p0 = prices[i0]
        path = prices[i0:i1 + 1]
        signed_ret = (path / p0 - 1.0) * row["side"]

        pt = pt_sl[0] * row["trgt"] if pt_sl[0] > 0 else np.inf
        sl = -pt_sl[1] * row["trgt"] if pt_sl[1] > 0 else -np.inf
        pt_hit = np.argmax(signed_ret > pt) if (signed_ret > pt).any() else -1
        sl_hit = np.argmax(signed_ret < sl) if (signed_ret < sl).any() else -1

        candidates = [(len(signed_ret) - 1, "vertical")]
        if pt_hit >= 0:
            candidates.append((pt_hit, "pt"))
        if sl_hit >= 0:
            candidates.append((sl_hit, "sl"))
        k, label = min(candidates, key=lambda x: x[0])

        r = float(signed_ret[k])
        out.at[t0, "t1"] = idx[i0 + k]
        out.at[t0, "ret"] = r
        out.at[t0, "bin"] = int(np.sign(r)) if r != 0 else 0
        out.at[t0, "touch"] = label
    return out


def build_events(
    close: pd.Series,
    vol: pd.Series,
    side: pd.Series,
    cfg: BarrierConfig,
) -> pd.DataFrame:
    """Assemble the events DataFrame for triple-barrier labeling.

    side is the *primary* model's signal: +1 long, -1 short, 0 no bet.
    Only non-zero side rows are kept.
    """
    mask = (side != 0) & (vol > cfg.min_ret)
    events = pd.DataFrame(index=close.index[mask])
    events["t1"] = vertical_barriers(close, cfg.vertical_bars).loc[events.index]
    events["trgt"] = vol.loc[events.index]
    events["side"] = side.loc[events.index]
    return events.dropna(subset=["t1"])


# --------------------------------------------------------------------------
# Meta-labeling (AFML 3.6)
# --------------------------------------------------------------------------

def meta_label(labels: pd.DataFrame) -> pd.Series:
    """Convert triple-barrier labels to meta-labels {0,1}.

    Given that the primary model chose a side, the secondary label is 1 if
    the event realised a non-negative return (primary was right), else 0.
    """
    return (labels["ret"] > 0).astype(int).rename("meta_bin")
