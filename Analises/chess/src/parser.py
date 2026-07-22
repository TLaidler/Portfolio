"""Parsers das fontes brutas → :class:`Observation`.

Formatos suportados (verificados empiricamente em snapshots reais):

* **Páginas de stats da Chess.com (era Vue, ~2021→hoje)** — JSON embutido em
  ``window.chesscom.stats = { userData: {..., "rating": R, "percentile": P} }``.
  O campo ``percentile`` usa a convenção CLÁSSICA (percentual de membros com
  rating igual ou inferior); verificado com jogadores fracos (397 → 8.5) e
  fortes (2118 → 99.9). O campo passou a existir por volta de jan/2021;
  páginas da era Angular (2018–2020) têm apenas o histórico de rating, sem
  percentil — por isso os anos pré-2021 dependem de fontes secundárias.
* **Texto livre** (Reddit, fóruns, StackExchange) — padrões regex do tipo
  ``1800 -> 98.7%``, ``rated 1800 (99.3%)``, ``Rating: 1520 / Percentile: 97.2``.
* **Lichess** — página ``/stat/rating/distribution/{perf}`` com a distribuição
  semanal embutida (``freq``/histograma), da qual o percentil exato é derivado.
* **Tabelas do ChessGoals** — HTML com colunas percentil × rating por modalidade.
"""
from __future__ import annotations

import json
import math
import re
from datetime import date, datetime
from typing import Iterable, Optional

from .utils import GAME_TYPES, Observation, get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# 1. Páginas de stats da Chess.com (fonte primária, confiança 1.0)
# ---------------------------------------------------------------------------
_GAME_TYPE_FROM_URL = re.compile(
    r"chess\.com/stats/(?:live/)?(rapid|blitz|bullet|standard|daily)", re.I
)


def game_type_from_url(url: str) -> Optional[str]:
    m = _GAME_TYPE_FROM_URL.search(url)
    if not m:
        return None
    gt = m.group(1).lower()
    return "rapid" if gt == "standard" else gt


def _extract_balanced_json(text: str, start: int) -> Optional[str]:
    """Extrai um objeto JSON balanceado começando em ``text[start] == '{'``."""
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


_USERDATA_RE = re.compile(r"userData\s*:\s*\{")
# Fallback regex caso o JSON não seja parseável: campos adjacentes observados
# em todas as eras Vue (2021–2025): ..."rating":R,...,"percentile":P
_RATING_PCTL_RE = re.compile(
    r'"rating":(\d{3,4}),"leaderboardRank":(?:\d+|null),'
    r'"highestRating":\{[^}]*\},"percentile":([\d.]+)'
)


def parse_chesscom_stats_page(
    html: str, url: str, snapshot_date: date
) -> Optional[Observation]:
    """Extrai (rating, percentil) de uma página de stats arquivada.

    Retorna ``None`` quando a página não tem o campo percentil (eras antigas,
    jogadores de leaderboard — para os quais o campo é omitido — ou stubs de
    erro do Wayback).
    """
    game_type = game_type_from_url(url)
    if game_type is None:
        return None

    rating: Optional[float] = None
    percentile: Optional[float] = None
    rated_count: Optional[int] = None
    leaderboard_rank: Optional[int] = None

    m = _USERDATA_RE.search(html)
    if m:
        blob = _extract_balanced_json(html, m.end() - 1)
        if blob:
            try:
                data = json.loads(blob)
                rating = data.get("rating")
                percentile = data.get("percentile")
                rated_count = data.get("ratedCount")
                leaderboard_rank = data.get("leaderboardRank")
            except (json.JSONDecodeError, AttributeError):
                pass

    if rating is None or percentile is None:
        fm = _RATING_PCTL_RE.search(html)
        if fm:
            rating = float(fm.group(1))
            percentile = float(fm.group(2))

    if rating is None or percentile is None:
        return None

    note_parts = []
    if rated_count is not None:
        note_parts.append(f"rated_count={rated_count}")
    if leaderboard_rank:
        note_parts.append(f"leaderboard_rank={leaderboard_rank}")
        # população implícita: rank / (1 - percentil/100)
        if 0 < float(percentile) < 100:
            implied = int(leaderboard_rank / (1 - float(percentile) / 100))
            note_parts.append(f"implied_population={implied}")

    return Observation(
        date=snapshot_date,
        source="wayback_stats",
        game_type=game_type,
        rating=float(rating),
        percentile=float(percentile),
        url=url,
        confidence=1.0,
        platform="chesscom",
        note=";".join(note_parts),
    )


def snapshot_date_from_fetch_url(fetch_url: str) -> Optional[date]:
    """Data a partir de uma URL do Wayback (``/web/YYYYMMDDhhmmss.../``)."""
    m = re.search(r"/web/(\d{14})", fetch_url)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y%m%d%H%M%S").date()


