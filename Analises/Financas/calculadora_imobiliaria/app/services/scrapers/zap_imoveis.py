"""Scraper ZapImóveis — versão MVP.

Mesmas observações do quintoandar.py: depende de API interna não-contratada.
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
]


class ZapImoveisScraper:
    name = "zap"
    base_url = "https://www.zapimoveis.com.br"
    api_url = "https://glue-api.zapimoveis.com.br/v3/listings"

    def __init__(self, timeout: float = 8.0) -> None:
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "x-domain": "www.zapimoveis.com.br",
            "Referer": f"{self.base_url}/aluguel/",
            "Origin": self.base_url,
        }

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=8, min=8, max=128),
        reraise=True,
    )
    def _fetch(self, client: httpx.Client, params: dict) -> httpx.Response:
        time.sleep(random.uniform(2.0, 5.0))
        resp = client.get(self.api_url, params=params, timeout=self.timeout)
        if resp.status_code in (403, 503):
            raise ScrapeBlocked(f"Zap bloqueou: HTTP {resp.status_code}")
        resp.raise_for_status()
        return resp

    def search(self, filters: SearchFilters, max_results: int = 50) -> list[Listing]:
        if filters.city.lower().strip() not in ("rio de janeiro", "rj"):
            raise ScrapeError(f"Cidade não suportada no MVP: {filters.city!r}")

        params = {
            "business": "RENTAL",
            "addressCity": "Rio de Janeiro",
            "addressState": "Rio de Janeiro",
            "size": min(max_results, 50),
            "from": 0,
            "listingType": "USED",
        }

        try:
            with httpx.Client(headers=self._headers(), follow_redirects=True) as client:
                resp = self._fetch(client, params)
                return self._parse_payload(resp.json(), max_results)
        except httpx.TimeoutException as exc:
            raise ScrapeTimeout("Zap timeout") from exc
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning("Zap parse falhou: %s", exc)
            raise ScrapeError(f"Zap indisponível: {exc}") from exc

    def _parse_payload(self, payload: dict, max_results: int) -> list[Listing]:
        results = (payload.get("search") or {}).get("result", {}).get("listings", []) \
            or payload.get("listings") or []
        listings: list[Listing] = []
        now = datetime.now(timezone.utc)
        for entry in results[:max_results]:
            try:
                listing = entry.get("listing", entry)
                pricing = (listing.get("pricingInfos") or [{}])[0]
                price = Decimal(str(pricing.get("rentalTotalPrice") or pricing.get("price") or 0))
                area = float((listing.get("usableAreas") or [0])[0] or 0)
                if price <= 0 or area <= 0:
                    continue
                address = listing.get("address") or {}
                listings.append(Listing(
                    price=price,
                    area_m2=area,
                    bedrooms=int((listing.get("bedrooms") or [0])[0] or 0) or None,
                    neighborhood=address.get("neighborhood"),
                    furnished=None,
                    has_ac="AIR_CONDITIONING" in (listing.get("amenities") or []),
                    source="zap",
                    url=f"{self.base_url}/imovel/{listing.get('id', '')}",
                    scraped_at=now,
                ))
            except (TypeError, ValueError, KeyError):
                continue
        return listings
