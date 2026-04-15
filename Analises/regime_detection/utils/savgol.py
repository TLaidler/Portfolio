"""
Canonical Savitzky-Golay causal filter implementation.

This is the SINGLE SOURCE OF TRUTH for savgol_causal across the entire project.
All scripts must import from here. Do NOT redefine locally.

Key properties:
  - Causal: pos=window-1, evaluates polynomial at the LAST point of the window
  - No look-ahead: only past data is used
  - Edge-padded: replicates last value to avoid zero-padding artifacts from np.convolve
  - First (window-1) bars are NaN (warmup period)

Functions:
  - savgol_causal: smoothed price (deriv=0)
  - savgol_causal_deriv: analytical derivative of the local polynomial (deriv=1,2,...)
"""

import numpy as np
from scipy.signal import savgol_coeffs


def savgol_causal(values: np.ndarray, window: int, polyorder: int) -> np.ndarray:
    """
    Savitzky-Golay CAUSAL filter (pos=window-1). No look-ahead.

    Uses edge-padding at the end to eliminate zero-padding artifacts
    in the last w-1 bars (bug fixed 2026-03-25).

    Parameters
    ----------
    values : np.ndarray
        Input price or signal array.
    window : int
        Filter window size (must be odd; adjusted if even).
    polyorder : int
        Polynomial order for local fit.

    Returns
    -------
    np.ndarray
        Filtered array, same length as input.
        First (window-1) values are NaN (warmup).
    """
    w = min(window, len(values))
    if w % 2 == 0:
        w -= 1
    if w < polyorder + 2:
        return values.copy()
    coeffs = savgol_coeffs(w, polyorder, pos=w - 1)
    padded = np.concatenate([values, np.full(w - 1, values[-1])])
    smoothed = np.convolve(padded, coeffs, mode="full")
    smoothed = smoothed[w - 1: w - 1 + len(values)]
    smoothed[: w - 1] = np.nan
    return smoothed


def savgol_causal_deriv(values: np.ndarray, window: int, polyorder: int,
                        deriv: int = 1) -> np.ndarray:
    """
    Analytical derivative of the SavGol causal polynomial.

    Uses savgol_coeffs(deriv=N) to compute the Nth derivative of the
    local polynomial fit, evaluated at the last point of the window.
    This gives velocity (deriv=1) and acceleration (deriv=2) without
    finite-difference approximation.

    Parameters
    ----------
    values : np.ndarray
        Input price or signal array.
    window : int
        Filter window size (must be odd; adjusted if even).
    polyorder : int
        Polynomial order for local fit. Must be >= deriv.
    deriv : int
        Derivative order (1=velocity, 2=acceleration).

    Returns
    -------
    np.ndarray
        Derivative array, same length as input.
        First (window-1) values are NaN (warmup).
    """
    w = min(window, len(values))
    if w % 2 == 0:
        w -= 1
    if w < polyorder + 2 or polyorder < deriv:
        return np.full_like(values, np.nan, dtype=np.float64)
    coeffs = savgol_coeffs(w, polyorder, pos=w - 1, deriv=deriv)
    padded = np.concatenate([values, np.full(w - 1, values[-1])])
    result = np.convolve(padded, coeffs, mode="full")
    result = result[w - 1: w - 1 + len(values)]
    result[: w - 1] = np.nan
    return result