# ---------------------------------------------------------------------------
# 2. Texto livre (Reddit, fóruns, StackExchange) — confiança 0.4–0.7
# ---------------------------------------------------------------------------
_GT_WORDS = {
    "rapid": "rapid",
    "blitz": "blitz",
    "bullet": "bullet",
    "daily": "daily",
    "correspondence": "daily",
    "classical": "classical",
}

# Padrões (rating, percentil). Percentil pode vir como "top X%" — flag no grupo.
_FREE_TEXT_PATTERNS: list[tuple[re.Pattern, bool]] = [
    # "1800 -> 98.7%" / "1800 → 98.7%" / "1800 = 98.7%"
    (re.compile(r"\b([1-9]\d{2,3})\s*(?:->|→|=|:)\s*(\d{1,2}(?:\.\d+)?)\s*(?:th)?\s*(?:%|percentile)", re.I), False),
    # "rated 1800 (99.3%)" / "rating 1800 (99.3 percentile)"
    (re.compile(r"\brat(?:ed|ing)\s*:?\s*([1-9]\d{2,3})\s*\((\d{1,2}(?:\.\d+)?)\s*(?:%|th)?\s*(?:percentile)?\)", re.I), False),
    # "Rating: 1520 ... Percentile: 97.2"
    (re.compile(r"\brating\s*:?\s*([1-9]\d{2,3})\b.{0,80}?\bpercentile\s*:?\s*(\d{1,2}(?:\.\d+)?)", re.I | re.S), False),
    # "1500 is (in) the 97th percentile"
    (re.compile(r"\b([1-9]\d{2,3})\s+is\s+(?:in\s+)?(?:the\s+)?(\d{1,2}(?:\.\d+)?)\s*(?:th|st|nd|rd)?\s*percentile", re.I), False),
    # "I'm 1500 (rapid), top 5%"  → top X% (converter)
    (re.compile(r"\b([1-9]\d{2,3})\b.{0,60}?\btop\s+(\d{1,2}(?:\.\d+)?)\s*%", re.I | re.S), True),
    # "top 5% ... 1500 rating"
    (re.compile(r"\btop\s+(\d{1,2}(?:\.\d+)?)\s*%.{0,60}?\b([1-9]\d{2,3})\b", re.I | re.S), True),
]


def _detect_game_type(text: str) -> Optional[str]:
    found = {gt for word, gt in _GT_WORDS.items() if re.search(rf"\b{word}\b", text, re.I)}
    return found.pop() if len(found) == 1 else None


def parse_free_text(
    text: str,
    url: str,
    text_date: Optional[date],
    source: str = "reddit",
    base_confidence: float = 0.7,
    platform: str = "chesscom",
) -> list[Observation]:
    """Extrai pares (rating, percentil) de texto livre.

    Sem data conhecida a confiança cai para 0.4 (e a observação só é útil se
    algum estágio posterior conseguir datá-la); sem modalidade detectável a
    observação é descartada.
    """
    game_type = _detect_game_type(text)
    if game_type is None:
        return []
    confidence = base_confidence if text_date else 0.4

    seen: set[tuple[float, float]] = set()
    out: list[Observation] = []
    for pattern, is_top in _FREE_TEXT_PATTERNS:
        for m in pattern.finditer(text):
            if is_top and pattern.pattern.startswith("\\btop"):
                pct_raw, rating_raw = m.group(1), m.group(2)
            else:
                rating_raw, pct_raw = m.group(1), m.group(2)
            try:
                rating = float(rating_raw)
                pct = float(pct_raw)
            except ValueError:
                continue
            if is_top:
                pct = 100.0 - pct
            key = (rating, round(pct, 1))
            if key in seen or not (0 < pct < 100) or not (100 <= rating <= 3600):
                continue
            seen.add(key)
            out.append(
                Observation(
                    date=text_date or date(1970, 1, 1),
                    source=source,
                    game_type=game_type,
                    rating=rating,
                    percentile=pct,
                    url=url,
                    confidence=confidence,
                    platform=platform,
                    note="top_x_converted" if is_top else "",
                )
            )
    return out


# ---------------------------------------------------------------------------
# 3. Distribuição da Lichess — confiança 1.0 (dado oficial completo)
# ---------------------------------------------------------------------------
# A página embute o histograma semanal. Formatos observados ao longo dos anos:
#   lichess.ratingDistributionChart({freq:[..],...})           (2016–2020)
#   LichessChart.ratingDistribution({freq:[..],...})           (variações)
#   {"freq":[...],"myRating":null,...}                         (JSON moderno)
_LICHESS_FREQ_RE = re.compile(r'"?freq"?\s*:\s*\[([\d,\s]+)\]')

