"""Curva monotônica percentil = f(rating) e sua inversa.

Construção em dois passos:

1. **Regressão isotônica ponderada** (garante monotonicidade e respeita a
   confiança de cada observação).
2. **PCHIP** sobre os nós isotônicos (suaviza preservando a monotonicidade —
   propriedade do interpolador de Fritsch–Carlson).

A inversa ``rating(percentile)`` interpola a mesma curva no sentido oposto.
Fora da faixa observada os valores são CLIPADOS (nunca extrapolados) — os
consumidores devem checar ``x_min``/``x_max``/``y_min``/``y_max``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import PchipInterpolator
from sklearn.isotonic import IsotonicRegression

_GRID_STEP = 5.0  # resolução interna da curva (pontos de rating)


@dataclass
class PercentileCurve:
    """Curva monotônica não-decrescente rating → percentil (0–100)."""

    x_grid: np.ndarray  # ratings (crescente)
    y_grid: np.ndarray  # percentis (não-decrescente)

    @property
    def x_min(self) -> float:
        return float(self.x_grid[0])

    @property
    def x_max(self) -> float:
        return float(self.x_grid[-1])

    @property
    def y_min(self) -> float:
        return float(self.y_grid[0])

    @property
    def y_max(self) -> float:
        return float(self.y_grid[-1])

    @classmethod
    def fit(
        cls,
        ratings: np.ndarray,
        percentiles: np.ndarray,
        weights: np.ndarray | None = None,
    ) -> "PercentileCurve":
        """Ajusta a curva a observações (possivelmente ruidosas e duplicadas)."""
        x = np.asarray(ratings, float)
        y = np.asarray(percentiles, float)
        if x.size < 2 or np.unique(x).size < 2:
            raise ValueError("observações insuficientes para ajustar a curva")
        w = np.ones_like(x) if weights is None else np.asarray(weights, float)

        iso = IsotonicRegression(y_min=0.0, y_max=100.0, increasing=True,
                                 out_of_bounds="clip")
        y_iso = iso.fit_transform(x, y, sample_weight=w)

        # nós: média isotônica por rating único (já não-decrescente)
        order = np.argsort(x, kind="stable")
        xs, ys = x[order], y_iso[order]
        knots_x, idx = np.unique(xs, return_index=True)
        knots_y = np.array([ys[i] for i in idx])
        knots_y = np.maximum.accumulate(knots_y)

        if knots_x.size >= 3:
            pchip = PchipInterpolator(knots_x, knots_y, extrapolate=False)
            grid_x = np.arange(knots_x[0], knots_x[-1] + _GRID_STEP, _GRID_STEP)
            grid_y = pchip(grid_x)
            grid_y = np.nan_to_num(grid_y, nan=knots_y[-1])
            grid_y = np.clip(np.maximum.accumulate(grid_y), 0.0, 100.0)
        else:  # 2 nós: reta
            grid_x = np.array([knots_x[0], knots_x[-1]])
            grid_y = np.array([knots_y[0], knots_y[-1]])

        return cls(x_grid=grid_x, y_grid=grid_y)

    def percentile(self, rating: np.ndarray) -> np.ndarray:
        """Percentil estimado para cada rating (clipado à faixa observada)."""
        r = np.clip(np.asarray(rating, float), self.x_min, self.x_max)
        return np.interp(r, self.x_grid, self.y_grid)

    def rating(self, percentile: float) -> float:
        """Rating estimado para um percentil (inversa; clipado à faixa)."""
        p = float(np.clip(percentile, self.y_min, self.y_max))
        # torna y estritamente crescente para inversão estável em platôs
        eps = np.arange(self.y_grid.size) * 1e-9
        return float(np.interp(p, self.y_grid + eps, self.x_grid))
