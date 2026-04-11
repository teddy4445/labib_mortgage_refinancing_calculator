from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext

from backend.app.domain.amortization import calculate_monthly_payment
from backend.app.domain.exceptions import PaymentStreamError, ValidationError
from backend.app.domain.rates import ONE, convert_annual_to_monthly_rate


@dataclass(frozen=True)
class PaymentStreamItem:
    month_index: int
    payment_amount: Decimal
    remaining_balance_after_payment: Decimal


def build_remaining_payment_stream(
    *,
    principal_nis: Decimal,
    annual_rate_percent: Decimal,
    remaining_months: int,
) -> list[PaymentStreamItem]:
    if principal_nis <= 0:
        raise PaymentStreamError("Principal must be greater than zero for payment-stream generation.")
    if remaining_months <= 0:
        raise PaymentStreamError("Remaining months must be greater than zero for payment-stream generation.")
    if annual_rate_percent < 0:
        raise ValidationError("Annual interest rate cannot be negative.")

    monthly_payment = calculate_monthly_payment(principal_nis, annual_rate_percent, remaining_months)
    monthly_rate = convert_annual_to_monthly_rate(annual_rate_percent)
    balance = principal_nis
    stream: list[PaymentStreamItem] = []

    with localcontext() as ctx:
        ctx.prec = 28
        for month_index in range(1, remaining_months + 1):
            interest_component = balance * monthly_rate
            principal_component = monthly_payment - interest_component
            if principal_component < 0:
                raise PaymentStreamError("Payment stream produced a negative principal component.")
            next_balance = balance - principal_component
            if month_index == remaining_months or next_balance < Decimal("0.000001"):
                next_balance = Decimal("0")
            stream.append(
                PaymentStreamItem(
                    month_index=month_index,
                    payment_amount=monthly_payment,
                    remaining_balance_after_payment=next_balance,
                )
            )
            balance = next_balance

    return stream


def present_value_of_payment_stream(
    *,
    payment_stream: list[PaymentStreamItem],
    annual_rate_percent: Decimal,
) -> Decimal:
    if not payment_stream:
        raise PaymentStreamError("Payment stream cannot be empty.")

    monthly_rate = convert_annual_to_monthly_rate(annual_rate_percent)
    if monthly_rate == 0:
        return sum(item.payment_amount for item in payment_stream)

    with localcontext() as ctx:
        ctx.prec = 28
        return sum(
            item.payment_amount / ((ONE + monthly_rate) ** item.month_index)
            for item in payment_stream
        )
