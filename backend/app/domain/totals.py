from __future__ import annotations

from decimal import Decimal, localcontext

from backend.app.domain.models import MarketContext, MortgageCalculationSummary, MortgageTrack
from backend.app.domain.tracks import calculate_track_payment


def calculate_total_monthly_payment(
    tracks: list[MortgageTrack],
    context: MarketContext,
) -> MortgageCalculationSummary:
    track_results = [calculate_track_payment(track, context) for track in tracks]
    with localcontext() as ctx:
        ctx.prec = 28
        total_monthly_payment = sum((result.monthly_payment for result in track_results), Decimal("0"))
        total_outstanding_balance = sum((track.outstanding_balance for track in tracks), Decimal("0"))
        total_adjusted_balance = sum(
            ((result.adjusted_balance if result.adjusted_balance is not None else result.outstanding_balance) for result in track_results),
            Decimal("0"),
        )

    assumptions: dict[str, str] = {}
    if context.boi_base_rate is not None:
        assumptions["boi_base_rate"] = str(context.boi_base_rate)
    if context.current_cpi is not None:
        assumptions["current_cpi"] = str(context.current_cpi)

    return MortgageCalculationSummary(
        total_monthly_payment=total_monthly_payment,
        total_outstanding_balance=total_outstanding_balance,
        total_adjusted_balance=total_adjusted_balance,
        track_results=track_results,
        assumptions=assumptions,
    )

