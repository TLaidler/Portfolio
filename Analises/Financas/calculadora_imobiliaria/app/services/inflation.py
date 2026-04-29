from __future__ import annotations

from decimal import Decimal


def real_value(nominal: Decimal, ipca_annual: Decimal, months_elapsed: int) -> Decimal:
    """Converte valor nominal futuro para valor real em poder de compra de hoje.

    real = nominal / (1 + π)^(k/12)
    """
    if ipca_annual == 0 or months_elapsed == 0:
        return nominal
    one = Decimal(1)
    deflator = (one + ipca_annual) ** (Decimal(months_elapsed) / Decimal(12))
    return nominal / deflator
