"""Cliente para a API SGS do Banco Central do Brasil.

Documentação: https://dadosabertos.bcb.gov.br/dataset/sgs-sistema-gerenciador-de-series-temporais
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import requests

from app.utils.cache import JSONFileCache
from app.utils.errors import BacenUnavailableError

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

SELIC_ANNUAL_CODE = 1178   # Selic anualizada (% a.a.)
CDI_DAILY_CODE = 12         # CDI diário (% a.d.)
IPCA_MONTHLY_CODE = 433     # IPCA mensal (variação % no mês)
IPCA_12M_CODE = 13522       # IPCA acumulado em 12 meses


class BacenClient:
    def __init__(
        self,
        cache_path: Path | str,
        cache_ttl: int = 86400,
        defaults: dict[str, Decimal] | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.cache = JSONFileCache(Path(cache_path), default_ttl=cache_ttl)
        self.timeout = timeout
        self.defaults = defaults or {}

    def _fetch_series(self, code: int, days_back: int = 30) -> list[dict[str, Any]]:
        """Busca série SGS dos últimos N dias."""
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=days_back)
        url = BASE_URL.format(code=code)
        params = {
            "formato": "json",
            "dataInicial": start.strftime("%d/%m/%Y"),
            "dataFinal": end.strftime("%d/%m/%Y"),
        }
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _get_latest_value(
        self,
        code: int,
        cache_key: str,
        default_key: str,
        as_fraction: bool = True,
    ) -> tuple[Decimal, bool, str | None]:
        """Retorna (valor, is_stale, fetched_at_iso). Em falha, usa cache expirado ou default."""
        cached, is_stale = self.cache.get(cache_key)
        if cached and not is_stale:
            return Decimal(cached["value"]), False, cached.get("fetched_at")

        try:
            series = self._fetch_series(code)
            if not series:
                raise ValueError("Série vazia")
            latest = series[-1]
            raw_value = Decimal(str(latest["valor"]))
            value = raw_value / Decimal(100) if as_fraction else raw_value
            now_iso = datetime.now(timezone.utc).isoformat()
            self.cache.set(
                cache_key,
                {"value": str(value), "fetched_at": now_iso, "raw_date": latest.get("data")},
            )
            return value, False, now_iso
        except (requests.RequestException, ValueError, KeyError) as exc:
            logger.warning("BACEN fetch falhou para code=%s: %s", code, exc)
            if cached:
                return Decimal(cached["value"]), True, cached.get("fetched_at")
            default = self.defaults.get(default_key)
            if default is not None:
                return Decimal(str(default)), True, None
            raise BacenUnavailableError(
                f"BACEN inacessível e sem cache nem default para {cache_key}"
            ) from exc

    def get_latest_selic_annual(self) -> tuple[Decimal, bool, str | None]:
        return self._get_latest_value(SELIC_ANNUAL_CODE, "selic_annual", "selic")

    def get_latest_cdi_annual(self) -> tuple[Decimal, bool, str | None]:
        # Código 12 retorna CDI diário; convertemos para anual via (1+i_d)^252 - 1.
        cached, is_stale = self.cache.get("cdi_annual")
        if cached and not is_stale:
            return Decimal(cached["value"]), False, cached.get("fetched_at")

        try:
            series = self._fetch_series(CDI_DAILY_CODE)
            if not series:
                raise ValueError("Série CDI vazia")
            daily = Decimal(str(series[-1]["valor"])) / Decimal(100)
            annual = ((Decimal(1) + daily) ** 252) - Decimal(1)
            now_iso = datetime.now(timezone.utc).isoformat()
            self.cache.set("cdi_annual", {"value": str(annual), "fetched_at": now_iso})
            return annual, False, now_iso
        except (requests.RequestException, ValueError, KeyError) as exc:
            logger.warning("CDI fetch falhou: %s", exc)
            if cached:
                return Decimal(cached["value"]), True, cached.get("fetched_at")
            default = self.defaults.get("cdi")
            if default is not None:
                return Decimal(str(default)), True, None
            raise BacenUnavailableError("CDI indisponível") from exc

    def get_latest_ipca_12m(self) -> tuple[Decimal, bool, str | None]:
        return self._get_latest_value(IPCA_12M_CODE, "ipca_12m", "ipca")
