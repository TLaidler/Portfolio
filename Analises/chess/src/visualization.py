"""Gráficos estáticos (matplotlib) e interativos (plotly).

Sistema visual: paleta de referência do método dataviz —
anos são uma dimensão ORDENADA e usam a rampa sequencial azul (claro→escuro);
comparações entre plataformas usam os slots categóricos fixos (azul, aqua).
Marcas finas (linhas 2px), grid recessivo, rótulos em tinta neutra.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .utils import FIGURES_DIR, get_logger

log = get_logger(__name__)

# --- paleta (reference palette, modo claro) --------------------------------
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

CAT = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948"]
# rampa sequencial azul, do step 250 ao 700 (ordinal: nunca mais claro que 250)
SEQ_BLUE = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
            "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]

GAME_TYPE_LABEL = {"rapid": "Rapid", "blitz": "Blitz", "bullet": "Bullet",
                   "daily": "Daily", "classical": "Classical"}


def _ordered_colors(n: int) -> list[str]:
    """n cores da rampa sequencial, espaçadas do claro ao escuro."""
    if n <= 1:
        return [SEQ_BLUE[-3]]
    idx = np.linspace(0, len(SEQ_BLUE) - 1, n).round().astype(int)
    return [SEQ_BLUE[i] for i in idx]


def _style_axes(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(BASELINE)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(INK_2)
    ax.yaxis.label.set_color(INK_2)
    ax.title.set_color(INK)


def _new_fig(figsize=(9, 5.5)) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    fig.patch.set_facecolor(PAGE)
    _style_axes(ax)
    return fig, ax


def _save(fig: plt.Figure, name: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / name
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    log.info("figura: %s", path.name)
    return path


# ---------------------------------------------------------------------------
# 1. Curvas rating → percentil, uma por ano
# ---------------------------------------------------------------------------
def plot_year_curves(
    curves: pd.DataFrame, game_type: str, platform: str = "chesscom"
) -> Optional[Path]:
    df = curves[(curves.game_type == game_type) & (curves.platform == platform)]
    years = sorted(df.year.unique())
    if not years:
        return None
    colors = dict(zip(years, _ordered_colors(len(years))))

    fig, ax = _new_fig()
    for year in years:
        g = df[df.year == year].sort_values("rating")
        suffix = " *" if g.low_confidence.iloc[0] else ""
        ax.plot(g.rating, g.percentile, color=colors[year], linewidth=2,
                label=f"{year}{suffix}", solid_capstyle="round")
        # rótulo direto no fim da linha (identidade nunca só pela cor)
        ax.annotate(str(year), (g.rating.iloc[-1], g.percentile.iloc[-1]),
                    xytext=(6, 0), textcoords="offset points",
                    color=colors[year], fontsize=8, fontweight="bold",
                    va="center")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Percentil (% de jogadores abaixo)")
    ax.set_title(f"Chess.com {GAME_TYPE_LABEL.get(game_type, game_type)} — "
                 f"percentil por rating, ano a ano")
    ax.set_ylim(0, 100)
    leg = ax.legend(loc="lower right", fontsize=8, frameon=False,
                    title="Ano (* = poucos dados)")
    leg.get_title().set_color(INK_2)
    for t in leg.get_texts():
        t.set_color(INK_2)
    return _save(fig, f"curves_{platform}_{game_type}.png")


# ---------------------------------------------------------------------------
# 2. Rating necessário para cada "Top X%" ao longo dos anos
# ---------------------------------------------------------------------------
def plot_percentile_targets(
    targets: pd.DataFrame, game_type: str, platform: str = "chesscom"
) -> Optional[Path]:
    df = targets[(targets.game_type == game_type) & (targets.platform == platform)]
    shares = sorted(df.top_share.unique(), reverse=True)  # 50 → 0.1
    if not shares or df.year.nunique() < 2:
        return None
    colors = dict(zip(shares, _ordered_colors(len(shares))))

    fig, ax = _new_fig()
    for share in shares:
        g = df[df.top_share == share].sort_values("year")
        ax.plot(g.year, g.rating_est, color=colors[share], linewidth=2,
                marker="o", markersize=4, label=f"Top {share:g}%")
        if g.rating_lo.notna().any():
            ax.fill_between(g.year, g.rating_lo, g.rating_hi,
                            color=colors[share], alpha=0.15, linewidth=0)
        ax.annotate(f"Top {share:g}%", (g.year.iloc[-1], g.rating_est.iloc[-1]),
                    xytext=(8, 0), textcoords="offset points",
                    color=colors[share], fontsize=8, fontweight="bold",
                    va="center")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Rating estimado")
    ax.set_title(f"Chess.com {GAME_TYPE_LABEL.get(game_type, game_type)} — "
                 f"rating necessário para cada Top X% (IC 95%)")
    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
    leg = ax.legend(loc="upper left", fontsize=8, frameon=False)
    for t in leg.get_texts():
        t.set_color(INK_2)
    return _save(fig, f"targets_{platform}_{game_type}.png")


# ---------------------------------------------------------------------------
# 3. Evolução do percentil de ratings fixos
# ---------------------------------------------------------------------------
def plot_fixed_ratings(
    fixed: pd.DataFrame, game_type: str, platform: str = "chesscom"
) -> Optional[Path]:
    df = fixed[(fixed.game_type == game_type) & (fixed.platform == platform)]
    ratings = sorted(df.rating.unique())
    if not ratings or df.year.nunique() < 2:
        return None
    colors = dict(zip(ratings, _ordered_colors(len(ratings))))

    fig, ax = _new_fig()
    for rating in ratings:
        g = df[df.rating == rating].sort_values("year")
        ax.plot(g.year, g.percentile_est, color=colors[rating], linewidth=2,
                marker="o", markersize=4, label=f"{rating}")
        if g.pctl_lo.notna().any():
            ax.fill_between(g.year, g.pctl_lo, g.pctl_hi,
                            color=colors[rating], alpha=0.15, linewidth=0)
        ax.annotate(str(rating), (g.year.iloc[-1], g.percentile_est.iloc[-1]),
                    xytext=(8, 0), textcoords="offset points",
                    color=colors[rating], fontsize=8, fontweight="bold",
                    va="center")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Percentil (% de jogadores abaixo)")
    ax.set_ylim(0, 100)
    ax.set_title(f"Chess.com {GAME_TYPE_LABEL.get(game_type, game_type)} — "
                 f"o que significa cada rating, ano a ano (IC 95%)")
    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
    leg = ax.legend(loc="lower right", fontsize=8, frameon=False, title="Rating")
    leg.get_title().set_color(INK_2)
    for t in leg.get_texts():
        t.set_color(INK_2)
    return _save(fig, f"fixed_ratings_{platform}_{game_type}.png")


# ---------------------------------------------------------------------------
# 4. Heatmap ano × rating → percentil
# ---------------------------------------------------------------------------
def plot_heatmap(
    curves: pd.DataFrame, game_type: str, platform: str = "chesscom",
    rating_step: int = 100,
) -> Optional[Path]:
    df = curves[(curves.game_type == game_type) & (curves.platform == platform)]
    if df.empty:
        return None
    df = df[df.rating % rating_step == 0]
    pivot = df.pivot_table(index="year", columns="rating", values="percentile")
    if pivot.empty:
        return None

    cmap = mpl.colors.LinearSegmentedColormap.from_list(
        "seq_blue", ["#cde2fb", "#0d366b"])
    fig, ax = _new_fig(figsize=(10, 0.6 * len(pivot) + 2))
    im = ax.pcolormesh(pivot.columns, np.arange(len(pivot)), pivot.values,
                       cmap=cmap, vmin=0, vmax=100, edgecolors=SURFACE,
                       linewidth=2)
    ax.set_yticks(np.arange(len(pivot)) + 0.0)
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Rating")
    ax.set_ylabel("Ano")
    ax.set_title(f"Chess.com {GAME_TYPE_LABEL.get(game_type, game_type)} — "
                 f"percentil (cor) por rating e ano")
    ax.grid(False)
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Percentil", color=INK_2)
    cbar.ax.tick_params(colors=MUTED)
    cbar.outline.set_visible(False)
    return _save(fig, f"heatmap_{platform}_{game_type}.png")


# ---------------------------------------------------------------------------
# 5. Chess.com × Lichess (mesmo ano, mesma modalidade)
# ---------------------------------------------------------------------------
def plot_platform_comparison(
    curves: pd.DataFrame, game_type: str = "rapid", year: Optional[int] = None
) -> Optional[Path]:
    df = curves[curves.game_type == game_type]
    common_years = (
        set(df[df.platform == "chesscom"].year) & set(df[df.platform == "lichess"].year)
    )
    if not common_years:
        return None
    year = year or max(common_years)

    fig, ax = _new_fig()
    for platform, color, label in (
        ("chesscom", CAT[0], "Chess.com"),
        ("lichess", CAT[1], "Lichess"),
    ):
        g = df[(df.platform == platform) & (df.year == year)].sort_values("rating")
        if g.empty:
            continue
        ax.plot(g.rating, g.percentile, color=color, linewidth=2, label=label)
        ax.annotate(label, (g.rating.iloc[-1], g.percentile.iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", color=color,
                    fontsize=9, fontweight="bold", va="center")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Percentil (% de jogadores abaixo)")
    ax.set_ylim(0, 100)
    ax.set_title(f"{GAME_TYPE_LABEL.get(game_type, game_type)} {year} — "
                 f"o mesmo rating vale percentis diferentes por plataforma")
    leg = ax.legend(loc="lower right", fontsize=9, frameon=False)
    for t in leg.get_texts():
        t.set_color(INK_2)
    return _save(fig, f"platforms_{game_type}_{year}.png")


# ---------------------------------------------------------------------------
# 6. Interativo (plotly): curvas por ano com tooltip
# ---------------------------------------------------------------------------
def plotly_year_curves(
    curves: pd.DataFrame, game_type: str, platform: str = "chesscom"
) -> Optional[Path]:
    df = curves[(curves.game_type == game_type) & (curves.platform == platform)]
    years = sorted(df.year.unique())
    if not years:
        return None
    colors = dict(zip(years, _ordered_colors(len(years))))

    fig = go.Figure()
    for year in years:
        g = df[df.year == year].sort_values("rating")
        has_band = g.pctl_lo.notna().any()
        if has_band:
            fig.add_trace(go.Scatter(
                x=pd.concat([g.rating, g.rating[::-1]]),
                y=pd.concat([g.pctl_hi, g.pctl_lo[::-1]]),
                fill="toself", fillcolor=colors[year], opacity=0.12,
                line=dict(width=0), hoverinfo="skip", showlegend=False,
            ))
        fig.add_trace(go.Scatter(
            x=g.rating, y=g.percentile, mode="lines",
            name=str(year), line=dict(color=colors[year], width=2),
            hovertemplate=(f"<b>{year}</b><br>Rating %{{x:.0f}}<br>"
                           "Percentil %{y:.1f}%<extra></extra>"),
        ))
    fig.update_layout(
        title=f"Chess.com {GAME_TYPE_LABEL.get(game_type, game_type)} — "
              f"percentil por rating, ano a ano (bandas: IC 95%)",
        xaxis_title="Rating", yaxis_title="Percentil (% de jogadores abaixo)",
        yaxis_range=[0, 100],
        plot_bgcolor=SURFACE, paper_bgcolor=PAGE,
        font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif',
                  color=INK_2),
        title_font_color=INK,
        legend_title_text="Ano",
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=BASELINE,
                     tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=BASELINE,
                     tickfont=dict(color=MUTED))
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"curves_{platform}_{game_type}.html"
    fig.write_html(path, include_plotlyjs="cdn")
    log.info("figura interativa: %s", path.name)
    return path


def generate_all(
    curves: pd.DataFrame, targets: pd.DataFrame, fixed: pd.DataFrame
) -> list[Path]:
    """Gera o conjunto completo de figuras; retorna os caminhos criados."""
    paths: list[Optional[Path]] = []
    for platform in curves.platform.unique():
        for gt in curves[curves.platform == platform].game_type.unique():
            paths.append(plot_year_curves(curves, gt, platform))
            paths.append(plot_percentile_targets(targets, gt, platform))
            paths.append(plot_fixed_ratings(fixed, gt, platform))
            paths.append(plot_heatmap(curves, gt, platform))
            paths.append(plotly_year_curves(curves, gt, platform))
    for gt in ("rapid", "blitz", "bullet", "classical"):
        paths.append(plot_platform_comparison(curves, gt))
    return [p for p in paths if p is not None]
