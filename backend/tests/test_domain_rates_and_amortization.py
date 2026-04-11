from __future__ import annotations

from decimal import Decimal

import pytest

from backend.app.domain.amortization import calculate_monthly_payment
from backend.app.domain.exceptions import ValidationError
from backend.app.domain.rates import convert_annual_to_monthly_rate


def test_convert_annual_to_monthly_rate_uses_compound_conversion() -> None:
    monthly_rate = convert_annual_to_monthly_rate(Decimal("3.5"))
    assert float(monthly_rate) == pytest.approx(0.002870898719, abs=1e-12)


def test_calculate_monthly_payment_uses_compound_monthly_rate() -> None:
    payment = calculate_monthly_payment(
        principal_nis=Decimal("500000"),
        annual_rate_percent=Decimal("3.5"),
        remaining_months=240,
    )
    assert float(payment) == pytest.approx(2885.707503, abs=1e-6)
    assert int(payment.quantize(Decimal("1"))) == 2886


def test_zero_rate_payment_is_principal_divided_by_months() -> None:
    payment = calculate_monthly_payment(
        principal_nis=Decimal("120000"),
        annual_rate_percent=Decimal("0"),
        remaining_months=120,
    )
    assert payment == Decimal("1000")


@pytest.mark.parametrize(
    ("principal", "annual_rate_percent", "remaining_months"),
    [
        (Decimal("-1"), Decimal("3.5"), 240),
        (Decimal("500000"), Decimal("-0.1"), 240),
        (Decimal("500000"), Decimal("3.5"), 0),
    ],
)
def test_amortization_rejects_invalid_inputs(
    principal: Decimal,
    annual_rate_percent: Decimal,
    remaining_months: int,
) -> None:
    with pytest.raises(ValidationError):
        calculate_monthly_payment(
            principal_nis=principal,
            annual_rate_percent=annual_rate_percent,
            remaining_months=remaining_months,
        )


def test_lower_rate_does_not_increase_payment_for_same_principal_and_term() -> None:
    lower_rate_payment = calculate_monthly_payment(Decimal("500000"), Decimal("2.0"), 240)
    higher_rate_payment = calculate_monthly_payment(Decimal("500000"), Decimal("5.0"), 240)
    assert lower_rate_payment < higher_rate_payment


def test_longer_term_keeps_payment_positive() -> None:
    payment = calculate_monthly_payment(Decimal("500000"), Decimal("3.5"), 360)
    assert payment > 0

