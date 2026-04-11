from __future__ import annotations

from decimal import Decimal

from backend.app.domain.analysis.breakeven import BreakEvenAnalysis
from backend.app.domain.analysis.npv import NpvAnalysis
from backend.app.domain.models import MarketContext, MortgageCalculationSummary, MortgageTrack, TrackType
from backend.app.domain.scenarios.models import CostComponent, RefinanceCostBreakdown, ScenarioEvaluation, ScenarioType


def zero_refinance_cost_breakdown() -> RefinanceCostBreakdown:
    zero = Decimal("0")
    return RefinanceCostBreakdown(
        advisor_fee=CostComponent(amount=zero, source="not_applicable", included=False),
        bank_fee=CostComponent(amount=zero, source="not_applicable", included=False),
        appraisal_fee=CostComponent(amount=zero, source="not_applicable", included=False),
        legacy_other_costs=CostComponent(amount=zero, source="not_applicable", included=False),
        prepayment_penalty_total=zero,
        total_refinance_cost=zero,
        source="status_quo",
    )


def build_replacement_track(
    *,
    balance: Decimal,
    offer_rate: Decimal,
    offer_term_months: int,
    track_type: TrackType,
    label: str,
    bank_margin: Decimal | None = None,
    original_cpi: Decimal | None = None,
    linkage_type: str | None = None,
    rate_type: str | None = None,
    reset_interval: str | None = None,
    next_reset_date=None,
) -> MortgageTrack:
    return MortgageTrack(
        label=label,
        track_type=track_type,
        outstanding_balance=balance,
        current_rate=offer_rate,
        remaining_term_months=offer_term_months,
        linkage_type=linkage_type,
        rate_type=rate_type,
        reset_interval=reset_interval,
        next_reset_date=next_reset_date,
        original_cpi=original_cpi,
        bank_margin=bank_margin,
    )


def build_status_quo_scenario(
    *,
    current_summary: MortgageCalculationSummary,
    current_tracks: list[MortgageTrack],
) -> ScenarioEvaluation:
    return ScenarioEvaluation(
        id="status_quo",
        type=ScenarioType.STATUS_QUO,
        name_code="STATUS_QUO",
        description_code="KEEP_EXISTING_MORTGAGE",
        portfolio_tracks=list(current_tracks),
        refinanced_track_labels=[],
        kept_track_labels=[track.label for track in current_tracks],
        current_monthly_payment=current_summary.total_monthly_payment,
        proposed_monthly_payment=current_summary.total_monthly_payment,
        monthly_savings=Decimal("0"),
        total_outstanding_balance=current_summary.total_outstanding_balance,
        total_adjusted_balance=current_summary.total_adjusted_balance,
        refinance_costs=zero_refinance_cost_breakdown(),
        break_even=BreakEvenAnalysis(
            break_even_months=None,
            break_even_years=None,
            raw_break_even_months=None,
            monthly_savings=Decimal("0"),
            refinance_costs=Decimal("0"),
            is_viable=False,
            reason_code="STATUS_QUO",
        ),
        npv=NpvAnalysis(
            npv=Decimal("0"),
            total_present_value=Decimal("0"),
            monthly_discount_rate=Decimal("0"),
            annual_discount_rate=Decimal("0"),
            horizon_months=max(track.remaining_term_months for track in current_tracks),
            is_positive=False,
            reason_code="STATUS_QUO",
        ),
        metadata={"market_context": _context_metadata(None)},
    )


def build_full_refinance_portfolio(replacement_track: MortgageTrack) -> list[MortgageTrack]:
    return [replacement_track]


def _context_metadata(context: MarketContext | None) -> dict[str, str]:
    if context is None:
        return {}
    metadata: dict[str, str] = {}
    if context.boi_base_rate is not None:
        metadata["boi_base_rate"] = str(context.boi_base_rate)
    if context.current_cpi is not None:
        metadata["current_cpi"] = str(context.current_cpi)
    if context.as_of is not None:
        metadata["as_of"] = context.as_of.isoformat()
    return metadata
