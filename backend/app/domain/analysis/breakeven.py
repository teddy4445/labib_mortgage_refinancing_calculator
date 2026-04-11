from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, localcontext

from backend.app.domain.exceptions import InvalidScenarioInputError


TWELVE = Decimal("12")


@dataclass(frozen=True)
class BreakEvenAnalysis:
    break_even_months: int | None
    break_even_years: Decimal | None
    raw_break_even_months: Decimal | None
    monthly_savings: Decimal
    refinance_costs: Decimal
    is_viable: bool
    reason_code: str


def calculate_break_even(
    *,
    monthly_savings: Decimal,
    refinance_costs: Decimal,
) -> BreakEvenAnalysis:
    if refinance_costs < 0:
        raise InvalidScenarioInputError("Refinance costs cannot be negative.")

    if monthly_savings < 0:
        return BreakEvenAnalysis(
            break_even_months=None,
            break_even_years=None,
            raw_break_even_months=None,
            monthly_savings=monthly_savings,
            refinance_costs=refinance_costs,
            is_viable=False,
            reason_code="NEGATIVE_MONTHLY_SAVINGS",
        )

    if monthly_savings == 0:
        return BreakEvenAnalysis(
            break_even_months=None,
            break_even_years=None,
            raw_break_even_months=None,
            monthly_savings=monthly_savings,
            refinance_costs=refinance_costs,
            is_viable=False,
            reason_code="ZERO_MONTHLY_SAVINGS",
        )

    with localcontext() as ctx:
        ctx.prec = 28
        raw_break_even_months = refinance_costs / monthly_savings if refinance_costs > 0 else Decimal("0")
        break_even_months = int(raw_break_even_months.to_integral_value(rounding=ROUND_CEILING))
        break_even_years = raw_break_even_months / TWELVE

    return BreakEvenAnalysis(
        break_even_months=break_even_months,
        break_even_years=break_even_years,
        raw_break_even_months=raw_break_even_months,
        monthly_savings=monthly_savings,
        refinance_costs=refinance_costs,
        is_viable=True,
        reason_code="BREAK_EVEN_AVAILABLE",
    )
