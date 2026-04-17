"""Shared helpers: paths, logging to .txt, multiprocessing, plotting style."""
from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Callable, Iterable, List, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    data: Path
    new_data: Path
    plots: Path
    resultados: Path
    model: Path

    @classmethod
    def discover(cls, start: Path | None = None) -> "ProjectPaths":
        root = Path(start) if start else Path(__file__).resolve().parent.parent
        paths = cls(
            root=root,
            data=root / "data",
            new_data=root / "new_data",
            plots=root / "plots",
            resultados=root / "resultados",
            model=root / "model",
        )
        paths.plots.mkdir(exist_ok=True)
        paths.resultados.mkdir(exist_ok=True)
        paths.model.mkdir(exist_ok=True)
        return paths


# --------------------------------------------------------------------------
# Text logging per-stage (one .txt per artifact)
# --------------------------------------------------------------------------

class TxtLogger:
    """Writes stage reports to resultados/<name>.txt and mirrors to stdout."""

    def __init__(self, folder: Path, name: str):
        self.path = folder / f"{name}.txt"
        self.path.write_text("", encoding="utf-8")
        self._stdout = logging.getLogger(name)
        if not self._stdout.handlers:
            h = logging.StreamHandler(sys.stdout)
            h.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
            self._stdout.addHandler(h)
            self._stdout.setLevel(logging.INFO)

    def write(self, text: str = "") -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(text + "\n")
        self._stdout.info(text)

    def header(self, title: str) -> None:
        bar = "=" * max(len(title), 60)
        self.write(bar)
        self.write(title)
        self.write(bar)

    def table(self, df: pd.DataFrame, float_fmt: str = "%.6f") -> None:
        self.write(df.to_string(float_format=float_fmt))


# --------------------------------------------------------------------------
# Multiprocessing (López de Prado Ch. 20 — mpPandasObj-style)
# --------------------------------------------------------------------------

def _lin_parts(num_atoms: int, num_threads: int) -> np.ndarray:
    parts = np.linspace(0, num_atoms, min(num_threads, num_atoms) + 1)
    return np.ceil(parts).astype(int)


def mp_apply(
    func: Callable,
    molecules: Sequence,
    num_threads: int | None = None,
    **kwargs,
) -> List:
    """Apply `func(molecule=slice, **kwargs)` over chunks of the index.

    Keeps things simple and safe on Windows: falls back to serial if
    num_threads <= 1 (useful while debugging).
    """
    n_threads = num_threads or max(1, cpu_count() - 1)
    if n_threads <= 1 or len(molecules) <= 1:
        return [func(molecule=list(molecules), **kwargs)]

    parts = _lin_parts(len(molecules), n_threads)
    jobs = []
    for i in range(1, len(parts)):
        jobs.append(
            dict(molecule=list(molecules[parts[i - 1]: parts[i]]), **kwargs)
        )
    with Pool(processes=n_threads) as pool:
        return pool.map(_mp_call_wrapper, [(func, j) for j in jobs])


def _mp_call_wrapper(args):  # top-level so it can be pickled on Windows
    func, kwargs = args
    return func(**kwargs)


# --------------------------------------------------------------------------
# Plotting defaults
# --------------------------------------------------------------------------

def set_plot_style() -> None:
    plt.rcParams.update({
        "figure.figsize": (10, 5),
        "figure.dpi": 110,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
    })


def save_fig(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
