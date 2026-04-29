"""Testes da conversão de taxa anual <-> mensal.

Casos canônicos validados contra Hazzan & Pompeo, *Matemática Financeira*, 6ª ed.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.rate_conversion import annual_to_monthly, monthly_to_annual


class TestEquivalentRate:
    """Taxa equivalente (composta): (1+i_m)^12 = 1+i_a."""

    def test_one_percent_monthly_equivals_12_68_annual(self):
        # 1.01^12 = 1.1268250301... -> 12.68%
        result = monthly_to_annual(Decimal("0.01"), convention="equivalent")
        assert abs(result - Decimal("0.12682503")) < Decimal("0.0000001")

    def test_12_68_annual_equivals_1_percent_monthly(self):
        result = annual_to_monthly(Decimal("0.1268250301"), convention="equivalent")
        assert abs(result - Decimal("0.01")) < Decimal("0.0000001")

    def test_round_trip_preserves_value(self):
        for annual in ["0.06", "0.10", "0.115", "0.15", "0.20"]:
            i_a = Decimal(annual)
            i_m = annual_to_monthly(i_a, convention="equivalent")
            i_a_back = monthly_to_annual(i_m, convention="equivalent")
            assert abs(i_a - i_a_back) < Decimal("0.0000001")

    def test_zero_rate_unsupported_in_loan_context(self):
        # rate_conversion aceita valores positivos; validação de "> 0" é em amortization.
        i_m = annual_to_monthly(Decimal("0"))
        assert i_m == Decimal("0")


class TestNominalRate:
    """Taxa nominal/proporcional: i_m = i_a / 12 (usada em alguns contratos CEF)."""

    def test_12_percent_annual_nominal_is_1_percent_monthly(self):
        result = annual_to_monthly(Decimal("0.12"), convention="nominal")
        assert result == Decimal("0.01")

    def test_nominal_round_trip(self):
        i_a = Decimal("0.12")
        assert monthly_to_annual(annual_to_monthly(i_a, "nominal"), "nominal") == i_a


class TestEquivalentVsNominalDiverge:
    """A diferença entre as convenções é o ponto acadêmico-chave."""

    def test_nominal_overstates_monthly_rate(self):
        i_a = Decimal("0.12")
        i_m_nominal = annual_to_monthly(i_a, "nominal")  # 0.01
        i_m_equiv = annual_to_monthly(i_a, "equivalent")  # ~0.009488
        assert i_m_nominal > i_m_equiv
        # capitalizar nominal por 12 meses dá efetiva > 12%
        effective_from_nominal = (Decimal(1) + i_m_nominal) ** 12 - Decimal(1)
        assert effective_from_nominal > i_a
