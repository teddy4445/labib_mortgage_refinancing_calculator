from __future__ import annotations

from decimal import Decimal

import pytest

from backend.app.domain.analysis.breakeven import calculate_break_even
from backend.app.domain.analysis.npv import calculate_npv
from backend.app.domain.exceptions import InvalidScenarioInputError
from backend.app.domain.rates import convert_annual_to_monthly_rate


def test_break_even_positive_savings_returns_finite_result() -> None:
    result = calculate_break_even(monthly_savings=Decimal("500"), refinance_costs=Decimal("10000"))

    assert result.is_viable is True
    assert result.break_even_months == 20
    assert result.reason_code == "BREAK_EVEN_AVAILABLE"


def test_break_even_zero_or_negative_savings_is_not_viable() -> None:
    zero_result = calculate_break_even(monthly_savings=Decimal("0"), refinance_costs=Decimal("10000"))
    negative_result = calculate_break_even(monthly_savings=Decimal("-100"), refinance_costs=Decimal("10000"))

    assert zero_result.is_viable is False
    assert zero_result.break_even_months is None
    assert negative_result.is_viable is False
    assert negative_result.reason_code == "NEGATIVE_MONTHLY_SAVINGS"


def test_npv_positive_case_uses_compound_monthly_discount_rate() -> None:
    result = calculate_npv(
        monthly_savings=Decimal("500"),
        horizon_months=120,
        refinance_costs=Decimal("10000"),
        annual_discount_rate_percent=Decimal("4.0"),
    )

    assert result.npv > 0
    assert result.total_present_value > Decimal("10000")
    assert result.monthly_discount_rate == convert_annual_to_monthly_rate(Decimal("4.0"))


def test_npv_zero_or_negative_savings_is_non_positive() -> None:
    zero_result = calculate_npv(
        monthly_savings=Decimal("0"),
        horizon_months=120,
        refinance_costs=Decimal("10000"),
        annual_discount_rate_percent=Decimal("4.0"),
    )
    negative_result = calculate_npv(
        monthly_savings=Decimal("-50"),
        horizon_months=120,
        refinance_costs=Decimal("10000"),
        annual_discount_rate_percent=Decimal("4.0"),
    )

    assert zero_result.npv <= 0
    assert negative_result.npv < 0


def test_npv_requires_positive_horizon() -> None:
    with pytest.raises(InvalidScenarioInputError):
        calculate_npv(
            monthly_savings=Decimal("500"),
            horizon_months=0,
            refinance_costs=Decimal("1000"),
            annual_discount_rate_percent=Decimal("4.0"),
        )
