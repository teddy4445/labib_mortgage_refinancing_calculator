from __future__ import annotations

from decimal import Decimal

from backend.app.domain.amortization import calculate_monthly_payment
from backend.app.domain.exceptions import MissingFieldError
from backend.app.domain.models import MarketContext, MortgageTrack, TrackCalculationResult
from backend.app.domain.rates import convert_annual_to_monthly_rate


def calculate_fixed_non_linked(track: MortgageTrack, context: MarketContext) -> TrackCalculationResult:
    del context
    if track.current_rate is None:
        raise MissingFieldError("current_rate is required for fixed non-linked tracks.")

    monthly_payment = calculate_monthly_payment(
        principal_nis=track.outstanding_balance,
        annual_rate_percent=track.current_rate,
        remaining_months=track.remaining_term_months,
    )
    return TrackCalculationResult(
        label=track.label,
        track_type=track.track_type,
        monthly_payment=monthly_payment,
        outstanding_balance=track.outstanding_balance,
        adjusted_balance=track.outstanding_balance,
        effective_annual_rate=track.current_rate,
        monthly_rate=convert_annual_to_monthly_rate(track.current_rate),
        prepayment_penalty_applies=True,
        linkage_type=track.linkage_type,
        rate_type=track.rate_type,
        reset_interval=track.reset_interval,
        next_reset_date=track.next_reset_date,
        metadata={"calculation_mode": "fixed_non_linked"},
    )


def calculate_adjustable_non_linked(track: MortgageTrack, context: MarketContext) -> TrackCalculationResult:
    result = calculate_fixed_non_linked(track, context)
    return TrackCalculationResult(
        **{
            **result.__dict__,
            "metadata": {
                **result.metadata,
                "calculation_mode": "adjustable_non_linked",
                "reset_interval": track.reset_interval,
            },
        }
    )

