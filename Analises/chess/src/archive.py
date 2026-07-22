"""Cliente do Internet Archive (Wayback Machine).

Duas responsabilidades:

1. Consultar o CDX API para listar snapshots de padrões de URL
   (ex.: ``chess.com/stats/live/rapid/*``) com amostragem estratificada por ano.
2. Baixar snapshots (usando o sufixo ``id_`` para obter o HTML original,
   sem a toolbar do Wayback) através do cache local.

O estágio *collect* grava um índice de snapshots em
``data/raw/snapshots_index.csv``; o estágio *parse* lê os corpos do cache.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from tqdm import tqdm

from .utils import (
    DATA_RAW,
    CachedSession,
    get_logger,
    seeded_sample,
)

log = get_logger(__name__)

CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"

# Padrões de URL das páginas de stats por modalidade. O padrão "standard"
# é a nomenclatura antiga (pré-2018) do que virou "rapid".
STATS_URL_PATTERNS: dict[str, list[str]] = {
    "rapid": ["chess.com/stats/live/rapid/*", "chess.com/stats/live/standard/*"],
    "blitz": ["chess.com/stats/live/blitz/*"],
    "bullet": ["chess.com/stats/live/bullet/*"],
    "daily": ["chess.com/stats/daily/*"],
}

# Páginas agregadas com histórico mensal no Wayback.
AGGREGATE_TARGETS: list[tuple[str, str, str]] = [
    # (source_tag, padrão CDX, game_type quando fixo — "" = detectar no parse)
    ("chessgoals", "chessgoals.com/rating-comparison/", ""),
    ("chessgoals", "chessgoals.com/descriptive-data/", ""),
    ("lichess_dist", "lichess.org/stat/rating/distribution/rapid", "rapid"),
    ("lichess_dist", "lichess.org/stat/rating/distribution/blitz", "blitz"),
    ("lichess_dist", "lichess.org/stat/rating/distribution/bullet", "bullet"),
    ("lichess_dist", "lichess.org/stat/rating/distribution/classical", "classical"),
]

SNAPSHOT_INDEX = DATA_RAW / "snapshots_index.csv"
INDEX_COLUMNS = ["kind", "source", "game_type", "timestamp", "original", "fetch_url", "status"]


@dataclass(frozen=True)
class CdxRow:
    """Uma linha do CDX API."""

    urlkey: str
    timestamp: str  # YYYYMMDDhhmmss
    original: str
    mimetype: str
    statuscode: str
    digest: str
    length: str

    @property
    def dt(self) -> datetime:
        return datetime.strptime(self.timestamp, "%Y%m%d%H%M%S")

    @property
    def fetch_url(self) -> str:
        # sufixo id_ => conteúdo original arquivado, sem rewriting da toolbar
        return f"https://web.archive.org/web/{self.timestamp}id_/{self.original}"


class WaybackClient:
    """Wrapper fino sobre o CDX API + download de snapshots."""

    def __init__(self, http: CachedSession) -> None:
        self.http = http

    def cdx_query(
        self,
        url_pattern: str,
        *,
        from_: str = "",
        to: str = "",
        limit: int = 5000,
        collapse: str = "urlkey",
        refresh: bool = False,
    ) -> list[CdxRow]:
        """Lista snapshots de um padrão de URL (statuscode 200, HTML)."""
        params = (
            f"url={url_pattern}&output=json&limit={limit}"
            "&filter=statuscode:200&filter=mimetype:text/html"
        )
        if collapse:
            params += f"&collapse={collapse}"
        if from_:
            params += f"&from={from_}"
        if to:
            params += f"&to={to}"
        full_url = f"{CDX_ENDPOINT}?{params}"

        status, body = self.http.get(full_url, refresh=refresh, timeout=120)
        if status != 200 or not body:
            log.warning("CDX falhou (%s) para %s", status, url_pattern)
            return []
        try:
            rows = json.loads(body)
        except json.JSONDecodeError:
            log.warning("CDX retornou JSON inválido para %s", url_pattern)
            return []
        if not rows or len(rows) < 2:
            return []
        return [CdxRow(*r[:7]) for r in rows[1:] if len(r) >= 7]

    # ------------------------------------------------------------------
    # Amostragem estratificada das páginas de stats
    # ------------------------------------------------------------------
    def sample_stats_snapshots(
        self,
        game_type: str,
        year: int,
        target: int,
        cdx_limit: int = 5000,
    ) -> list[CdxRow]:
        """Snapshots de páginas de stats de ``game_type`` capturados em ``year``.

        Junta todos os padrões de URL da modalidade e amostra
        deterministicamente até ``target`` snapshots.
        """
        rows: list[CdxRow] = []
        for pattern in STATS_URL_PATTERNS[game_type]:
            rows.extend(
                self.cdx_query(
                    pattern,
                    from_=str(year),
                    to=str(year),
                    limit=cdx_limit,
                )
            )
        # dedup por urlkey (o mesmo jogador pode aparecer em 2 padrões)
        unique = {r.urlkey + r.timestamp: r for r in rows}
        # seed determinística entre processos (hash() nativo é randomizado)
        gt_code = sum(ord(c) for c in game_type)
        sampled = seeded_sample(sorted(unique.values(), key=lambda r: r.urlkey),
                                target, seed=year * 7 + gt_code)
        log.info("%s/%d: %d snapshots no CDX, %d amostrados",
                 game_type, year, len(unique), len(sampled))
        return sampled

    def list_aggregate_snapshots(self) -> list[tuple[str, str, CdxRow]]:
        """Snapshots (mensais) das páginas agregadas configuradas."""
        out: list[tuple[str, str, CdxRow]] = []
        for source, pattern, game_type in AGGREGATE_TARGETS:
            rows = self.cdx_query(pattern, collapse="timestamp:6", limit=1000)
            log.info("agregado %s (%s): %d snapshots mensais", source, pattern, len(rows))
            out.extend((source, game_type, r) for r in rows)
        return out

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------
    def download(self, rows: Iterable[CdxRow], desc: str = "download") -> dict[str, int]:
        """Baixa snapshots para o cache. Retorna {fetch_url: status}."""
        statuses: dict[str, int] = {}
        for row in tqdm(list(rows), desc=desc, unit="snap"):
            status, _ = self.http.get(row.fetch_url)
            statuses[row.fetch_url] = status
        return statuses


# ---------------------------------------------------------------------------
# Índice de snapshots baixados (liga collect → parse)
# ---------------------------------------------------------------------------
def append_to_index(entries: list[dict]) -> None:
    """Anexa entradas ao índice, evitando duplicatas por fetch_url."""
    SNAPSHOT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    existing: set[str] = set()
    if SNAPSHOT_INDEX.exists():
        with open(SNAPSHOT_INDEX, newline="", encoding="utf-8") as fh:
            existing = {row["fetch_url"] for row in csv.DictReader(fh)}
    new = [e for e in entries if e["fetch_url"] not in existing]
    write_header = not SNAPSHOT_INDEX.exists()
    with open(SNAPSHOT_INDEX, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=INDEX_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerows(new)
    log.info("índice: +%d entradas (%d já existiam)", len(new), len(entries) - len(new))


def read_index() -> list[dict]:
    if not SNAPSHOT_INDEX.exists():
        return []
    with open(SNAPSHOT_INDEX, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
