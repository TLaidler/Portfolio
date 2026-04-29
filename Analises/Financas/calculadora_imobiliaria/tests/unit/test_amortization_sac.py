"""Testes da Tabela SAC.

Caso canônico: PV=100.000, i=1% a.m., n=120
    → A=833,33; PMT_1=1.833,33; PMT_120=841,67
    → Total juros = i·PV·(n+1)/2 = 0.01·100000·60.5 = 60.500,00
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.amortization import build_schedule


class TestSacCanonical:
    def test_canonical_120_months(self):
        schedule = build_schedule(
            property_value=Decimal("100000"),
            down_payment=Decimal("0"),
            annual_rate=Decimal("0.12"),
            term_months=120,
            system="SAC",
            rate_convention="nominal",
        )
        # Amortização constante = 100000/120 = 833.33
        first = schedule.installments[0]
        last = schedule.installments[-1]

        # PMT_1 = A + i·PV = 833,33 + 1000 = 1833,33
        assert abs(first.payment - Decimal("1833.33")) <= Decimal("0.02")
        # PMT_120 = A + i·A = 833,33 + 8,33 ≈ 841,67. A última parcela absorve
        # o resíduo de arredondamento acumulado ao longo de 119 meses (≈ R$ 0,40).
        assert abs(last.payment - Decimal("841.67")) <= Decimal("0.50")

    def test_total_interest_closed_form(self):
        # Total juros = i·PV·(n+1)/2
        schedule = build_schedule(
            property_value=Decimal("100000"),
            down_payment=Decimal("0"),
            annual_rate=Decimal("0.12"),
            term_months=120,
            system="SAC",
            rate_convention="nominal",
        )
        expected = Decimal("0.01") * Decimal("100000") * Decimal("121") / Decimal(2)
        # Tolerância R$ 0,50 cobre o resíduo de A=833,33... arredondado em 120 parcelas.
        assert abs(schedule.total_interest - expected) <= Decimal("0.50")


class TestSacProperties:
    def test_payment_decreases_monotonically(self):
        schedule = build_schedule(
            property_value=Decimal("400000"),
            down_payment=Decimal("80000"),
            annual_rate=Decimal("0.10"),
            term_months=240,
            system="SAC",
        )
        for prev, curr in zip(schedule.installments[:-2], schedule.installments[1:-1]):
            assert curr.payment <= prev.payment

    def test_principal_constant_except_last(self):
        schedule = build_schedule(
            property_value=Decimal("300000"),
            down_payment=Decimal("60000"),
            annual_rate=Decimal("0.10"),
            term_months=120,
            system="SAC",
        )
        principals = [i.principal for i in schedule.installments[:-1]]
        # Variação máxima de R$ 0,01 por arredondamento.
        assert max(principals) - min(principals) <= Decimal("0.01")

    def test_balance_zero_at_end(self):
        schedule = build_schedule(
            property_value=Decimal("400000"),
            down_payment=Decimal("100000"),
            annual_rate=Decimal("0.115"),
            term_months=360,
            system="SAC",
        )
        assert schedule.installments[-1].balance == Decimal("0.00")


class TestSacVsPrice:
    """SAC paga menos juros totais que PRICE para mesma operação."""

    def test_sac_total_interest_lower_than_price(self):
        params = dict(
            property_value=Decimal("500000"),
            down_payment=Decimal("100000"),
            annual_rate=Decimal("0.115"),
            term_months=360,
        )
        sac = build_schedule(system="SAC", **params)
        price = build_schedule(system="PRICE", **params)
        assert sac.total_interest < price.total_interest

    def test_sac_first_payment_higher_than_price(self):
        params = dict(
            property_value=Decimal("500000"),
            down_payment=Decimal("100000"),
            annual_rate=Decimal("0.115"),
            term_months=360,
        )
        sac = build_schedule(system="SAC", **params)
        price = build_schedule(system="PRICE", **params)
        assert sac.first_payment > price.first_payment

    def test_sac_last_payment_lower_than_price_constant(self):
        params = dict(
            property_value=Decimal("500000"),
            down_payment=Decimal("100000"),
            annual_rate=Decimal("0.115"),
            term_months=360,
        )
        sac = build_schedule(system="SAC", **params)
        price = build_schedule(system="PRICE", **params)
        assert sac.last_payment < price.first_payment
