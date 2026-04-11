from __future__ import annotations

from decimal import Decimal

from backend.app.domain.analysis.npv import calculate_npv
from backend.app.domain.exceptions import MissingMarketInputError
from backend.app.domain.models import MarketContext
from backend.app.domain.scenarios.models import PrimeRobustnessAnalysis, PrimeRobustnessPathResult, ScenarioEvaluation
from backend.app.domain.totals import calculate_total_monthly_payment


def evaluate_prime_robustness(
    *,
    scenario: ScenarioEvaluation,
    status_quo: ScenarioEvaluation,
    base_context: MarketContext,
    annual_discount_rate_percent: Decimal,
    holding_period_months: int,
    modest_annual_increase_percent: Decimal,
) -> PrimeRobustnessAnalysis:
    has_prime_exposure = any(track.track_type.value == "prime_floating" for track in scenario.portfolio_tracks) or any(
        track.track_type.value == "prime_floating" for track in status_quo.portfolio_tracks
    )
    if not has_prime_exposure:
        return PrimeRobustnessAnalysis(has_prime_exposure=False, beneficial_under_all_paths=True, path_results=[])

    if base_context.boi_base_rate is None:
        raise MissingMarketInputError("boi_base_rate is required for prime robustness analysis.")

    path_definitions = [
        ("STABLE_BOI", base_context.boi_base_rate),
        ("MODEST_BOI_INCREASE", base_context.boi_base_rate + modest_annual_increase_percent),
    ]
    path_results: list[PrimeRobustnessPathResult] = []

    for path_code, ending_boi_rate in path_definitions:
        scenario_summary = calculate_total_monthly_payment(
            tracks=scenario.portfolio_tracks,
            context=MarketContext(
                boi_base_rate=ending_boi_rate,
                current_cpi=base_context.current_cpi,
                as_of=base_context.as_of,
            ),
        )
        status_quo_summary = calculate_total_monthly_payment(
            tracks=status_quo.portfolio_tracks,
            context=MarketContext(
                boi_base_rate=ending_boi_rate,
                current_cpi=base_context.current_cpi,
                as_of=base_context.as_of,
            ),
        )
        monthly_savings = status_quo_summary.total_monthly_payment - scenario_summary.total_monthly_payment
        npv = calculate_npv(
            monthly_savings=monthly_savings,
            horizon_months=holding_period_months,
            refinance_costs=scenario.refinance_costs.total_refinance_cost,
            annual_discount_rate_percent=annual_discount_rate_percent,
        )
        path_results.append(
            PrimeRobustnessPathResult(
                path_code=path_code,
                boi_base_rate_start=base_context.boi_base_rate,
                boi_base_rate_end=ending_boi_rate,
                projected_monthly_payment=scenario_summary.total_monthly_payment,
                monthly_savings_vs_status_quo=monthly_savings,
                npv=npv.npv,
                remains_beneficial=monthly_savings > 0 and npv.npv > 0,
            )
        )

    return PrimeRobustnessAnalysis(
        has_prime_exposure=True,
        beneficial_under_all_paths=all(path.remains_beneficial for path in path_results),
        path_results=path_results,
    )
