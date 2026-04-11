from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from backend.app.domain.exceptions import UnsupportedTrackTypeError


class TrackType(str, Enum):
    FIXED_NON_LINKED = "fixed_non_linked"
    FIXED_LINKED = "fixed_linked"
    PRIME_FLOATING = "prime_floating"
    ADJUSTABLE_NON_LINKED = "adjustable_non_linked"
    ADJUSTABLE_LINKED = "adjustable_linked"

    @classmethod
    def from_raw(cls, raw_value: str) -> "TrackType":
        normalized = (raw_value or "").strip().lower().replace("-", "_").replace("/", "_").replace(" ", "_")
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        aliases = {
            "fixed_non_linked": cls.FIXED_NON_LINKED,
            "fixed_nonlinked": cls.FIXED_NON_LINKED,
            "fixed_nolinked": cls.FIXED_NON_LINKED,
            "fixed_linked": cls.FIXED_LINKED,
            "prime": cls.PRIME_FLOATING,
            "prime_floating": cls.PRIME_FLOATING,
            "floating": cls.PRIME_FLOATING,
            "adjustable_non_linked": cls.ADJUSTABLE_NON_LINKED,
            "adjustable_nonlinked": cls.ADJUSTABLE_NON_LINKED,
            "adjustable_linked": cls.ADJUSTABLE_LINKED,
        }
        track_type = aliases.get(normalized)
        if track_type is None:
            raise UnsupportedTrackTypeError(f"Unsupported track type: {raw_value}")
        return track_type


@dataclass(frozen=True)
class MarketContext:
    boi_base_rate: Decimal | None = None
    current_cpi: Decimal | None = None
    as_of: date | None = None


@dataclass(frozen=True)
class MortgageTrack:
    label: str
    track_type: TrackType
    outstanding_balance: Decimal
    current_rate: Decimal | None
    remaining_term_months: int
    linkage_type: str | None = None
    rate_type: str | None = None
    reset_interval: str | None = None
    next_reset_date: date | None = None
    amortization_method: str | None = None
    prepayment_penalty_rule: str | None = None
    original_cpi: Decimal | None = None
    bank_margin: Decimal | None = None


@dataclass(frozen=True)
class TrackCalculationResult:
    label: str
    track_type: TrackType
    monthly_payment: Decimal
    outstanding_balance: Decimal
    adjusted_balance: Decimal | None
    effective_annual_rate: Decimal
    monthly_rate: Decimal
    prepayment_penalty_applies: bool
    linkage_type: str | None = None
    rate_type: str | None = None
    reset_interval: str | None = None
    next_reset_date: date | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MortgageCalculationSummary:
    total_monthly_payment: Decimal
    total_outstanding_balance: Decimal
    total_adjusted_balance: Decimal
    track_results: list[TrackCalculationResult]
    assumptions: dict[str, Any] = field(default_factory=dict)
