from __future__ import annotations

from decimal import Decimal, localcontext

from backend.app.domain.amortization import calculate_monthly_payment
from backend.app.domain.exceptions import MissingFieldError, ValidationError
from backend.app.domain.models import MarketContext, MortgageTrack, TrackCalculationResult
from backend.app.domain.rates import convert_annual_to_monthly_rate


def adjust_balance_for_cpi(outstanding_balance: Decimal, original_cpi: Decimal, current_cpi: Decimal) -> Decimal:
    if outstanding_balance <= 0:
        raise ValidationError("Outstanding balance must be greater than zero.")
    if original_cpi <= 0 or current_cpi <= 0:
        raise ValidationError("CPI values must be greater than zero.")
    with localcontext() as ctx:
        ctx.prec = 28
        return outstanding_balance * (current_cpi / original_cpi)


def calculate_fixed_linked(track: MortgageTrack, context: MarketContext) -> TrackCalculationResult:
    if track.current_rate is None:
        raise MissingFieldError("current_rate is required for CPI-linked tracks.")
    if track.original_cpi is None:
        raise MissingFieldError("original_cpi is required for CPI-linked tracks.")
    if context.current_cpi is None:
        raise MissingFieldError("current_cpi is required for CPI-linked tracks.")

    adjusted_balance = adjust_balance_for_cpi(track.outstanding_balance, track.original_cpi, context.current_cpi)
    monthly_payment = calculate_monthly_payment(
        principal_nis=adjusted_balance,
        annual_rate_percent=track.current_rate,
        remaining_months=track.remaining_term_months,
    )
    return TrackCalculationResult(
        label=track.label,
        track_type=track.track_type,
        monthly_payment=monthly_payment,
        outstanding_balance=track.outstanding_balance,
        adjusted_balance=adjusted_balance,
        effective_annual_rate=track.current_rate,
        monthly_rate=convert_annual_to_monthly_rate(track.current_rate),
        prepayment_penalty_applies=True,
        linkage_type=track.linkage_type,
        rate_type=track.rate_type,
        reset_interval=track.reset_interval,
        next_reset_date=track.next_reset_date,
        metadata={
            "calculation_mode": "fixed_linked",
            "original_cpi": str(track.original_cpi),
            "current_cpi": str(context.current_cpi),
        },
    )


def calculate_adjustable_linked(track: MortgageTrack, context: MarketContext) -> TrackCalculationResult:
    result = calculate_fixed_linked(track, context)
    return TrackCalculationResult(
        **{
            **result.__dict__,
            "metadata": {
                **result.metadata,
                "calculation_mode": "adjustable_linked",
                "reset_interval": track.reset_interval,
            },
        }
    )

