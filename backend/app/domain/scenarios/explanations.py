from __future__ import annotations

from decimal import Decimal

from backend.app.domain.models import TrackType
from backend.app.domain.scenarios.models import ScenarioEvaluation, ScenarioType


def derive_scenario_tokens_and_risks(
    *,
    scenario: ScenarioEvaluation,
    status_quo: ScenarioEvaluation,
) -> tuple[list[str], list[str]]:
    explanation_tokens: set[str] = set()
    risk_flags: set[str] = set()

    current_track_types = {track.track_type for track in status_quo.portfolio_tracks}
    scenario_track_types = {track.track_type for track in scenario.portfolio_tracks}

    if scenario.monthly_savings > 0:
        explanation_tokens.add("LOWER_PAYMENT")
    if scenario.npv.npv > 0:
        explanation_tokens.add("POSITIVE_NPV")
    else:
        explanation_tokens.add("NEGATIVE_NPV")
        if scenario.type != ScenarioType.STATUS_QUO:
            risk_flags.add("NEGATIVE_NPV")

    if scenario.break_even.is_viable and scenario.break_even.break_even_months is not None:
        if scenario.break_even.break_even_months <= 24:
            explanation_tokens.add("FAST_BREAK_EVEN")
        elif scenario.break_even.break_even_months >= 60:
            explanation_tokens.add("LONG_BREAK_EVEN")
            risk_flags.add("LONG_BREAK_EVEN")

    if scenario.refinance_costs.total_refinance_cost > max(status_quo.current_monthly_payment * Decimal("12"), Decimal("0")):
        explanation_tokens.add("HIGH_UPFRONT_COST")
        risk_flags.add("HIGH_UPFRONT_COST")

    if TrackType.PRIME_FLOATING in scenario_track_types:
        risk_flags.add("PRIME_EXPOSURE")
    elif TrackType.PRIME_FLOATING in current_track_types and TrackType.PRIME_FLOATING not in scenario_track_types:
        explanation_tokens.add("REDUCED_PRIME_EXPOSURE")

    linked_types = {TrackType.FIXED_LINKED, TrackType.ADJUSTABLE_LINKED}
    if scenario_track_types & linked_types:
        risk_flags.add("CPI_LINKED_EXPOSURE")
    elif current_track_types & linked_types and not (scenario_track_types & linked_types):
        explanation_tokens.add("REDUCED_CPI_EXPOSURE")

    adjustable_types = {TrackType.ADJUSTABLE_LINKED, TrackType.ADJUSTABLE_NON_LINKED}
    if scenario_track_types & adjustable_types:
        risk_flags.add("RESET_DATE_RISK")
    elif current_track_types & adjustable_types and not (scenario_track_types & adjustable_types):
        explanation_tokens.add("REDUCED_RESET_EXPOSURE")

    if any(track.track_type == TrackType.PRIME_FLOATING for track in scenario.portfolio_tracks) and scenario.robustness is None:
        risk_flags.add("LOW_CONFIDENCE_INPUTS")
        explanation_tokens.add("LOW_CONFIDENCE_INPUTS")

    if scenario.robustness is not None:
        if scenario.robustness.beneficial_under_all_paths and scenario.type != ScenarioType.STATUS_QUO:
            explanation_tokens.add("BENEFICIAL_UNDER_BOTH_RATE_SCENARIOS")
        elif scenario.type != ScenarioType.STATUS_QUO and not scenario.robustness.beneficial_under_all_paths:
            risk_flags.add("RATE_PATH_SENSITIVITY")
            explanation_tokens.add("SENSITIVE_TO_RISING_RATES")

    if scenario.type == ScenarioType.STATUS_QUO:
        explanation_tokens.add("STATUS_QUO_BASELINE")

    return sorted(explanation_tokens), sorted(risk_flags)


def derive_recommendation_tokens(
    *,
    ranked_scenarios: list[ScenarioEvaluation],
    status_quo: ScenarioEvaluation,
) -> list[str]:
    if not ranked_scenarios:
        return ["NO_SCENARIOS_AVAILABLE"]

    best = ranked_scenarios[0]
    tokens: set[str] = set(best.explanation_tokens)
    if best.id == status_quo.id:
        tokens.add("KEEPING_CURRENT_IS_PREFERRED")
        return sorted(tokens)

    tokens.add("BETTER_ALTERNATIVE_FOUND")
    if best.type == ScenarioType.PARTIAL_REFINANCE:
        tokens.add("PARTIAL_REFINANCE_RECOMMENDED")
        full_scenarios = [scenario for scenario in ranked_scenarios if scenario.type == ScenarioType.FULL_REFINANCE]
        if full_scenarios and best.recommendation_score > full_scenarios[0].recommendation_score:
            tokens.add("PARTIAL_REFI_OUTPERFORMS_FULL")
    elif best.type == ScenarioType.FULL_REFINANCE:
        tokens.add("FULL_REFINANCE_RECOMMENDED")

    return sorted(tokens)
