from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext

from backend.app.domain.exceptions import InvalidScenarioInputError
from backend.app.domain.rates import convert_annual_to_monthly_rate


@dataclass(frozen=True)
class NpvAnalysis:
    npv: Decimal
    total_present_value: Decimal
    monthly_discount_rate: Decimal
    annual_discount_rate: Decimal
    horizon_months: int
    is_positive: bool
    reason_code: str


def calculate_npv(
    *,
    monthly_savings: Decimal,
    horizon_months: int,
    refinance_costs: Decimal,
    annual_discount_rate_percent: Decimal,
) -> NpvAnalysis:
    if horizon_months <= 0:
        raise InvalidScenarioInputError("NPV horizon_months must be positive.")
    if refinance_costs < 0:
        raise InvalidScenarioInputError("Refinance costs cannot be negative.")
    if annual_discount_rate_percent < 0:
        raise InvalidScenarioInputError("Annual discount rate cannot be negative.")

    monthly_discount_rate = convert_annual_to_monthly_rate(annual_discount_rate_percent)
    with localcontext() as ctx:
        ctx.prec = 28
        if monthly_discount_rate == 0:
            total_present_value = monthly_savings * Decimal(horizon_months)
        else:
            total_present_value = Decimal("0")
            denominator_base = Decimal("1") + monthly_discount_rate
            for month in range(1, horizon_months + 1):
                total_present_value += monthly_savings / (denominator_base**month)
        npv = total_present_value - refinance_costs

    return NpvAnalysis(
        npv=npv,
        total_present_value=total_present_value,
        monthly_discount_rate=monthly_discount_rate,
        annual_discount_rate=annual_discount_rate_percent,
        horizon_months=horizon_months,
        is_positive=npv > 0,
        reason_code="POSITIVE_NPV" if npv > 0 else "NON_POSITIVE_NPV",
    )
