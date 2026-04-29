from __future__ import annotations

from decimal import Decimal

from flask import Flask


def format_brl(value: Decimal | float | int | None, decimals: int = 2) -> str:
    """Formata valor como moeda brasileira: 1234567.89 -> 'R$ 1.234.567,89'."""
    if value is None:
        return "—"
    v = Decimal(str(value)).quantize(Decimal(10) ** -decimals)
    sign = "-" if v < 0 else ""
    v = abs(v)
    int_part, _, frac_part = f"{v:.{decimals}f}".partition(".")
    int_with_sep = ".".join(
        [int_part[max(0, i - 3):i] for i in range(len(int_part), 0, -3)][::-1]
    )
    return f"{sign}R$ {int_with_sep},{frac_part}" if decimals else f"{sign}R$ {int_with_sep}"


def format_percent(value: Decimal | float | None, decimals: int = 2) -> str:
    """Formata fração como percentual: 0.1075 -> '10,75%'."""
    if value is None:
        return "—"
    v = Decimal(str(value)) * 100
    formatted = f"{v:.{decimals}f}".replace(".", ",")
    return f"{formatted}%"


def format_months(value: int | None) -> str:
    """Formata duração em meses: 360 -> '30 anos' / 18 -> '1 ano e 6 meses'."""
    if value is None:
        return "—"
    if value <= 0:
        return "0 meses"
    years, months = divmod(value, 12)
    parts = []
    if years:
        parts.append(f"{years} ano" + ("s" if years != 1 else ""))
    if months:
        parts.append(f"{months} {'mês' if months == 1 else 'meses'}")
    return " e ".join(parts) if parts else "0 meses"


def register_filters(app: Flask) -> None:
    app.jinja_env.filters["brl"] = format_brl
    app.jinja_env.filters["percent"] = format_percent
    app.jinja_env.filters["months"] = format_months
