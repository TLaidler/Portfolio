from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal


SourceName = Literal["quintoandar", "zap"]


@dataclass(frozen=True)
class Listing:
    price: Decimal
    area_m2: float
    bedrooms: int | None
    neighborhood: str | None
    furnished: bool | None
    has_ac: bool | None
    source: SourceName
    url: str
    scraped_at: datetime

    @property
    def price_per_m2(self) -> Decimal:
        if self.area_m2 <= 0:
            return Decimal(0)
        return self.price / Decimal(str(self.area_m2))


@dataclass
class SearchFilters:
    city: str
    neighborhood: str | None = None
    area_min: float | None = None
    area_max: float | None = None
    furnished: bool | None = None
    has_ac: bool | None = None

    def cache_key_payload(self) -> dict[str, Any]:
        return {
            "city": self.city.lower().strip(),
            "neighborhood": (self.neighborhood or "").lower().strip(),
            "area_min": self.area_min,
            "area_max": self.area_max,
            "furnished": self.furnished,
            "has_ac": self.has_ac,
        }


@dataclass
class RentalStats:
    n: int
    mean: Decimal
    median: Decimal
    p25: Decimal
    p75: Decimal
    mean_per_m2: Decimal
    median_per_m2: Decimal
    by_source: dict[str, int]
    stale: bool = False
    fetched_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "mean": str(self.mean),
            "median": str(self.median),
            "p25": str(self.p25),
            "p75": str(self.p75),
            "mean_per_m2": str(self.mean_per_m2),
            "median_per_m2": str(self.median_per_m2),
            "by_source": self.by_source,
            "stale": self.stale,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }


@dataclass
class ScrapeResult:
    stats: RentalStats | None
    listings: list[Listing] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "stats": self.stats.to_dict() if self.stats else None,
            "listings": [
                {
                    "price": str(l.price),
                    "area_m2": l.area_m2,
                    "bedrooms": l.bedrooms,
                    "neighborhood": l.neighborhood,
                    "furnished": l.furnished,
                    "has_ac": l.has_ac,
                    "source": l.source,
                    "url": l.url,
                    "price_per_m2": str(l.price_per_m2),
                }
                for l in self.listings[:20]  # limita payload da API
            ],
            "error": self.error,
        }
