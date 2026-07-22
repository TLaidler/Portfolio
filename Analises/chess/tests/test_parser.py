"""Testes dos parsers com fixtures de HTML real (snapshots do Wayback)."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser import (
    game_type_from_url,
    parse_chesscom_stats_page,
    parse_free_text,
    parse_lichess_distribution,
    snapshot_date_from_fetch_url,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- stats pages
def test_stats_page_regular_player_2022():
    obs = parse_chesscom_stats_page(
        _load("0s0s00_2022.html"),
        "https://www.chess.com/stats/live/rapid/0s0s00",
        date(2022, 9, 12),
    )
    assert obs is not None
    assert obs.rating == 947
    assert obs.percentile == 70.3
    assert obs.game_type == "rapid"
    assert obs.confidence == 1.0
    assert "rated_count=1330" in obs.note


def test_stats_page_weak_player_percentile_is_classic():
    """Jogador de 397 deve ter percentil BAIXO (convenção clássica)."""
    obs = parse_chesscom_stats_page(
        _load("bobcobbsboggletoggle_202104.html"),
        "https://www.chess.com/stats/live/rapid/bobcobbsboggletoggle",
        date(2021, 4, 3),
    )
    assert obs is not None
    assert obs.rating == 397
    assert obs.percentile == 8.5


def test_stats_page_null_percentile_returns_none():
    """Jogador com poucas partidas tem percentile:null -> sem observação."""
    obs = parse_chesscom_stats_page(
        _load("0gzpanda_2025.html"),
        "https://www.chess.com/stats/live/rapid/0gzpanda",
        date(2025, 2, 21),
    )
    assert obs is None


def test_stats_page_angular_era_returns_none():
    """Páginas de 2018 (era Angular) não têm percentil."""
    obs = parse_chesscom_stats_page(
        _load("amrugg_2018.html"),
        "https://www.chess.com/stats/live/rapid/amrugg",
        date(2018, 9, 4),
    )
    assert obs is None


def test_game_type_from_url():
    assert game_type_from_url("https://www.chess.com/stats/live/rapid/x") == "rapid"
    assert game_type_from_url("https://www.chess.com/stats/live/standard/x") == "rapid"
    assert game_type_from_url("https://www.chess.com/stats/daily/x") == "daily"
    assert game_type_from_url("https://example.com/") is None


def test_snapshot_date_from_fetch_url():
    url = "https://web.archive.org/web/20220724102357id_/https://www.chess.com/stats/live/rapid/00beni"
    assert snapshot_date_from_fetch_url(url) == date(2022, 7, 24)


# ---------------------------------------------------------------- texto livre
@pytest.mark.parametrize(
    "text,expected",
    [
        ("I'm rated 1800 (99.3%) in rapid", (1800.0, 99.3)),
        ("my blitz: 1200 -> 90% percentile", (1200.0, 90.0)),
        ("Rating: 1520\nPercentile: 97.2 (bullet)", (1520.0, 97.2)),
        ("1112 is in the 79.5 percentile on rapid", (1112.0, 79.5)),
    ],
)
def test_free_text_patterns(text, expected):
    obs = parse_free_text(text, "http://x", date(2021, 5, 1))
    assert (obs[0].rating, obs[0].percentile) == expected


def test_free_text_top_percent_is_converted():
    obs = parse_free_text("I am 1500 rapid, top 5% of players", "u", date(2022, 1, 1))
    assert (obs[0].rating, obs[0].percentile) == (1500.0, 95.0)


def test_free_text_without_game_type_is_discarded():
    assert parse_free_text("I am 1500, top 5%", "u", date(2022, 1, 1)) == []


def test_free_text_without_date_lowers_confidence():
    obs = parse_free_text("rapid 1200 -> 90%", "u", None)
    assert obs[0].confidence == 0.4


# ---------------------------------------------------------------- lichess
def test_lichess_distribution_cdf():
    freq = [0] * 40
    freq[10] = 100   # bucket até 875
    html = f'<script>lichess.ratingDistributionChart({{freq:[{",".join(map(str,freq))}],"myRating":null}})</script>'
    obs = parse_lichess_distribution(html, "u", date(2020, 1, 1), "blitz")
    assert obs == []  # total (100) < 1000 é rejeitado

    freq[20] = 900   # bucket até 1125

    freq[30] = 9000  # agora total = 10000
    html = f'<script>lichess.ratingDistributionChart({{freq:[{",".join(map(str,freq))}]}})</script>'
    obs = parse_lichess_distribution(html, "u", date(2020, 1, 1), "blitz")
    assert obs, "distribuição válida deve gerar observações"
    by_rating = {o.rating: o.percentile for o in obs}
    assert by_rating[600 + 11 * 25] == pytest.approx(1.0)    # 100/10000
    assert by_rating[600 + 21 * 25] == pytest.approx(10.0)   # 1000/10000
    assert all(o.platform == "lichess" for o in obs)
    # monotônico
    pcts = [o.percentile for o in sorted(obs, key=lambda o: o.rating)]
    assert pcts == sorted(pcts)
