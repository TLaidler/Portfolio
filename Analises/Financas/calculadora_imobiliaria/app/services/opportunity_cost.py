"""Análise de custo de oportunidade: comprar (financiar) vs alugar+investir.

Modelos:

A) **Cenário A — Comprar:** desembolso inicial = entrada D; pagamento mensal = parcela do
   financiamento; patrimônio em mês k:
       W_A(k) = V_0·(1+g)^(k/12) − SD_k
   onde V_0 é o valor do imóvel hoje, g é a valorização anual, SD_k é o saldo devedor.

B-iso) **Cenário B-isobudget:** mesmo orçamento mensal nos dois cenários. Quando parcela > aluguel,
   investe a diferença Δ_k = PMT_k − R_k na Selic. Quando parcela < aluguel, déficit
   (saca do investimento). Patrimônio:
       W_B^iso(k) = D·(1+i_S)^k + Σⱼ Δⱼ·(1+i_S)^(k−j)

B-real) **Cenário B-real:** investe apenas D; desembolsa apenas o aluguel; diferença é consumo.
       W_B^real(k) = D·(1+i_S)^k

Break-even: menor k* tal que W_A(k*) ≥ W_B(k*).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.services.amortization import AmortizationSystem, build_schedule
from app.services.inflation import real_value
from app.services.rate_conversion import annual_to_monthly

ScenarioBMode = Literal["isobudget", "real"]


@dataclass(frozen=True)
class OpportunityInput:
    property_value: Decimal
    down_payment: Decimal
    annual_rate: Decimal
    term_months: int
    system: AmortizationSystem
    monthly_rent: Decimal
    selic_annual: Decimal
    ipca_annual: Decimal
    property_appreciation_annual: Decimal = Decimal(0)
    rent_adjustment_annual: Decimal | None = None  # None = usa ipca_annual
    scenario_b_mode: ScenarioBMode = "isobudget"
    rate_convention: Literal["equivalent", "nominal"] = "equivalent"


@dataclass(frozen=True)
class OpportunityPoint:
    month: int
    wealth_buy_nominal: Decimal
    wealth_rent_nominal: Decimal
    wealth_buy_real: Decimal
    wealth_rent_real: Decimal
    payment: Decimal
    rent: Decimal
    balance: Decimal
    property_value: Decimal


@dataclass(frozen=True)
class OpportunityResult:
    points: tuple[OpportunityPoint, ...]
    breakeven_month: int | None
    down_payment_payback_month: int | None
    final_wealth_buy_nominal: Decimal
    final_wealth_rent_nominal: Decimal
    final_wealth_buy_real: Decimal
    final_wealth_rent_real: Decimal
    verdict: Literal["BUY", "RENT", "TIE"]
    scenario_b_mode: ScenarioBMode
    schedule_first_payment: Decimal
    avg_rent: Decimal


def compare_buy_vs_rent(inp: OpportunityInput) -> OpportunityResult:
    schedule = build_schedule(
        property_value=inp.property_value,
        down_payment=inp.down_payment,
        annual_rate=inp.annual_rate,
        term_months=inp.term_months,
        system=inp.system,
        rate_convention=inp.rate_convention,
    )

    selic_monthly = annual_to_monthly(inp.selic_annual, convention="equivalent")
    g_monthly = annual_to_monthly(inp.property_appreciation_annual, convention="equivalent") \
        if inp.property_appreciation_annual != 0 else Decimal(0)
    rent_adj_annual = inp.rent_adjustment_annual if inp.rent_adjustment_annual is not None else inp.ipca_annual

    points: list[OpportunityPoint] = []
    investment_balance = inp.down_payment
    rent_total = Decimal(0)
    breakeven_month: int | None = None
    payback_month: int | None = None
    cum_spread_capitalized = Decimal(0)

    for inst in schedule.installments:
        k = inst.month

        # Aluguel ajustado anualmente por IPCA (ou índice escolhido).
        years_elapsed = (k - 1) // 12
        rent_k = inp.monthly_rent * ((Decimal(1) + rent_adj_annual) ** Decimal(years_elapsed))
        rent_total += rent_k

        # Cenário A: valor do imóvel valorizado − saldo devedor
        property_value_k = inp.property_value * ((Decimal(1) + g_monthly) ** k) if g_monthly else inp.property_value
        wealth_buy_nom = property_value_k - inst.balance

        # Cenário B
        if inp.scenario_b_mode == "isobudget":
            delta = inst.payment - rent_k
            investment_balance = investment_balance * (Decimal(1) + selic_monthly) + delta
            wealth_rent_nom = investment_balance
        else:  # real
            investment_balance = investment_balance * (Decimal(1) + selic_monthly)
            wealth_rent_nom = investment_balance

        # Valores reais (deflator IPCA)
        wealth_buy_real = real_value(wealth_buy_nom, inp.ipca_annual, k)
        wealth_rent_real = real_value(wealth_rent_nom, inp.ipca_annual, k)

        if breakeven_month is None and wealth_buy_nom >= wealth_rent_nom:
            breakeven_month = k

        # Payback da entrada via spread (aluguel evitado − juros do mês)
        if payback_month is None:
            spread_k = rent_k - inst.interest
            cum_spread_capitalized = cum_spread_capitalized * (Decimal(1) + selic_monthly) + spread_k
            if cum_spread_capitalized >= inp.down_payment:
                payback_month = k

        points.append(OpportunityPoint(
            month=k,
            wealth_buy_nominal=wealth_buy_nom.quantize(Decimal("0.01")),
            wealth_rent_nominal=wealth_rent_nom.quantize(Decimal("0.01")),
            wealth_buy_real=wealth_buy_real.quantize(Decimal("0.01")),
            wealth_rent_real=wealth_rent_real.quantize(Decimal("0.01")),
            payment=inst.payment,
            rent=rent_k.quantize(Decimal("0.01")),
            balance=inst.balance,
            property_value=property_value_k.quantize(Decimal("0.01")),
        ))

    final = points[-1]
    diff = final.wealth_buy_nominal - final.wealth_rent_nominal
    threshold = max(final.wealth_buy_nominal, final.wealth_rent_nominal) * Decimal("0.02")
    if abs(diff) <= threshold:
        verdict = "TIE"
    elif diff > 0:
        verdict = "BUY"
    else:
        verdict = "RENT"

    avg_rent = (rent_total / Decimal(len(points))).quantize(Decimal("0.01"))

    return OpportunityResult(
        points=tuple(points),
        breakeven_month=breakeven_month,
        down_payment_payback_month=payback_month,
        final_wealth_buy_nominal=final.wealth_buy_nominal,
        final_wealth_rent_nominal=final.wealth_rent_nominal,
        final_wealth_buy_real=final.wealth_buy_real,
        final_wealth_rent_real=final.wealth_rent_real,
        verdict=verdict,
        scenario_b_mode=inp.scenario_b_mode,
        schedule_first_payment=schedule.first_payment,
        avg_rent=avg_rent,
    )
