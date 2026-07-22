"""Testes da limpeza, detecção de anomalias e ajuste de curvas."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.interpolation import PercentileCurve
from src.statistics import (
    clean_observations,
    fit_cells,
    flag_anomalies,
    observations_to_frame,
)
from src.utils import Observation


def _obs(rating, pct, d=date(2022, 6, 1), gt="rapid", conf=1.0, note=""):
    return Observation(
        date=d, source="test", game_type=gt, rating=rating,
        percentile=pct, url=f"http://x/{rating}", confidence=conf, note=note,
    )


def _synthetic_cell(n=60, seed=1):
    """Observações sintéticas de uma CDF logística com ruído."""
    rng = np.random.default_rng(seed)
    ratings = rng.uniform(300, 2400, n)
    true_pct = 100 / (1 + np.exp(-(ratings - 900) / 300))
    noisy = np.clip(true_pct + rng.normal(0, 2, n), 0.1, 99.9)
    return [_obs(r, p) for r, p in zip(ratings, noisy)]


def test_clean_removes_invalid_and_provisional():
    obs = [
        _obs(1000, 50),
        _obs(1000, 0),                       # percentil inválido
        _obs(50, 10),                        # rating fora da faixa
        _obs(1000, 60, d=date(1970, 1, 1)),  # sem data
        _obs(1000, 99.9, note="rated_count=2"),  # provisório
        _obs(1200, 70, note="rated_count=500"),
    ]
    df, stats = clean_observations(observations_to_frame(obs))
    assert set(zip(df.rating, df.percentile)) == {(1000.0, 50.0), (1200.0, 70.0)}
    assert stats["input"] == 6


def test_flag_anomalies_drops_gross_outlier():
    obs = _synthetic_cell()
    obs.append(_obs(1539, 5.9))  # o caso real 00beni: 1539 -> 5.9
    df, _ = clean_observations(observations_to_frame(obs))
    kept, dropped = flag_anomalies(df)
    assert len(dropped) == 1
    assert dropped.iloc[0].rating == 1539


def test_curve_is_monotonic_and_invertible():
    obs = _synthetic_cell()
    df, _ = clean_observations(observations_to_frame(obs))
    fits = fit_cells(df, n_boot=0)
    assert len(fits) == 1
    curve = fits[0].curve
    grid = np.linspace(curve.x_min, curve.x_max, 200)
    vals = curve.percentile(grid)
    assert np.all(np.diff(vals) >= -1e-9), "curva deve ser não-decrescente"
    # inversa consistente: rating(percentile(r)) ~ r nas regiões não-planas
    r = 1200.0
    p = float(curve.percentile(np.array([r]))[0])
    assert abs(curve.rating(p) - r) < 60


def test_curve_does_not_extrapolate():
    curve = PercentileCurve.fit(
        np.array([800, 1000, 1200, 1400.0]),
        np.array([30, 50, 70, 85.0]),
    )
    assert curve.percentile(np.array([200.0]))[0] == pytest.approx(30)   # clip
    assert curve.percentile(np.array([3000.0]))[0] == pytest.approx(85)  # clip
    assert curve.rating(99.9) == pytest.approx(1400)                     # clip


def test_fit_cells_respects_min_obs():
    obs = [_obs(800, 30), _obs(1000, 50), _obs(1200, 70)]  # só 3 < MIN_OBS_FIT
    df, _ = clean_observations(observations_to_frame(obs))
    assert fit_cells(df, n_boot=0) == []


def test_bootstrap_bands_cover_estimate():
    obs = _synthetic_cell(n=80)
    df, _ = clean_observations(observations_to_frame(obs))
    fits = fit_cells(df, n_boot=100)
    f = fits[0]
    r = np.array([1000.0])
    est = float(f.curve.percentile(r)[0])
    boot = [float(b.percentile(r)[0]) for b in f.boot_curves]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    assert lo <= est <= hi
