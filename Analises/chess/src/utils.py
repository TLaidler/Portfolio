"""Utilidades compartilhadas: configuração, logging, modelo de dados e HTTP cacheado.

Todos os acessos de rede do projeto passam por :class:`CachedSession`, que
aplica rate-limit por host, retries com backoff e cache persistente em SQLite
(``data/raw/cache.db``) — tornando a coleta resumível e reprodutível.
"""
from __future__ import annotations

import logging
import random
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Caminhos e constantes
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"

GAME_TYPES = ("rapid", "blitz", "bullet", "daily")
PLATFORMS = ("chesscom", "lichess")

USER_AGENT = (
    "chess-rating-history-research/0.1 "
    "(academic/portfolio project; contact: thiago.cunha@transfero.com)"
)

RANDOM_SEED = 42


def get_logger(name: str) -> logging.Logger:
    """Logger com formato único para todo o projeto."""
    logger = logging.getLogger(name)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    return logger


# ---------------------------------------------------------------------------
# Modelo de dados
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Observation:
    """Uma observação histórica (rating, percentil) numa data conhecida.

    ``percentile`` usa SEMPRE a convenção clássica: percentual de jogadores
    com rating igual ou inferior (0–100). Fontes que publicam "top X%" são
    convertidas no parser via ``100 - X``.
    """

    date: date
    source: str          # wayback_stats | reddit | chessgoals | forum | chesscom_api | lichess_dist | manual
    game_type: str       # rapid | blitz | bullet | daily | classical (lichess)
    rating: float
    percentile: float    # convenção clássica (0-100)
    url: str
    confidence: float    # 0.0 – 1.0
    platform: str = "chesscom"
    note: str = ""

    def is_valid(self) -> bool:
        return (
            0.0 <= self.percentile <= 100.0
            and 100 <= self.rating <= 3600
            and self.game_type in (*GAME_TYPES, "classical")
            and self.platform in PLATFORMS
        )


OBSERVATION_COLUMNS = [
    "date", "source", "game_type", "rating", "percentile",
    "url", "confidence", "platform", "note",
]


# ---------------------------------------------------------------------------
# Rate limiter simples por host
# ---------------------------------------------------------------------------
class _RateLimiter:
    """Garante intervalo mínimo entre requisições ao mesmo host."""

    def __init__(self) -> None:
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, host: str, min_interval: float) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last.get(host, 0.0)
            sleep_for = max(0.0, min_interval - elapsed)
        if sleep_for > 0:
            time.sleep(sleep_for)
        with self._lock:
            self._last[host] = time.monotonic()


# Intervalos mínimos (segundos) por host; default conservador.
HOST_INTERVALS = {
    "web.archive.org": 1.2,
    "api.chess.com": 0.6,
    "www.reddit.com": 2.0,
    "lichess.org": 1.0,
}
DEFAULT_INTERVAL = 1.0


# ---------------------------------------------------------------------------
# Sessão HTTP com cache SQLite
# ---------------------------------------------------------------------------
class CachedSession:
    """``requests.Session`` com retry, rate-limit e cache persistente.

    O cache guarda o corpo e o status de cada GET por URL. Respostas de erro
    (>=400) também são cacheadas para não re-tentar snapshots quebrados a cada
    execução — use ``refresh=True`` para forçar novo download.
    """

    def __init__(self, cache_path: Optional[Path] = None) -> None:
        self.log = get_logger(self.__class__.__name__)
        cache_path = cache_path or (DATA_RAW / "cache.db")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(cache_path), check_same_thread=False)
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS http_cache (
                   url TEXT PRIMARY KEY,
                   fetched_at TEXT NOT NULL,
                   status INTEGER NOT NULL,
                   content BLOB
               )"""
        )
        self._db.commit()
        self._db_lock = threading.Lock()
        self._limiter = _RateLimiter()

        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        retry = Retry(
            total=4,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # -- cache helpers ------------------------------------------------------
    def _cache_get(self, url: str) -> Optional[tuple[int, bytes]]:
        with self._db_lock:
            row = self._db.execute(
                "SELECT status, content FROM http_cache WHERE url = ?", (url,)
            ).fetchone()
        return (row[0], row[1]) if row else None

    def _cache_put(self, url: str, status: int, content: bytes) -> None:
        with self._db_lock:
            self._db.execute(
                "INSERT OR REPLACE INTO http_cache (url, fetched_at, status, content)"
                " VALUES (?, ?, ?, ?)",
                (url, datetime.utcnow().isoformat(), status, content),
            )
            self._db.commit()

    def cached_urls(self, like: str) -> list[str]:
        """URLs já cacheadas que casam com um padrão SQL LIKE."""
        with self._db_lock:
            rows = self._db.execute(
                "SELECT url FROM http_cache WHERE url LIKE ? AND status = 200", (like,)
            ).fetchall()
        return [r[0] for r in rows]

    # -- GET ----------------------------------------------------------------
    def get(
        self,
        url: str,
        *,
        refresh: bool = False,
        timeout: float = 60.0,
        cache_errors: bool = True,
    ) -> tuple[int, bytes]:
        """GET com cache. Retorna ``(status_code, body)``; nunca levanta por status.

        Erros de rede (timeout/conexão) retornam ``(0, b"")`` sem cachear.
        """
        if not refresh:
            hit = self._cache_get(url)
            if hit is not None:
                return hit

        host = requests.utils.urlparse(url).hostname or ""
        self._limiter.wait(host, HOST_INTERVALS.get(host, DEFAULT_INTERVAL))
        try:
            resp = self.session.get(url, timeout=timeout)
        except requests.RequestException as exc:
            self.log.warning("falha de rede em %s: %s", url, exc)
            return 0, b""

        if resp.status_code == 200 or cache_errors:
            self._cache_put(url, resp.status_code, resp.content)
        return resp.status_code, resp.content

    def close(self) -> None:
        self.session.close()
        with self._db_lock:
            self._db.close()


def seeded_sample(items: list, k: int, seed: int = RANDOM_SEED) -> list:
    """Amostra determinística (reprodutível) de até ``k`` itens."""
    if len(items) <= k:
        return list(items)
    rng = random.Random(seed)
    return rng.sample(items, k)
