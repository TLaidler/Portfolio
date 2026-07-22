"""Fontes secundárias: Reddit, StackExchange, Lichess atual e URLs extras.

Todas produzem :class:`Observation` com confiança menor que a fonte primária.
O arquivo ``data/raw/extra_urls.txt`` permite injetar manualmente URLs achadas
pelo agente pesquisador (formato por linha: ``URL [YYYY-MM-DD] [source]``).
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from .parser import (
    decode_html,
    parse_free_text,
    parse_lichess_distribution,
)
from .utils import DATA_RAW, CachedSession, Observation, get_logger

log = get_logger(__name__)

REDDIT_QUERIES = [
    "chess.com percentile",
    "chess.com rating percentile",
    "rapid rating percentile chess.com",
    "blitz percentile chess.com",
    "chess.com rating distribution",
    "99 percentile chess.com",
    "top 5% chess.com rating",
]

STACKEXCHANGE_API = "https://api.stackexchange.com/2.3"
LICHESS_PERFS = ("rapid", "blitz", "bullet", "classical")
EXTRA_URLS_FILE = DATA_RAW / "extra_urls.txt"


class RedditSearcher:
    """Busca posts via o endpoint público ``search.json`` (sem OAuth).

    O Reddit pode recusar (403/429) UAs não autenticados; falhas são toleradas
    — a fonte é complementar.
    """

    def __init__(self, http: CachedSession) -> None:
        self.http = http

    def search(self, queries: Optional[list[str]] = None) -> list[Observation]:
        queries = queries or REDDIT_QUERIES
        out: list[Observation] = []
        seen_posts: set[str] = set()
        for q in tqdm(queries, desc="reddit", unit="query"):
            url = (
                "https://www.reddit.com/search.json?q="
                + q.replace(" ", "+")
                + "&limit=100&sort=relevance&t=all&raw_json=1"
            )
            status, body = self.http.get(url)
            if status != 200 or not body:
                log.warning("reddit search falhou (%s): %s", status, q)
                continue
            try:
                data = json.loads(body)
                posts = data["data"]["children"]
            except (json.JSONDecodeError, KeyError):
                continue
            for post in posts:
                d = post.get("data", {})
                pid = d.get("id", "")
                if not pid or pid in seen_posts:
                    continue
                seen_posts.add(pid)
                text = f"{d.get('title', '')}\n{d.get('selftext', '')}"
                created = d.get("created_utc")
                post_date = (
                    datetime.utcfromtimestamp(created).date() if created else None
                )
                permalink = "https://www.reddit.com" + d.get("permalink", "")
                obs = parse_free_text(
                    text, permalink, post_date,
                    source="reddit", base_confidence=0.7,
                )
                for o in obs:
                    log.info(
                        "reddit: %s %s %.0f -> %.1f%% (%s)",
                        post_date, o.game_type, o.rating, o.percentile,
                        d.get("subreddit", "?"),
                    )
                out.extend(obs)
        log.info("reddit: %d observações", len(out))
        return out


class StackExchangeSearcher:
    """Busca em chess.stackexchange.com via API pública (quota anônima)."""

    def __init__(self, http: CachedSession) -> None:
        self.http = http

    def search(self) -> list[Observation]:
        out: list[Observation] = []
        url = (
            f"{STACKEXCHANGE_API}/search/advanced?order=desc&sort=relevance"
            "&q=percentile%20rating&site=chess&pagesize=50"
            "&filter=withbody"
        )
        status, body = self.http.get(url)
        if status != 200 or not body:
            log.warning("stackexchange falhou (%s)", status)
            return out
        try:
            items = json.loads(body).get("items", [])
        except json.JSONDecodeError:
            return out
        for item in items:
            text = f"{item.get('title', '')}\n{item.get('body', '')}"
            created = item.get("creation_date")
            q_date = datetime.utcfromtimestamp(created).date() if created else None
            out.extend(
                parse_free_text(
                    text, item.get("link", ""), q_date,
                    source="stackexchange", base_confidence=0.6,
                )
            )
        log.info("stackexchange: %d observações", len(out))
        return out


def fetch_current_lichess(http: CachedSession, today: Optional[date] = None) -> list[Observation]:
    """Distribuição semanal ATUAL da Lichess (dado oficial completo)."""
    today = today or date.today()
    out: list[Observation] = []
    for perf in LICHESS_PERFS:
        url = f"https://lichess.org/stat/rating/distribution/{perf}"
        status, body = http.get(url, refresh=True, cache_errors=False)
        if status != 200 or not body:
            log.warning("lichess %s falhou (%s)", perf, status)
            continue
        obs = parse_lichess_distribution(decode_html(body), url, today, perf)
        log.info("lichess %s: %d buckets", perf, len(obs))
        out.extend(obs)
    return out


_EXTRA_LINE_RE = re.compile(
    r"^(?P<url>https?://\S+)(?:\s+(?P<date>\d{4}-\d{2}-\d{2}))?(?:\s+(?P<source>\w+))?\s*$"
)


def fetch_extra_urls(http: CachedSession) -> list[Observation]:
    """Processa URLs extras (achados do agente pesquisador / manuais)."""
    if not EXTRA_URLS_FILE.exists():
        return []
    out: list[Observation] = []
    lines = [
        ln.strip()
        for ln in EXTRA_URLS_FILE.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    for line in tqdm(lines, desc="urls extras", unit="url"):
        m = _EXTRA_LINE_RE.match(line)
        if not m:
            log.warning("linha inválida em extra_urls.txt: %s", line)
            continue
        url = m.group("url")
        url_date = (
            datetime.strptime(m.group("date"), "%Y-%m-%d").date()
            if m.group("date")
            else None
        )
        source = m.group("source") or "manual"
        status, body = http.get(url)
        if status != 200 or not body:
            continue
        text = decode_html(body)
        # remove tags para reduzir falsos positivos de regex em atributos
        text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        out.extend(
            parse_free_text(text, url, url_date, source=source, base_confidence=0.6)
        )
    log.info("urls extras: %d observações", len(out))
    return out
