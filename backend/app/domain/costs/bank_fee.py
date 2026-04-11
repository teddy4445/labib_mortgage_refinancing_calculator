from __future__ import annotations

from decimal import Decimal

from backend.app.domain.costs.models import CostComponent
from backend.app.domain.exceptions import ValidationError


def calculate_bank_fee(
    *,
    user_quote: Decimal | None,
    default_amount: Decimal,
    allocation_ratio: Decimal = Decimal("1"),
) -> CostComponent:
    if default_amount < 0:
        raise ValidationError("Bank-fee default amount cannot be negative.")
    if allocation_ratio <= 0:
        raise ValidationError("Bank-fee allocation ratio must be greater than zero.")
    if user_quote is not None and user_quote < 0:
        raise ValidationError("Bank-fee override cannot be negative.")

    base_amount = user_quote if user_quote is not None and user_quote > 0 else default_amount
    source = "user_override" if user_quote is not None and user_quote > 0 else "default_estimate"
    return CostComponent(
        amount=base_amount * allocation_ratio,
        source=source,
        included=(base_amount * allocation_ratio) > 0,
        metadata={
            "base_amount": str(base_amount),
            "allocation_ratio": str(allocation_ratio),
        },
    )