LICHESS_BUCKET_WIDTH = 25    # largura de cada bucket
# O primeiro bucket acompanhou o piso de rating da Lichess: 800 até jul/2019,
# 600 depois (lila commit 67637670e8, 2019-07-01, "update min rating").
_LICHESS_FLOOR_CHANGE = date(2019, 7, 1)


def lichess_bucket_start(snapshot_date: date) -> int:
    return 600 if snapshot_date >= _LICHESS_FLOOR_CHANGE else 800


def parse_lichess_distribution(
    html: str, url: str, snapshot_date: date, game_type: str
) -> list[Observation]:
    """Converte o histograma da Lichess em observações (rating, percentil).

    Gera uma observação por bucket (limite superior do bucket → percentil
    acumulado), o que descreve a CDF exata daquela semana.
    """
    m = _LICHESS_FREQ_RE.search(html)
    if not m:
        return []
    try:
        freq = [int(x) for x in m.group(1).replace(" ", "").split(",") if x]
    except ValueError:
        return []
    total = sum(freq)
    if total < 1000:  # página quebrada / distribuição vazia
        return []

    start = lichess_bucket_start(snapshot_date)
    out: list[Observation] = []
    cum = 0
    for i, count in enumerate(freq):
        cum += count
        upper = start + (i + 1) * LICHESS_BUCKET_WIDTH
        pct = 100.0 * cum / total
        if pct >= 100.0 and count == 0:
            continue
        out.append(
            Observation(
                date=snapshot_date,
                source="lichess_dist",
                game_type=game_type,
                rating=float(upper),
                percentile=round(pct, 4),
                url=url,
                confidence=1.0,
                platform="lichess",
                note=f"weekly_players={total}",
            )
        )
    return out


# ---------------------------------------------------------------------------
# 4. Tabelas do ChessGoals — confiança 0.9
# ---------------------------------------------------------------------------
# As tabelas têm linhas "percentil | lichess X | chess.com Y" por modalidade.
# Estrutura muda entre versões; extraímos pares de células numéricas de
# tabelas cujo cabeçalho mencione percentile + modalidade.
_TABLE_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.I | re.S)
_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.I | re.S)
_TAG_RE = re.compile(r"<[^>]+>")


def _cell_text(cell_html: str) -> str:
    return _TAG_RE.sub("", cell_html).replace("&nbsp;", " ").strip()


def parse_chessgoals_tables(
    html: str, url: str, snapshot_date: date
) -> list[Observation]:
    """Extrai observações das tabelas de percentil do ChessGoals.

    Cabeçalhos esperados (variam entre versões): colunas contendo
    "percentile" e colunas "chess.com rapid", "lichess blitz" etc.
    """
    out: list[Observation] = []
    for table_html in _TABLE_RE.findall(html):
        rows = _ROW_RE.findall(table_html)
        if len(rows) < 3:
            continue
        header = [_cell_text(c).lower() for c in _CELL_RE.findall(rows[0])]
        if not header or not any("percentile" in h for h in header):
            continue
        try:
            pct_idx = next(i for i, h in enumerate(header) if "percentile" in h)
        except StopIteration:
            continue

        # mapeia colunas → (plataforma, modalidade)
        col_map: dict[int, tuple[str, str]] = {}
        for i, h in enumerate(header):
            if i == pct_idx:
                continue
            platform = "lichess" if "lichess" in h else ("chesscom" if "chess.com" in h or "chesscom" in h else "")
            gt = next((g for g in (*GAME_TYPES, "classical") if g in h), "")
            if platform and gt:
                col_map[i] = (platform, gt)
        if not col_map:
            continue

        for row_html in rows[1:]:
            cells = [_cell_text(c) for c in _CELL_RE.findall(row_html)]
            if len(cells) <= pct_idx:
                continue
            pct_m = re.search(r"(\d{1,2}(?:\.\d+)?)", cells[pct_idx])
            if not pct_m:
                continue
            pct = float(pct_m.group(1))
            for i, (platform, gt) in col_map.items():
                if i >= len(cells):
                    continue
                r_m = re.search(r"\b([1-9]\d{2,3})\b", cells[i].replace(",", ""))
                if not r_m:
                    continue
                rating = float(r_m.group(1))
                if not (100 <= rating <= 3600 and 0 < pct < 100):
                    continue
                out.append(
                    Observation(
                        date=snapshot_date,
                        source="chessgoals",
                        game_type=gt,
                        rating=rating,
                        percentile=pct,
                        url=url,
                        confidence=0.9,
                        platform=platform,
                        note="",
                    )
                )
    return out


def maybe_gunzip(body: bytes) -> bytes:
    """Snapshots com sufixo ``id_`` podem vir com gzip cru (bytes originais)."""
    if body[:2] == b"\x1f\x8b":
        import gzip

        try:
            return gzip.decompress(body)
        except OSError:
            return body
    return body


def decode_html(body: bytes) -> str:
    return maybe_gunzip(body).decode("utf-8", errors="replace")
