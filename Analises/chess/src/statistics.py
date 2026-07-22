"""Limpeza, deduplicação, detecção de conflitos e ajuste das curvas anuais.

Metodologia:

1. Filtros de validade (faixas, datas, contagem mínima de partidas quando
   conhecida).
2. Deduplicação por (fonte, URL, data, modalidade, rating).
3. Detecção de anomalias: um ajuste isotônico preliminar por célula
   (plataforma × modalidade × ano) identifica observações cujo resíduo excede
   ``ANOMALY_RESIDUAL_PP`` pontos percentuais — são descartadas e registradas
   (ex.: bugs do próprio site nos snapshots).
4. Curva final: regressão isotônica ponderada pela confiança + suavização
   PCHIP (ver :mod:`interpolation`), com intervalos de confiança por bootstrap.
"""
from __future__ import annotations

import dataclasses
from datetime import date
from typing import Iterable, Optional

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from .interpolation import PercentileCurve
from .utils import OBSERVATION_COLUMNS, Observation, get_logger

log = get_logger(__name__)

ANOMALY_RESIDUAL_PP = 25.0   # resíduo máximo (pontos percentuais) antes de descartar
MIN_RATED_GAMES = 10         # partidas mínimas p/ confiar no percentil (quando conhecido)
MIN_OBS_FIT = 5              # mínimo absoluto para ajustar uma curva
MIN_OBS_OK = 15              # abaixo disso a célula é marcada "low_confidence"
TARGET_TOP_SHARES = (50.0, 25.0, 10.0, 5.0, 1.0, 0.5, 0.1)  # "Top X%"
FIXED_RATINGS = (800, 1000, 1200, 1500, 1800, 2000)


