from __future__ import annotations

from decimal import Decimal

from backend.app.domain.analysis.breakeven import calculate_break_even
from backend.app.domain.analysis.npv import calculate_npv
from backend.app.domain.models import MarketContext, MortgageTrack
from backend.app.domain.scenarios.models import RefinanceCostBreakdown, ScenarioEvaluation, ScenarioType
from backend.app.domain.totals import calculate_total_monthly_payment


def evaluate_scenario_portfolio(
    *,
    scenario_id: str,
    scenario_type: ScenarioType,
    name_code: str,
    description_code: str,
    portfolio_tracks: list[MortgageTrack],
    current_monthly_payment: Decimal,
    refinance_costs: RefinanceCostBreakdown,
    market_context: MarketContext,
    horizon_months: int,
    annual_discount_rate_percent: Decimal,
    refinanced_track_labels: list[str],
    kept_track_labels: list[str],
    metadata: dict[str, object] | None = None,
) -> ScenarioEvaluation:
    summary = calculate_total_monthly_payment(tracks=portfolio_tracks, context=market_context)
    proposed_monthly_payment = summary.total_monthly_payment
    monthly_savings = current_monthly_payment - proposed_monthly_payment
    break_even = calculate_break_even(
        monthly_savings=monthly_savings,
        refinance_costs=refinance_costs.total_refinance_cost,
    )
    npv = calculate_npv(
        monthly_savings=monthly_savings,
        horizon_months=horizon_months,
        refinance_costs=refinance_costs.total_refinance_cost,
        annual_discount_rate_percent=annual_discount_rate_percent,
    )

    return ScenarioEvaluation(
        id=scenario_id,
        type=scenario_type,
        name_code=name_code,
        description_code=description_code,
        portfolio_tracks=portfolio_tracks,
        refinanced_track_labels=refinanced_track_labels,
        kept_track_labels=kept_track_labels,
        current_monthly_payment=current_monthly_payment,
        proposed_monthly_payment=proposed_monthly_payment,
        monthly_savings=monthly_savings,
        total_outstanding_balance=summary.total_outstanding_balance,
        total_adjusted_balance=summary.total_adjusted_balance,
        refinance_costs=refinance_costs,
        break_even=break_even,
        npv=npv,
        metadata={
            **summary.assumptions,
            **(metadata or {}),
            "horizon_months": horizon_months,
        },
    )
