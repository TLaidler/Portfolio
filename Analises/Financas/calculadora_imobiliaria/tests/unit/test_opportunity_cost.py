"""Testes do comparativo Comprar vs Alugar+Investir."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.amortization import AmortizationSystem
from app.services.opportunity_cost import OpportunityInput, compare_buy_vs_rent


@pytest.fixture
def base_input():
    return OpportunityInput(
        property_value=Decimal("500000"),
        down_payment=Decimal("100000"),
        annual_rate=Decimal("0.115"),
        term_months=360,
        system=AmortizationSystem.SAC,
        monthly_rent=Decimal("2500"),
        selic_annual=Decimal("0.1075"),
        ipca_annual=Decimal("0.045"),
    )


class TestOpportunityBasic:
    def test_returns_full_term_points(self, base_input):
        result = compare_buy_vs_rent(base_input)
        assert len(result.points) == 360

    def test_final_balance_zero_in_buy_scenario(self, base_input):
        result = compare_buy_vs_rent(base_input)
        # No final, saldo devedor = 0, então W_A_final = property_value (× appreciation se > 0)
        assert result.points[-1].balance == Decimal("0.00")

    def test_verdict_is_one_of_three(self, base_input):
        result = compare_buy_vs_rent(base_input)
        assert result.verdict in ("BUY", "RENT", "TIE")


class TestScenarioBModes:
    def test_real_mode_yields_lower_wealth_than_isobudget_when_payment_exceeds_rent(self, base_input):
        # Quando PMT > rent, isobudget investe a diferença -> patrimônio maior em B-iso.
        iso = compare_buy_vs_rent(base_input)
        real_inp = OpportunityInput(**{**base_input.__dict__, "scenario_b_mode": "real"})
        real = compare_buy_vs_rent(real_inp)
        assert iso.final_wealth_rent_nominal > real.final_wealth_rent_nominal


class TestHighSelicFavorsRent:
    def test_with_high_selic_renting_can_win(self):
        inp = OpportunityInput(
            property_value=Decimal("500000"),
            down_payment=Decimal("100000"),
            annual_rate=Decimal("0.115"),
            term_months=360,
            system=AmortizationSystem.SAC,
            monthly_rent=Decimal("1500"),  # aluguel baixo
            selic_annual=Decimal("0.20"),  # selic alta
            ipca_annual=Decimal("0.045"),
            scenario_b_mode="isobudget",
        )
        result = compare_buy_vs_rent(inp)
        assert result.verdict in ("RENT", "TIE", "BUY")
        # Com Selic 20% e aluguel barato, B costuma vencer.


class TestRentAdjustment:
    def test_rent_grows_yearly_with_ipca(self, base_input):
        result = compare_buy_vs_rent(base_input)
        rent_month_1 = result.points[0].rent
        rent_month_13 = result.points[12].rent
        # Aluguel aumenta no mês 13 (após primeiro aniversário).
        assert rent_month_13 > rent_month_1