# ---------------------------------------------------------------------------
# DataFrame <-> Observation
# ---------------------------------------------------------------------------
def observations_to_frame(observations: Iterable[Observation]) -> pd.DataFrame:
    rows = [dataclasses.asdict(o) for o in observations]
    df = pd.DataFrame(rows, columns=OBSERVATION_COLUMNS)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def load_observations(path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df["note"] = df["note"].fillna("")
    return df


# ---------------------------------------------------------------------------
# Limpeza
# ---------------------------------------------------------------------------
def _rated_count_from_note(note: str) -> Optional[int]:
    for part in str(note).split(";"):
        if part.startswith("rated_count="):
            try:
                return int(part.split("=", 1)[1])
            except ValueError:
                return None
    return None


def clean_observations(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Aplica filtros de validade e dedup. Retorna (limpo, estatísticas)."""
    stats: dict[str, int] = {"input": len(df)}
    df = df.copy()

    df = df[(df["percentile"] > 0) & (df["percentile"] < 100)]
    df = df[(df["rating"] >= 100) & (df["rating"] <= 3600)]
    stats["after_range_filter"] = len(df)

    # datas desconhecidas (sentinela 1970) não podem ancorar um ano
    df = df[df["date"] >= pd.Timestamp("2007-01-01")]
    stats["after_date_filter"] = len(df)

    # poucas partidas => percentil de rating provisório (ex.: 2 jogos, 99.9%)
    rated = df["note"].map(_rated_count_from_note)
    df = df[(rated.isna()) | (rated >= MIN_RATED_GAMES)]
    stats["after_rated_count_filter"] = len(df)

    df = df.drop_duplicates(subset=["source", "url", "date", "game_type", "rating", "percentile"])
    stats["after_dedup"] = len(df)

    df["year"] = df["date"].dt.year
    return df.reset_index(drop=True), stats


def flag_anomalies(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove observações que violam grosseiramente a monotonicidade da célula.

    Ajusta isotônica preliminar por (platform, game_type, year) e descarta
    pontos com |resíduo| > ``ANOMALY_RESIDUAL_PP``. Retorna (mantidas, descartadas).
    """
    keep_parts: list[pd.DataFrame] = []
    drop_parts: list[pd.DataFrame] = []
    for (platform, gt, year), g in df.groupby(["platform", "game_type", "year"]):
        if len(g) < MIN_OBS_FIT:
            keep_parts.append(g)
            continue
        iso = IsotonicRegression(y_min=0, y_max=100, increasing=True, out_of_bounds="clip")
        fitted = iso.fit_transform(g["rating"], g["percentile"], sample_weight=g["confidence"])
        resid = (g["percentile"] - fitted).abs()
        bad = resid > ANOMALY_RESIDUAL_PP
        if bad.any():
            log.info(
                "%s/%s/%s: %d anomalia(s) descartada(s) (resíduo > %.0fpp)",
                platform, gt, year, int(bad.sum()), ANOMALY_RESIDUAL_PP,
            )
        keep_parts.append(g[~bad])
        drop_parts.append(g[bad])
    kept = pd.concat(keep_parts, ignore_index=True) if keep_parts else df.iloc[0:0]
    dropped = pd.concat(drop_parts, ignore_index=True) if drop_parts else df.iloc[0:0]
    return kept, dropped


# ---------------------------------------------------------------------------
# Ajuste por célula + bootstrap
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class CellFit:
    platform: str
    game_type: str
    year: int
    curve: PercentileCurve
    n_obs: int
    low_confidence: bool
    boot_curves: list[PercentileCurve] = dataclasses.field(default_factory=list)


def fit_cells(
    df: pd.DataFrame,
    n_boot: int = 300,
    seed: int = 42,
    min_obs: int = MIN_OBS_FIT,
) -> list[CellFit]:
    """Ajusta uma curva percentil=f(rating) por (plataforma, modalidade, ano)."""
    rng = np.random.default_rng(seed)
    fits: list[CellFit] = []
    for (platform, gt, year), g in sorted(df.groupby(["platform", "game_type", "year"])):
        if len(g) < min_obs:
            log.info("%s/%s/%s: %d obs — insuficiente, pulando", platform, gt, year, len(g))
            continue
        x = g["rating"].to_numpy(float)
        y = g["percentile"].to_numpy(float)
        w = g["confidence"].to_numpy(float)
        curve = PercentileCurve.fit(x, y, w)

        boot: list[PercentileCurve] = []
        if n_boot > 0:
            n = len(g)
            for _ in range(n_boot):
                idx = rng.integers(0, n, n)
                try:
                    boot.append(PercentileCurve.fit(x[idx], y[idx], w[idx]))
                except ValueError:
                    continue
        fits.append(
            CellFit(
                platform=platform,
                game_type=gt,
                year=int(year),
                curve=curve,
                n_obs=len(g),
                low_confidence=len(g) < MIN_OBS_OK,
                boot_curves=boot,
            )
        )
        log.info("%s/%s/%s: curva com %d obs (faixa %d–%d)",
                 platform, gt, year, len(g), int(curve.x_min), int(curve.x_max))
    return fits


def _boot_band(values: np.ndarray, alpha: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    lo = np.nanpercentile(values, 100 * alpha / 2, axis=0)
    hi = np.nanpercentile(values, 100 * (1 - alpha / 2), axis=0)
    return lo, hi


def curves_long_frame(fits: list[CellFit], step: int = 25) -> pd.DataFrame:
    """Formato longo das curvas com bandas bootstrap, para viz/relatório."""
    rows: list[dict] = []
    for f in fits:
        grid = np.arange(
            int(np.ceil(f.curve.x_min / step)) * step,
            int(np.floor(f.curve.x_max / step)) * step + 1,
            step,
            dtype=float,
        )
        if grid.size == 0:
            continue
        mean = f.curve.percentile(grid)
        if f.boot_curves:
            ens = np.vstack([
                np.where((grid >= b.x_min) & (grid <= b.x_max), b.percentile(grid), np.nan)
                for b in f.boot_curves
            ])
            lo, hi = _boot_band(ens)
        else:
            lo = hi = np.full_like(mean, np.nan)
        for r, p, l, h in zip(grid, mean, lo, hi):
            rows.append(
                dict(
                    platform=f.platform, game_type=f.game_type, year=f.year,
                    rating=r, percentile=p, pctl_lo=l, pctl_hi=h,
                    n_obs=f.n_obs, low_confidence=f.low_confidence,
                )
            )
    return pd.DataFrame(rows)


def percentile_targets_frame(fits: list[CellFit]) -> pd.DataFrame:
    """Rating estimado para cada alvo "Top X%" (com IC bootstrap)."""
    rows: list[dict] = []
    for f in fits:
        for top in TARGET_TOP_SHARES:
            pctl = 100.0 - top
            if not (f.curve.y_min <= pctl <= f.curve.y_max):
                continue  # alvo fora da faixa observada — não extrapolar
            est = f.curve.rating(pctl)
            if f.boot_curves:
                samples = np.array([
                    b.rating(pctl) for b in f.boot_curves
                    if b.y_min <= pctl <= b.y_max
                ])
                lo, hi = (np.percentile(samples, [2.5, 97.5]) if samples.size >= 30
                          else (np.nan, np.nan))
            else:
                lo = hi = np.nan
            rows.append(
                dict(
                    platform=f.platform, game_type=f.game_type, year=f.year,
                    top_share=top, percentile=pctl,
                    rating_est=est, rating_lo=lo, rating_hi=hi,
                    n_obs=f.n_obs, low_confidence=f.low_confidence,
                )
            )
    return pd.DataFrame(rows)


def fixed_ratings_frame(fits: list[CellFit]) -> pd.DataFrame:
    """Percentil estimado de ratings fixos (800, 1000, ...) por ano."""
    rows: list[dict] = []
    for f in fits:
        for rating in FIXED_RATINGS:
            if not (f.curve.x_min <= rating <= f.curve.x_max):
                continue
            est = float(f.curve.percentile(np.array([rating], float))[0])
            if f.boot_curves:
                samples = np.array([
                    float(b.percentile(np.array([rating], float))[0])
                    for b in f.boot_curves
                    if b.x_min <= rating <= b.x_max
                ])
                lo, hi = (np.percentile(samples, [2.5, 97.5]) if samples.size >= 30
                          else (np.nan, np.nan))
            else:
                lo = hi = np.nan
            rows.append(
                dict(
                    platform=f.platform, game_type=f.game_type, year=f.year,
                    rating=rating, percentile_est=est,
                    pctl_lo=lo, pctl_hi=hi,
                    n_obs=f.n_obs, low_confidence=f.low_confidence,
                )
            )
    return pd.DataFrame(rows)
