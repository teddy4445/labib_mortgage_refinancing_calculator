from __future__ import annotations

from decimal import Decimal, localcontext

from backend.app.domain.exceptions import ValidationError


HUNDRED = Decimal("100")
TWELVE = Decimal("12")
ONE = Decimal("1")


def validate_non_negative_rate(annual_rate_percent: Decimal) -> None:
    if annual_rate_percent < 0:
        raise ValidationError("Annual interest rate cannot be negative.")


def convert_annual_to_monthly_rate(annual_rate_percent: Decimal) -> Decimal:
    validate_non_negative_rate(annual_rate_percent)
    annual_multiplier = ONE + (annual_rate_percent / HUNDRED)
    with localcontext() as ctx:
        ctx.prec = 28
        return (annual_multiplier.ln() / TWELVE).exp() - ONE

