"""Cliente da Chess.com para dados ATUAIS.

O Pub API oficial (``api.chess.com/pub``) não expõe percentil nem distribuição
de ratings. A curva atual (2026) é reconstruída buscando as páginas de stats
públicas dos MESMOS usuários amostrados no Wayback — o que reaproveita o
parser da fonte primária e cobre toda a faixa de rating.
"""
from __future__ import annotations

import dataclasses
import re
from datetime import date
from typing import Iterable, Optional

from tqdm import tqdm

from .parser import decode_html, game_type_from_url, parse_chesscom_stats_page
from .utils import CachedSession, Observation, get_logger

log = get_logger(__name__)

PUB_API = "https://api.chess.com/pub"
_USERNAME_FROM_STATS_URL = re.compile(
    r"chess\.com/stats/(?:live/(?:rapid|blitz|bullet|standard)|daily)/([A-Za-z0-9_-]+)"
)


def username_from_stats_url(url: str) -> Optional[str]:
    m = _USERNAME_FROM_STATS_URL.search(url)
    return m.group(1) if m else None


class ChessComClient:
    def __init__(self, http: CachedSession) -> None:
        self.http = http

    def fetch_current_stats_observations(
        self,
        stats_urls: Iterable[str],
        today: Optional[date] = None,
        limit_per_type: int = 250,
        refresh: bool = False,
    ) -> list[Observation]:
        """Busca páginas de stats atuais e extrai (rating, percentil) de hoje.

        ``stats_urls`` são URLs originais (sem Wayback); usuários deletados ou
        páginas sem percentil são simplesmente ignorados.
        """
        today = today or date.today()
        by_type: dict[str, list[str]] = {}
        for url in stats_urls:
            gt = game_type_from_url(url)
            user = username_from_stats_url(url)
            if not gt or not user:
                continue
            clean = f"https://www.chess.com/stats/live/{gt}/{user}"
            if gt == "daily":
                clean = f"https://www.chess.com/stats/daily/{user}"
            bucket = by_type.setdefault(gt, [])
            if clean not in bucket and len(bucket) < limit_per_type:
                bucket.append(clean)

        out: list[Observation] = []
        flat = [u for urls in by_type.values() for u in urls]
        for url in tqdm(flat, desc="chess.com atual", unit="page"):
            status, body = self.http.get(url, refresh=refresh)
            if status != 200 or not body:
                continue
            obs = parse_chesscom_stats_page(decode_html(body), url, today)
            if obs is not None:
                out.append(dataclasses.replace(obs, source="chesscom_live"))
        log.info("chess.com atual: %d observações de %d páginas", len(out), len(flat))
        return out

    def get_player_stats(self, username: str) -> Optional[dict]:
        """Endpoint oficial ``/pub/player/{user}/stats`` (sem percentil)."""
        import json

        status, body = self.http.get(f"{PUB_API}/player/{username}/stats")
        if status != 200 or not body:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
