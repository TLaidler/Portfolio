from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.amortization import AmortizationSchedule, AmortizationSystem


class SimulationRequest(BaseModel):
    property_value: Decimal = Field(..., gt=0, le=Decimal("100000000"))
    down_payment: Decimal = Field(..., ge=0)
    annual_rate: Decimal = Field(..., gt=0, lt=Decimal(1))
    term_months: int | None = Field(None, ge=1, le=600)
    term_years: int | None = Field(None, ge=1, le=50)
    system: Literal["SAC", "PRICE"] = "SAC"
    rate_convention: Literal["equivalent", "nominal"] = "equivalent"
    monthly_income: Decimal = Field(..., gt=0)

    @field_validator("property_value", "down_payment", "annual_rate", "monthly_income", mode="before")
    @classmethod
    def _coerce_decimal(cls, v):
        if v is None or v == "":
            return v
        if isinstance(v, str):
            return Decimal(v.replace(".", "").replace(",", ".") if "," in v else v)
        return Decimal(str(v))

    @model_validator(mode="after")
    def _check_consistency(self) -> "SimulationRequest":
        if self.term_months is None and self.term_years is None:
            raise ValueError("Informe term_months ou term_years.")
        if self.term_months is not None and self.term_years is not None:
            raise ValueError("Informe apenas um: term_months OU term_years.")
        if self.down_payment >= self.property_value:
            raise ValueError("Entrada deve ser menor que o valor do imóvel.")
        return self

    @property
    def effective_term_months(self) -> int:
        return self.term_months if self.term_months is not None else (self.term_years * 12)


class InstallmentDTO(BaseModel):
    month: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal


class ScheduleSummary(BaseModel):
    system: str
    property_value: Decimal
    down_payment: Decimal
    financed_amount: Decimal
    annual_rate: Decimal
    monthly_rate: Decimal
    term_months: int
    first_payment: Decimal
    last_payment: Decimal
    total_paid: Decimal
    total_interest: Decimal
    income_commitment_pct: Decimal | None = None
    income_commitment_alert: bool = False


class ScheduleResponse(BaseModel):
    summary: ScheduleSummary
    installments: list[InstallmentDTO]

    @classmethod
    def from_schedule(
        cls,
        schedule: AmortizationSchedule,
        monthly_income: Decimal | None = None,
    ) -> "ScheduleResponse":
        commitment = None
        alert = False
        if monthly_income and monthly_income > 0:
            commitment = (schedule.first_payment / monthly_income).quantize(Decimal("0.0001"))
            alert = commitment > Decimal("0.30")

        summary = ScheduleSummary(
            system=schedule.system.value if isinstance(schedule.system, AmortizationSystem) else str(schedule.system),
            property_value=schedule.property_value,
            down_payment=schedule.down_payment,
            financed_amount=schedule.financed_amount,
            annual_rate=schedule.annual_rate,
            monthly_rate=schedule.monthly_rate.quantize(Decimal("0.000001")),
            term_months=schedule.term_months,
            first_payment=schedule.first_payment,
            last_payment=schedule.last_payment,
            total_paid=schedule.total_paid,
            total_interest=schedule.total_interest,
            income_commitment_pct=commitment,
            income_commitment_alert=alert,
        )
        installments = [
            InstallmentDTO(
                month=i.month,
                payment=i.payment,
                interest=i.interest,
                principal=i.principal,
                balance=i.balance,
            )
            for i in schedule.installments
        ]
        return cls(summary=summary, installments=installments)
