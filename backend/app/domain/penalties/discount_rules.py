from __future__ import annotations

from decimal import Decimal

from backend.app.domain.exceptions import InvalidYearsSinceOriginationError


def statutory_discount_factor(years_since_origination: Decimal) -> Decimal:
    if years_since_origination < 0:
        raise InvalidYearsSinceOriginationError("Years since origination cannot be negative.")
    if years_since_origination < Decimal("3"):
        return Decimal("1.00")
    if years_since_origination < Decimal("5"):
        return Decimal("0.80")
    return Decimal("0.70")
