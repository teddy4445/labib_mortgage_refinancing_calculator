from __future__ import annotations

from decimal import Decimal

from backend.app.domain.scenarios.models import ScenarioEvaluation, ScenarioType


def _score_scenario(scenario: ScenarioEvaluation) -> Decimal:
    score = Decimal("0")
    if scenario.type == ScenarioType.STATUS_QUO:
        score += Decimal("5")

    if scenario.monthly_savings > 0:
        score += Decimal("20")
    elif scenario.monthly_savings < 0:
        score -= Decimal("12")

    if scenario.npv.npv > 0:
        score += Decimal("24")
    elif scenario.npv.npv < 0:
        score -= Decimal("24")

    if scenario.break_even.is_viable and scenario.break_even.break_even_months is not None:
        if scenario.break_even.break_even_months <= 24:
            score += Decimal("10")
        elif scenario.break_even.break_even_months <= 60:
            score += Decimal("4")
        else:
            score -= Decimal("8")

    if scenario.robustness is not None:
        if scenario.robustness.beneficial_under_all_paths:
            score += Decimal("8")
        elif scenario.robustness.has_prime_exposure:
            score -= Decimal("6")

    if "REDUCED_PRIME_EXPOSURE" in scenario.explanation_tokens:
        score += Decimal("4")
    if "REDUCED_CPI_EXPOSURE" in scenario.explanation_tokens:
        score += Decimal("3")
    if "REDUCED_RESET_EXPOSURE" in scenario.explanation_tokens:
        score += Decimal("2")
    if "HIGH_UPFRONT_COST" in scenario.risk_flags:
        score -= Decimal("5")
    if "LOW_CONFIDENCE_INPUTS" in scenario.risk_flags:
        score -= Decimal("4")

    return score


def rank_scenarios(scenarios: list[ScenarioEvaluation]) -> list[ScenarioEvaluation]:
    for scenario in scenarios:
        scenario.recommendation_score = _score_scenario(scenario)
    return sorted(
        scenarios,
        key=lambda scenario: (
            scenario.recommendation_score,
            scenario.npv.npv,
            scenario.monthly_savings,
            Decimal("1") if scenario.type != ScenarioType.STATUS_QUO else Decimal("0"),
        ),
        reverse=True,
    )
