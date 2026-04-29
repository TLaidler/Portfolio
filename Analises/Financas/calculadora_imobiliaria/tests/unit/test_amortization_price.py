"""Testes da Tabela PRICE.

Caso canônico: PV=100.000, i=1% a.m., n=120 → PMT=R$1.434,71
(Hazzan & Pompeo, 6ª ed., cap. 6).
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.amortization import (
    AmortizationSystem,
    build_schedule,
)
from app.utils.errors import InvalidLoanParametersError


class TestPriceCanonical:
    """Validação contra valores publicados na literatura."""

    def test_hazzan_pompeo_120_months(self):
        # PV=100k, i=1% a.m. (taxa nominal), n=120 -> PMT≈1434.71
        # Para casar com 1% a.m. exatamente, usamos convenção 'nominal'.
        schedule = build_schedule(
            property_value=Decimal("100000"),
            down_payment=Decimal("0"),
            annual_rate=Decimal("0.12"),  # 12% a.a. nominal -> 1% a.m.
            term_months=120,
            system=AmortizationSystem.PRICE,
            rate_convention="nominal",
        )
        assert abs(schedule.first_payment - Decimal("1434.71")) <= Decimal("0.02")
        # PRICE: todas as parcelas iguais (exceto última que pode ter centavos de ajuste).
        for inst in schedule.installments[:-1]:
            assert inst.payment == schedule.first_payment

    def test_balance_zero_at_end(self):
        schedule = build_schedule(
            property_value=Decimal("400000"),
            down_payment=Decimal("100000"),
            annual_rate=Decimal("0.115"),
            term_months=360,
            system="PRICE",
        )
        assert schedule.installments[-1].balance == Decimal("0.00")

    def test_principal_sum_equals_financed(self):
        schedule = build_schedule(
            property_value=Decimal("500000"),
            down_payment=Decimal("100000"),
            annual_rate=Decimal("0.10"),
            term_months=240,
            system="PRICE",
        )
        total_principal = sum((i.principal for i in schedule.installments), Decimal(0))
        # Tolerância de R$0,02 por arredondamento HALF_EVEN ao longo de 240 parcelas.
        assert abs(total_principal - schedule.financed_amount) <= Decimal("0.05")


class TestPriceProperties:
    """Invariantes matemáticas da Tabela PRICE."""

    def test_interest_decreases_monotonically(self):
        schedule = build_schedule(
            property_value=Decimal("300000"),
            down_payment=Decimal("60000"),
            annual_rate=Decimal("0.10"),
            term_months=180,
            system="PRICE",
        )
        for prev, curr in zip(schedule.installments, schedule.installments[1:]):
            assert curr.interest <= prev.interest

    def test_principal_increases_monotonically(self):
        schedule = build_schedule(
            property_value=Decimal("300000"),
            down_payment=Decimal("60000"),
            annual_rate=Decimal("0.10"),
            term_months=180,
            system="PRICE",
        )
        # Excluindo última parcela (pode ter ajuste de resíduo)
        for prev, curr in zip(schedule.installments[:-2], schedule.installments[1:-1]):
            assert curr.principal >= prev.principal

    def test_payment_components_sum_to_payment(self):
        schedule = build_schedule(
            property_value=Decimal("250000"),
            down_payment=Decimal("50000"),
            annual_rate=Decimal("0.09"),
            term_months=120,
            system="PRICE",
        )
        for inst in schedule.installments:
            assert inst.payment == inst.interest + inst.principal


class TestPriceValidation:
    """Validação de inputs."""

    def test_rejects_zero_property_value(self):
        with pytest.raises(InvalidLoanParametersError):
            build_schedule(0, 0, Decimal("0.1"), 360, "PRICE")

    def test_rejects_down_payment_equal_to_property(self):
        with pytest.raises(InvalidLoanParametersError):
            build_schedule(100000, 100000, Decimal("0.1"), 360, "PRICE")

    def test_rejects_zero_term(self):
        with pytest.raises(InvalidLoanParametersError):
            build_schedule(100000, 10000, Decimal("0.1"), 0, "PRICE")
