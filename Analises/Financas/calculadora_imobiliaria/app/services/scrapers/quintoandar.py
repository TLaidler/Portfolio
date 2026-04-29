"""Scraper QuintoAndar — versão MVP.

ATENÇÃO: este scraper depende da API interna do QuintoAndar, que não é um contrato
público. A estrutura abaixo segue os princípios do plano (httpx + headers realistas
+ rate limit + parser tolerante), mas o endpoint exato e o schema da resposta podem
mudar sem aviso. Antes de habilitar em produção, é necessário validar via DevTools.

Comportamento atual: tenta o endpoint conhecido; se falhar (404/403/timeout), levanta
ScrapeError. O aggregator captura isso e oferece input manual ao usuário.
"""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.services.scrapers.models import Listing, SearchFilters
from app.utils.errors import ScrapeBlocked, ScrapeError, ScrapeTimeout

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

CITY_SLUGS = {
    "rio de janeiro": "rio-de-janeiro-rj-brasil",
    "rj": "rio-de-janeiro-rj-brasil",
}


class QuintoAndarScraper:
    name = "quintoandar"
    base_url = "https://www.quintoandar.com.br"

    def __init__(self, timeout: float = 8.0) -> None:
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Referer": f"{self.base_url}/alugar",
        }

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=8, min=8, max=128),
        reraise=True,
    )
    def _fetch_page(self, client: httpx.Client, url: str, params: dict) -> httpx.Response:
        time.sleep(random.uniform(2.0, 5.0))
        resp = client.get(url, params=params, timeout=self.timeout)
        if resp.status_code in (403, 503):
            raise ScrapeBlocked(f"QuintoAndar bloqueou: HTTP {resp.status_code}")
        resp.raise_for_status()
        return resp

    def search(self, filters: SearchFilters, max_results: int = 50) -> list[Listing]:
        slug = CITY_SLUGS.get(filters.city.lower().strip())
        if not slug:
            raise ScrapeError(f"Cidade não suportada no MVP: {filters.city!r}")

        # MVP: o endpoint da API interna mudou ao longo do tempo. Esta implementação
        # tenta a busca pública mas falha graciosamente se o site bloquear/mudar.
        try:
            with httpx.Client(headers=self._headers(), follow_redirects=True) as client:
                url = f"{self.base_url}/api/yellow-pages/v2/search"
                params = {"city": slug, "businessContext": "RENT", "size": min(max_results, 50)}
                resp = self._fetch_page(client, url, params)
                payload = resp.json()
                return self._parse_payload(payload, filters, max_results)
        except httpx.TimeoutException as exc:
            raise ScrapeTimeout("QuintoAndar timeout") from exc
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning("QuintoAndar parse falhou: %s", exc)
            raise ScrapeError(f"QuintoAndar indisponível: {exc}") from exc

    def _parse_payload(
        self, payload: dict, filters: SearchFilters, max_results: int
    ) -> list[Listing]:
        items = payload.get("hits") or payload.get("results") or payload.get("data") or []
        listings: list[Listing] = []
        now = datetime.now(timezone.utc)
        for item in items[:max_results]:
            try:
                price = Decimal(str(item.get("rent") or item.get("totalCost") or 0))
                area = float(item.get("area") or item.get("usableArea") or 0)
                if price <= 0 or area <= 0:
                    continue
                listings.append(Listing(
                    price=price,
                    area_m2=area,
                    bedrooms=item.get("bedrooms"),
                    neighborhood=(item.get("address") or {}).get("region"),
                    furnished=item.get("isFurnished"),
                    has_ac=None,
                    source="quintoandar",
                    url=f"{self.base_url}/imovel/{item.get('id', '')}",
                    scraped_at=now,
                ))
            except (TypeError, ValueError, KeyError):
                continue
        return listings
