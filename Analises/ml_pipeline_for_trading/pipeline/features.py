"""Feature engineering (AFML Ch. 5 + Feynman's empirical notes).

Key design choices:
- Savitzky-Golay filter is applied *causally* with edge-padding by the last
  valid value to avoid look-ahead bias (the filter's coefficients centered on
  the current sample would otherwise peek into the future).
- Fractional differentiation uses a fixed-width window (AFML 5.4.2). Weights
  with |w| < tau are truncated so every observation sees the same kernel.
- Only the features validated by Feynman's MDA (see feature notes) are
  computed by default.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.signal import savgol_coeffs


# --------------------------------------------------------------------------
# Savitzky-Golay (causal)
# --------------------------------------------------------------------------

def savgol_causal(series: pd.Series, window: int, polyorder: int, deriv: int = 0) -> pd.Series:
    """Causal Savitzky-Golay filter.

    Implementation: use SavGol coefficients evaluated at pos=window-1 (the
    rightmost point of the window). The convolution is then strictly
    backward-looking. The first (window-1) observations are back-filled with
    the last non-NaN value to keep the series aligned — these are *not*
    future leakage, just missing-data handling for early samples.
    """
    if window % 2 == 0:
        window += 1
    coeffs = savgol_coeffs(window, polyorder, deriv=deriv, pos=window - 1, use="conv")
    arr = series.to_numpy(dtype=float)
    out = np.full_like(arr, np.nan)
    for i in range(window - 1, len(arr)):
        out[i] = np.dot(coeffs, arr[i - window + 1: i + 1])
    return pd.Series(out, index=series.index, name=f"savgol_{window}_{polyorder}_d{deriv}")


# --------------------------------------------------------------------------
# Fractional differentiation, fixed-width window (AFML 5.4.2)
# --------------------------------------------------------------------------

def _ffd_weights(d: float, size: int) -> np.ndarray:
    w = [1.0]
    for k in range(1, size):
        w.append(-w[-1] * (d - k + 1) / k)
    return np.array(w[::-1])


def fixed_width_frac_diff(series: pd.Series, d: float = 0.4, threshold: float = 1e-4) -> pd.Series:
    """Fractionally differentiated series with fixed-width window.

    Weights are computed until |w_k| < threshold, then reused for every
    point — preserving memory while making the series stationary.
    """
    # Determine width
    w, k = [1.0], 1
    while True:
        w_k = -w[-1] * (d - k + 1) / k
        if abs(w_k) < threshold:
            break
        w.append(w_k)
        k += 1
    weights = np.array(w[::-1])
    width = len(weights)

    arr = series.to_numpy(dtype=float)
    out = np.full_like(arr, np.nan)
    for i in range(width - 1, len(arr)):
        window = arr[i - width + 1: i + 1]
        if np.isnan(window).any():
            continue
        out[i] = float(np.dot(weights, window))
    return pd.Series(out, index=series.index, name=f"ffd_d{d}")


# --------------------------------------------------------------------------
# Statistical features
# --------------------------------------------------------------------------

def rolling_tstat(returns: pd.Series, window: int) -> pd.Series:
    """t-statistic of the mean return over a rolling window.

    tstat = mean(r) / (std(r) / sqrt(N)) — a volatility-normalised momentum.
    """
    mu = returns.rolling(window).mean()
    sd = returns.rolling(window).std()
    return (mu / (sd / np.sqrt(window))).rename(f"tstat_{window}")


def rolling_vol_on_savgol(close: pd.Series, savgol_w: int = 21, vol_w: int = 20) -> pd.Series:
    smooth = savgol_causal(close, savgol_w, polyorder=3)
    r = smooth.pct_change()
    return r.rolling(vol_w).std().rename(f"volatility_{vol_w}")


def zscore(series: pd.Series, window: int) -> pd.Series:
    mu = series.rolling(window).mean()
    sd = series.rolling(window).std()
    return ((series - mu) / sd).rename(f"{series.name}_zscore_{window}")


# --------------------------------------------------------------------------
# Exogenous joins (macro / sentiment)
# --------------------------------------------------------------------------

def asof_join_daily(bars_index: pd.DatetimeIndex, daily_series: pd.Series, column: str) -> pd.Series:
    """Forward-fill a daily series onto an irregular bar index, as-of the bar.

    Uses `merge_asof` so each bar sees only the most recent daily value at
    bar time — no look-ahead.
    """
    left = pd.DataFrame({"ts": bars_index}).sort_values("ts")
    right = daily_series.sort_index().rename(column).to_frame().reset_index()
    right.columns = ["ts", column]
    merged = pd.merge_asof(left, right, on="ts", direction="backward")
    return merged.set_index("ts")[column].reindex(bars_index)


# --------------------------------------------------------------------------
# Pipeline stage: assemble the validated feature set
# --------------------------------------------------------------------------

@dataclass
class FeatureConfig:
    tstat_windows: List[int] = field(default_factory=lambda: [10, 20, 50])
    sg_velocity_window: int = 51
    sg_acceleration_window: int = 5
    vol_savgol_w: int = 21
    vol_window: int = 20
    ffd_d: float = 0.4
    fear_greed_z_window: int = 5
    dxy_spread_window: int = 30


class FeatureBuilder:
    """Build Feynman's validated 10 features on dollar bars."""

    def __init__(self, cfg: FeatureConfig | None = None):
        self.cfg = cfg or FeatureConfig()

    def build(
        self,
        bars: pd.DataFrame,
        exog: Dict[str, pd.Series] | None = None,
    ) -> pd.DataFrame:
        exog = exog or {}
        close = bars["close"].astype(float)
        r = close.pct_change()

        feats: Dict[str, pd.Series] = {}

        # --- Savitzky-Golay kinematic state ---
        sg_vel = savgol_causal(close, self.cfg.sg_velocity_window, polyorder=3, deriv=1)
        sg_vel_norm = (sg_vel / close).rolling(50).apply(
            lambda x: x.iloc[-1] / x.std() if x.std() > 0 else 0.0, raw=False
        )
        feats[f"sg_velocity_{self.cfg.sg_velocity_window}"] = sg_vel_norm

        sg_acc = savgol_causal(close, self.cfg.sg_acceleration_window, polyorder=3, deriv=2)
        feats[f"sg_acceleration_{self.cfg.sg_acceleration_window}"] = (sg_acc / close)

        # --- tstat momentum (the only genuine signal per Feynman) ---
        for w in self.cfg.tstat_windows:
            feats[f"tstat_{w}"] = rolling_tstat(r, w)

        # --- volatility filter on SavGol returns ---
        feats[f"volatility_{self.cfg.vol_window}"] = rolling_vol_on_savgol(
            close, self.cfg.vol_savgol_w, self.cfg.vol_window
        )

        # --- stationary memory-preserving price (FFD) ---
        feats["ffd_close"] = fixed_width_frac_diff(close, d=self.cfg.ffd_d)

        # --- Exogenous context ---
        if "vix" in exog:
            # compute daily pct_change first, then as-of join to bars
            vix_daily_chg = exog["vix"].pct_change()
            feats["vix_chg"] = asof_join_daily(bars.index, vix_daily_chg, "vix_chg")
        if "dxy" in exog:
            # BTC daily return sampled at bar times, vs DXY daily return,
            # then rolling z-score of the difference
            btc_daily = close.resample("1D").last().pct_change()
            dxy_daily = exog["dxy"].pct_change()
            diff_daily = (btc_daily - dxy_daily.reindex(btc_daily.index, method="ffill")).dropna()
            spread_z_daily = zscore(
                diff_daily.rename("btc_macro_diff"), self.cfg.dxy_spread_window
            ).rename("btc_dxy_spread")
            feats["btc_dxy_spread"] = asof_join_daily(
                bars.index, spread_z_daily, "btc_dxy_spread"
            )
        if "fear_greed" in exog:
            fg_z_daily = zscore(exog["fear_greed"], self.cfg.fear_greed_z_window)
            feats["fear_greed_zscore_5"] = asof_join_daily(
                bars.index, fg_z_daily, "fear_greed_zscore_5"
            )

        X = pd.concat(feats.values(), axis=1)
        X.columns = list(feats.keys())
        return X
