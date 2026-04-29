"""Agregador: combina resultados dos scrapers e calcula estatísticas.

Para o MVP, este módulo já tem estrutura completa mas usa apenas QuintoAndar e
Zap quando disponíveis. Quando ambos falham (ou não estão implementados),
retorna ScrapeResult com error preenchido para o frontend mostrar input manual.
"""
from __future__ import annotations

import logging
import statistics
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from app.services.scrapers.models import Listing, RentalStats, ScrapeResult, SearchFilters
from app.utils.errors import ScrapeError

logger = logging.getLogger(__name__)

MIN_LISTINGS = 5


class RentalAggregator:
    def __init__(self, db_path: Path | str, ttl_hours: int = 6) -> None:
        self.db_path = db_path
        self.ttl_hours = ttl_hours

    def search(
        self,
        city: str,
        neighborhood: str | None = None,
        area_min: float | None = None,
        area_max: float | None = None,
        furnished: bool | None = None,
        has_ac: bool | None = None,
    ) -> ScrapeResult:
        filters = SearchFilters(
            city=city,
            neighborhood=neighborhood,
            area_min=area_min,
            area_max=area_max,
            furnished=furnished,
            has_ac=has_ac,
        )
        listings: list[Listing] = []

        # Os scrapers reais entram aqui em iterações futuras (rodam em paralelo
        # via concurrent.futures, com cache SQLite e fallback gracioso).
        # Por enquanto, lançamos ScrapeError para que o frontend mostre o
        # caminho de "input manual de aluguel" — comportamento documentado no plano.
        try:
            from app.services.scrapers.quintoandar import QuintoAndarScraper
            from app.services.scrapers.zap_imoveis import ZapImoveisScraper

            for scraper_cls in (QuintoAndarScraper, ZapImoveisScraper):
                try:
                    scraper = scraper_cls()
                    listings.extend(scraper.search(filters, max_results=50))
                except Exception as exc:
                    logger.warning("%s falhou: %s", scraper_cls.__name__, exc)
        except ImportError:
            pass

        if len(listings) < MIN_LISTINGS:
            raise ScrapeError(
                "Dados de aluguel indisponíveis no momento. "
                "Você pode informar o aluguel manualmente para prosseguir."
            )

        return ScrapeResult(
            stats=self._compute_stats(listings),
            listings=listings,
        )

    @staticmethod
    def _compute_stats(listings: list[Listing]) -> RentalStats:
        prices = [l.price for l in listings]
        per_m2 = [l.price_per_m2 for l in listings if l.area_m2 > 0]
        sorted_prices = sorted(prices)
        n = len(prices)
        mean = sum(prices, Decimal(0)) / Decimal(n)
        median = Decimal(str(statistics.median(prices)))
        p25 = Decimal(str(statistics.quantiles(prices, n=4)[0])) if n >= 4 else sorted_prices[0]
        p75 = Decimal(str(statistics.quantiles(prices, n=4)[2])) if n >= 4 else sorted_prices[-1]
        mean_per_m2 = sum(per_m2, Decimal(0)) / Decimal(len(per_m2)) if per_m2 else Decimal(0)
        median_per_m2 = Decimal(str(statistics.median(per_m2))) if per_m2 else Decimal(0)

        by_source: dict[str, int] = {}
        for l in listings:
            by_source[l.source] = by_source.get(l.source, 0) + 1

        return RentalStats(
            n=n,
            mean=mean.quantize(Decimal("0.01")),
            median=median.quantize(Decimal("0.01")),
            p25=p25.quantize(Decimal("0.01")),
            p75=p75.quantize(Decimal("0.01")),
            mean_per_m2=mean_per_m2.quantize(Decimal("0.01")),
            median_per_m2=median_per_m2.quantize(Decimal("0.01")),
            by_source=by_source,
            stale=False,
            fetched_at=datetime.now(timezone.utc),
        )
