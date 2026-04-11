from __future__ import annotations

from decimal import Decimal, localcontext

from backend.app.domain.exceptions import ValidationError
from backend.app.domain.rates import ONE, convert_annual_to_monthly_rate


def calculate_monthly_payment(
    principal_nis: Decimal,
    annual_rate_percent: Decimal,
    remaining_months: int,
) -> Decimal:
    if principal_nis <= 0:
        raise ValidationError("Principal must be greater than zero.")
    if remaining_months <= 0:
        raise ValidationError("Remaining months must be greater than zero.")

    monthly_rate = convert_annual_to_monthly_rate(annual_rate_percent)
    if monthly_rate == 0:
        with localcontext() as ctx:
            ctx.prec = 28
            return principal_nis / Decimal(remaining_months)

    with localcontext() as ctx:
        ctx.prec = 28
        growth_factor = (ONE + monthly_rate) ** remaining_months
        return principal_nis * (monthly_rate * growth_factor) / (growth_factor - ONE)

