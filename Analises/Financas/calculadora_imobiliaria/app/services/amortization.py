"""Tabelas de amortização SAC e PRICE.

Referências:
- Hazzan, S. & Pompeo, J. N. *Matemática Financeira*. 6ª ed., cap. 6.
- Banco Central do Brasil — Caderno de Educação Financeira.

Princípios:
- Operações monetárias usam `Decimal` com `ROUND_HALF_EVEN` (banker's rounding).
- Conversão de taxa anual para mensal usa equivalência composta por padrão
  (preserva (1+i_m)^12 = 1+i_a). Flag `nominal` reproduz contratos CEF.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import Enum
from typing import Literal

from app.services.rate_conversion import RateConvention, annual_to_monthly
from app.utils.errors import InvalidLoanParametersError

CENT = Decimal("0.01")


class AmortizationSystem(str, Enum):
    SAC = "SAC"
    PRICE = "PRICE"


@dataclass(frozen=True)
class Installment:
    month: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal


@dataclass(frozen=True)
class AmortizationSchedule:
    system: AmortizationSystem
    property_value: Decimal
    down_payment: Decimal
    financed_amount: Decimal
    annual_rate: Decimal
    monthly_rate: Decimal
    term_months: int
    installments: tuple[Installment, ...]
    total_paid: Decimal
    total_interest: Decimal
    first_payment: Decimal
    last_payment: Decimal


def _q(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


def _validate_inputs(
    property_value: Decimal,
    down_payment: Decimal,
    annual_rate: Decimal,
    term_months: int,
) -> None:
    if property_value <= 0:
        raise InvalidLoanParametersError("Valor do imóvel deve ser positivo.")
    if down_payment < 0:
        raise InvalidLoanParametersError("Entrada não pode ser negativa.")
    if down_payment >= property_value:
        raise InvalidLoanParametersError("Entrada deve ser menor que o valor do imóvel.")
    if annual_rate <= 0:
        raise InvalidLoanParametersError("Taxa anual deve ser positiva.")
    if term_months <= 0:
        raise InvalidLoanParametersError("Prazo deve ser positivo.")


def _price_schedule(
    pv: Decimal, monthly_rate: Decimal, n: int
) -> tuple[list[Installment], Decimal]:
    """Tabela PRICE: parcela constante PMT = PV * i*(1+i)^n / ((1+i)^n - 1)."""
    one_plus_i = Decimal(1) + monthly_rate
    factor = one_plus_i ** n
    pmt_raw = pv * monthly_rate * factor / (factor - Decimal(1))
    pmt = _q(pmt_raw)

    installments: list[Installment] = []
    balance = pv
    total_paid = Decimal(0)

    for k in range(1, n + 1):
        if k < n:
            interest_raw = balance * monthly_rate
            interest = _q(interest_raw)
            principal = _q(pmt - interest)
            new_balance = _q(balance - principal)
            payment = pmt
        else:
            # Última parcela ajusta resíduo para zerar saldo exatamente.
            interest = _q(balance * monthly_rate)
            principal = _q(balance)
            payment = _q(interest + principal)
            new_balance = Decimal("0.00")

        installments.append(
            Installment(month=k, payment=payment, interest=interest,
                        principal=principal, balance=new_balance)
        )
        total_paid += payment
        balance = new_balance

    return installments, total_paid


def _sac_schedule(
    pv: Decimal, monthly_rate: Decimal, n: int
) -> tuple[list[Installment], Decimal]:
    """Tabela SAC: amortização constante A = PV/n."""
    amortization_raw = pv / Decimal(n)
    installments: list[Installment] = []
    balance = pv
    total_paid = Decimal(0)
    cumulative_principal = Decimal(0)

    for k in range(1, n + 1):
        interest = _q(balance * monthly_rate)
        if k < n:
            principal = _q(amortization_raw)
            cumulative_principal += principal
            new_balance = _q(pv - cumulative_principal)
        else:
            principal = _q(balance)
            new_balance = Decimal("0.00")

        payment = _q(principal + interest)
        installments.append(
            Installment(month=k, payment=payment, interest=interest,
                        principal=principal, balance=new_balance)
        )
        total_paid += payment
        balance = new_balance

    return installments, total_paid


def build_schedule(
    property_value: Decimal | float | int | str,
    down_payment: Decimal | float | int | str,
    annual_rate: Decimal | float | int | str,
    term_months: int,
    system: AmortizationSystem | str,
    rate_convention: RateConvention = "equivalent",
) -> AmortizationSchedule:
    """Constrói tabela completa de amortização.

    Args:
        property_value: valor total do imóvel (R$).
        down_payment: valor de entrada (R$).
        annual_rate: taxa de juros anual em fração (0.115 = 11,5% a.a.).
        term_months: prazo em meses.
        system: 'SAC' ou 'PRICE'.
        rate_convention: 'equivalent' (default, correto) ou 'nominal' (CEF).
    """
    pv_total = Decimal(str(property_value))
    down = Decimal(str(down_payment))
    rate = Decimal(str(annual_rate))
    sys_enum = AmortizationSystem(system if isinstance(system, str) else system.value)

    _validate_inputs(pv_total, down, rate, term_months)
    financed = pv_total - down
    monthly_rate = annual_to_monthly(rate, convention=rate_convention)

    if sys_enum == AmortizationSystem.PRICE:
        installments, total_paid = _price_schedule(financed, monthly_rate, term_months)
    else:
        installments, total_paid = _sac_schedule(financed, monthly_rate, term_months)

    total_paid_q = _q(total_paid)
    total_interest = _q(total_paid_q - financed)

    return AmortizationSchedule(
        system=sys_enum,
        property_value=_q(pv_total),
        down_payment=_q(down),
        financed_amount=_q(financed),
        annual_rate=rate,
        monthly_rate=monthly_rate,
        term_months=term_months,
        installments=tuple(installments),
        total_paid=total_paid_q,
        total_interest=total_interest,
        first_payment=installments[0].payment,
        last_payment=installments[-1].payment,
    )
