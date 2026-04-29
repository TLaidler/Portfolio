from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.amortization import AmortizationSystem
from app.services.opportunity_cost import OpportunityInput, OpportunityResult


class OpportunityRequest(BaseModel):
    property_value: Decimal = Field(..., gt=0, le=Decimal("100000000"))
    down_payment: Decimal = Field(..., ge=0)
    annual_rate: Decimal = Field(..., gt=0, lt=Decimal(1))
    term_months: int = Field(..., ge=1, le=600)
    system: Literal["SAC", "PRICE"] = "SAC"
    monthly_rent: Decimal = Field(..., gt=0)
    selic_annual: Decimal = Field(..., gt=0, lt=Decimal(1))
    ipca_annual: Decimal = Field(Decimal("0.045"), ge=Decimal("-0.2"), le=Decimal(1))
    property_appreciation_annual: Decimal = Field(
        Decimal(0), ge=Decimal("-0.5"), le=Decimal(1)
    )
    rent_adjustment_annual: Decimal | None = None
    scenario_b_mode: Literal["isobudget", "real"] = "isobudget"
    rate_convention: Literal["equivalent", "nominal"] = "equivalent"

    @field_validator(
        "property_value", "down_payment", "annual_rate", "monthly_rent",
        "selic_annual", "ipca_annual", "property_appreciation_annual",
        "rent_adjustment_annual",
        mode="before",
    )
    @classmethod
    def _coerce_decimal(cls, v):
        if v is None or v == "":
            return v
        return Decimal(str(v))

    @model_validator(mode="after")
    def _check_consistency(self) -> "OpportunityRequest":
        if self.down_payment >= self.property_value:
            raise ValueError("Entrada deve ser menor que o valor do imóvel.")
        return self

    def to_domain(self) -> OpportunityInput:
        return OpportunityInput(
            property_value=self.property_value,
            down_payment=self.down_payment,
            annual_rate=self.annual_rate,
            term_months=self.term_months,
            system=AmortizationSystem(self.system),
            monthly_rent=self.monthly_rent,
            selic_annual=self.selic_annual,
            ipca_annual=self.ipca_annual,
            property_appreciation_annual=self.property_appreciation_annual,
            rent_adjustment_annual=self.rent_adjustment_annual,
            scenario_b_mode=self.scenario_b_mode,
            rate_convention=self.rate_convention,
        )


class OpportunityPointDTO(BaseModel):
    month: int
    wealth_buy_nominal: Decimal
    wealth_rent_nominal: Decimal
    wealth_buy_real: Decimal
    wealth_rent_real: Decimal
    payment: Decimal
    rent: Decimal


class OpportunitySummary(BaseModel):
    breakeven_month: int | None
    down_payment_payback_month: int | None
    final_wealth_buy_nominal: Decimal
    final_wealth_rent_nominal: Decimal
    final_wealth_buy_real: Decimal
    final_wealth_rent_real: Decimal
    verdict: Literal["BUY", "RENT", "TIE"]
    scenario_b_mode: Literal["isobudget", "real"]
    schedule_first_payment: Decimal
    avg_rent: Decimal


class OpportunityResponse(BaseModel):
    summary: OpportunitySummary
    points: list[OpportunityPointDTO]

    @classmethod
    def from_result(
        cls,
        result: OpportunityResult,
        scenario_b_mode: Literal["isobudget", "real"],
    ) -> "OpportunityResponse":
        summary = OpportunitySummary(
            breakeven_month=result.breakeven_month,
            down_payment_payback_month=result.down_payment_payback_month,
            final_wealth_buy_nominal=result.final_wealth_buy_nominal,
            final_wealth_rent_nominal=result.final_wealth_rent_nominal,
            final_wealth_buy_real=result.final_wealth_buy_real,
            final_wealth_rent_real=result.final_wealth_rent_real,
            verdict=result.verdict,
            scenario_b_mode=scenario_b_mode,
            schedule_first_payment=result.schedule_first_payment,
            avg_rent=result.avg_rent,
        )
        points = [
            OpportunityPointDTO(
                month=p.month,
                wealth_buy_nominal=p.wealth_buy_nominal,
                wealth_rent_nominal=p.wealth_rent_nominal,
                wealth_buy_real=p.wealth_buy_real,
                wealth_rent_real=p.wealth_rent_real,
                payment=p.payment,
                rent=p.rent,
            )
            for p in result.points
        ]
        return cls(summary=summary, points=points)
