from __future__ import annotations

from decimal import Decimal

from backend.app.domain.exceptions import MarketDataValidationError
from backend.app.domain.market_data.models import (
    BoiBaseRateRecord,
    CpiRecord,
    InflationExpectationRecord,
    MortgageRateBucketRecord,
)


def validate_base_rate_records(records: list[BoiBaseRateRecord]) -> None:
    if len(records) != 1:
        raise MarketDataValidationError("Base-rate snapshot must contain exactly one record.")


def validate_mortgage_rate_bucket_records(records: list[MortgageRateBucketRecord]) -> None:
    if not records:
        raise MarketDataValidationError("Mortgage-rate bucket snapshot must contain at least one record.")
    for record in records:
        if record.remaining_months_max < record.remaining_months_min:
            raise MarketDataValidationError("Mortgage-rate bucket max months must be >= min months.")


def validate_cpi_records(records: list[CpiRecord]) -> None:
    if not records:
        raise MarketDataValidationError("CPI snapshot must contain at least one record.")


def validate_inflation_expectation_records(records: list[InflationExpectationRecord]) -> None:
    if not records:
        raise MarketDataValidationError("Inflation-expectations snapshot must contain at least one record.")


def detect_single_value_jump(
    *,
    current_value: Decimal,
    previous_value: Decimal | None,
    max_allowed_delta: Decimal,
    warning_code: str,
) -> list[str]:
    if previous_value is None:
        return []
    if abs(current_value - previous_value) > max_allowed_delta:
        return [warning_code]
    return []
