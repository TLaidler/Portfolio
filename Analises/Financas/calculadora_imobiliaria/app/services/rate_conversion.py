from __future__ import annotations

from decimal import Decimal, getcontext
from typing import Literal

getcontext().prec = 28


RateConvention = Literal["equivalent", "nominal"]


def annual_to_monthly(annual_rate: Decimal, convention: RateConvention = "equivalent") -> Decimal:
    """Converte taxa anual para taxa mensal.

    - 'equivalent' (default, academicamente correto):
        i_m = (1 + i_a)^(1/12) - 1
      Preserva a invariância (1+i_m)^12 = 1+i_a.

    - 'nominal' (proporcional, usado em alguns contratos CEF):
        i_m = i_a / 12
    """
    if convention == "nominal":
        return annual_rate / Decimal(12)

    one = Decimal(1)
    base = one + annual_rate
    if base <= 0:
        raise ValueError("Taxa anual implicaria base não-positiva para a raiz duodécima.")
    exponent = Decimal(1) / Decimal(12)
    return _power(base, exponent) - one


def monthly_to_annual(monthly_rate: Decimal, convention: RateConvention = "equivalent") -> Decimal:
    """Converte taxa mensal para anual."""
    if convention == "nominal":
        return monthly_rate * Decimal(12)
    one = Decimal(1)
    return _power(one + monthly_rate, Decimal(12)) - one


def _power(base: Decimal, exponent: Decimal) -> Decimal:
    """Decimal ** Decimal (não-inteiro). Usa ln/exp para precisão."""
    if exponent == int(exponent):
        return base ** int(exponent)
    return (exponent * base.ln()).exp()
