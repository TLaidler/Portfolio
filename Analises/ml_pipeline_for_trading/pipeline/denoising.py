"""Denoising and detoning of empirical correlation matrices (AFML Ch. 2, MLAM).

Empirical covariance matrices of financial features are nearly singular
(Marcos Lopez de Prado, "Machine Learning for Asset Managers", 2020). The
Marcenko-Pastur distribution tells us which eigenvalues are indistinguishable
from noise under the null of no signal. We shrink those eigenvalues to their
mean and keep the ones above the theoretical edge.

Detoning removes the first (market/common-factor) eigenvector, which is
usually dominant and destabilizes portfolio allocation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar


def _mp_pdf(var: float, q: float, pts: int = 1000) -> pd.Series:
    """Marcenko-Pastur density for ratio q = T / N and variance var."""
    lam_plus = var * (1 + (1.0 / q) ** 0.5) ** 2
    lam_minus = var * (1 - (1.0 / q) ** 0.5) ** 2
    lam = np.linspace(lam_minus, lam_plus, pts)
    pdf = q / (2 * np.pi * var * lam) * ((lam_plus - lam) * (lam - lam_minus)) ** 0.5
    return pd.Series(pdf, index=lam)


def _eigen_decomp(corr: np.ndarray):
    w, v = np.linalg.eigh(corr)
    idx = np.argsort(w)[::-1]
    return w[idx], v[:, idx]


def _fit_mp_variance(eigvals: np.ndarray, q: float) -> tuple[float, float]:
    """Find the variance for the MP null that best fits the eigenvalue pdf."""
    from scipy.stats import gaussian_kde

    kde = gaussian_kde(eigvals, bw_method=0.25)

    def obj(var: float) -> float:
        if var <= 0:
            return np.inf
        mp = _mp_pdf(var, q)
        emp = kde.evaluate(mp.index.values)
        return float(np.sum((mp.values - emp) ** 2))

    res = minimize_scalar(obj, bounds=(1e-4, 1.0), method="bounded")
    var = float(res.x)
    lam_plus = var * (1 + (1.0 / q) ** 0.5) ** 2
    return var, lam_plus


def denoise_corr(corr: pd.DataFrame, q: float) -> pd.DataFrame:
    """Replace eigenvalues below MP edge by their average (constant-residual)."""
    C = corr.to_numpy()
    w, v = _eigen_decomp(C)
    _, lam_plus = _fit_mp_variance(w, q)
    n_facts = int((w > lam_plus).sum())
    if n_facts == 0:
        return corr.copy()
    w_denoised = w.copy()
    if n_facts < len(w):
        w_denoised[n_facts:] = w[n_facts:].mean()
    C_d = v @ np.diag(w_denoised) @ v.T
    # Rescale to unit diagonal
    d = np.sqrt(np.diag(C_d))
    C_d = C_d / np.outer(d, d)
    return pd.DataFrame(C_d, index=corr.index, columns=corr.columns)


def detone(corr: pd.DataFrame, n_market_factors: int = 1) -> pd.DataFrame:
    """Remove the top-k eigenvectors (the 'market' component)."""
    C = corr.to_numpy()
    w, v = _eigen_decomp(C)
    w_dt = w.copy()
    w_dt[:n_market_factors] = 0.0
    C_dt = v @ np.diag(w_dt) @ v.T
    d = np.sqrt(np.clip(np.diag(C_dt), 1e-12, None))
    C_dt = C_dt / np.outer(d, d)
    return pd.DataFrame(C_dt, index=corr.index, columns=corr.columns)


def corr_to_dist(corr: pd.DataFrame) -> pd.DataFrame:
    """Lopez de Prado's correlation distance: sqrt(0.5*(1-corr))."""
    return ((0.5 * (1.0 - corr)).clip(lower=0.0)) ** 0.5
