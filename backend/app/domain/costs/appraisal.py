from __future__ import annotations

from decimal import Decimal

from backend.app.domain.costs.models import CostComponent
from backend.app.domain.exceptions import ValidationError


def calculate_appraisal_fee(
    *,
    included: bool,
    explicit_amount: Decimal | None,
    default_amount: Decimal,
    allocation_ratio: Decimal = Decimal("1"),
) -> CostComponent:
    if default_amount < 0:
        raise ValidationError("Appraisal default amount cannot be negative.")
    if allocation_ratio <= 0:
        raise ValidationError("Appraisal allocation ratio must be greater than zero.")
    if explicit_amount is not None and explicit_amount < 0:
        raise ValidationError("Appraisal override cannot be negative.")

    if not included and (explicit_amount is None or explicit_amount <= 0):
        return CostComponent(
            amount=Decimal("0"),
            source="not_applicable",
            included=False,
            metadata={"allocation_ratio": str(allocation_ratio)},
        )

    base_amount = explicit_amount if explicit_amount is not None and explicit_amount > 0 else default_amount
    source = "user_override" if explicit_amount is not None and explicit_amount > 0 else "default_estimate"
    return CostComponent(
        amount=base_amount * allocation_ratio,
        source=source,
        included=True,
        metadata={
            "base_amount": str(base_amount),
            "allocation_ratio": str(allocation_ratio),
        },
    )
