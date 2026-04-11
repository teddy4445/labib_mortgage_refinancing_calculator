from __future__ import annotations

from decimal import Decimal

from backend.app.domain.amortization import calculate_monthly_payment
from backend.app.domain.exceptions import MissingFieldError, ValidationError
from backend.app.domain.models import MarketContext, MortgageTrack, TrackCalculationResult
from backend.app.domain.rates import convert_annual_to_monthly_rate


PRIME_SPREAD = Decimal("1.5")


def calculate_prime_floating(track: MortgageTrack, context: MarketContext) -> TrackCalculationResult:
    if context.boi_base_rate is None:
        raise MissingFieldError("boi_base_rate is required for prime floating tracks.")

    margin = track.bank_margin
    if margin is None:
        if track.current_rate is None:
            raise MissingFieldError("bank_margin or current_rate is required for prime floating tracks.")
        margin = track.current_rate - (context.boi_base_rate + PRIME_SPREAD)

    effective_annual_rate = context.boi_base_rate + PRIME_SPREAD + margin
    if effective_annual_rate < 0:
        raise ValidationError("Prime floating effective rate cannot be negative.")

    monthly_payment = calculate_monthly_payment(
        principal_nis=track.outstanding_balance,
        annual_rate_percent=effective_annual_rate,
        remaining_months=track.remaining_term_months,
    )
    return TrackCalculationResult(
        label=track.label,
        track_type=track.track_type,
        monthly_payment=monthly_payment,
        outstanding_balance=track.outstanding_balance,
        adjusted_balance=track.outstanding_balance,
        effective_annual_rate=effective_annual_rate,
        monthly_rate=convert_annual_to_monthly_rate(effective_annual_rate),
        prepayment_penalty_applies=False,
        linkage_type=track.linkage_type,
        rate_type=track.rate_type,
        reset_interval=track.reset_interval,
        next_reset_date=track.next_reset_date,
        metadata={
            "calculation_mode": "prime_floating",
            "boi_base_rate": str(context.boi_base_rate),
            "prime_spread": str(PRIME_SPREAD),
            "bank_margin": str(margin),
        },
    )

