from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from backend.app.domain.scenarios.models import ScenarioEvaluation, ScenarioType


@dataclass(frozen=True)
class RecommendationRankingItem:
    scenario_id: str
    scenario_type: str
    rank: int
    score: Decimal
    is_better_than_status_quo: bool
    explanation_tokens: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RecommendationOutcome:
    best_scenario_id: str
    recommendation_code: str
    confidence: str
    is_better_than_status_quo: bool
    requires_human_followup_offer: bool
    explanation_tokens: list[str] = field(default_factory=list)
    ranking: list[RecommendationRankingItem] = field(default_factory=list)


def build_recommendation_outcome(
    *,
    ranked_scenarios: list[ScenarioEvaluation],
    status_quo_scenario: ScenarioEvaluation,
    explanation_tokens: list[str],
) -> RecommendationOutcome:
    best_scenario = ranked_scenarios[0]
    is_better_than_status_quo = (
        best_scenario.id != status_quo_scenario.id
        and best_scenario.monthly_savings > 0
        and best_scenario.npv.npv > 0
        and best_scenario.recommendation_score > status_quo_scenario.recommendation_score
    )
    requires_human_followup_offer = is_better_than_status_quo and best_scenario.type != ScenarioType.STATUS_QUO

    if not is_better_than_status_quo:
        recommendation_code = "KEEP_CURRENT"
    elif best_scenario.type == ScenarioType.PARTIAL_REFINANCE:
        recommendation_code = "CONSIDER_PARTIAL_REFINANCE"
    else:
        recommendation_code = "CONSIDER_FULL_REFINANCE"

    confidence = "high" if "LOW_CONFIDENCE_INPUTS" not in explanation_tokens else "medium"

    ranking = [
        RecommendationRankingItem(
            scenario_id=scenario.id,
            scenario_type=scenario.type.value,
            rank=index + 1,
            score=scenario.recommendation_score,
            is_better_than_status_quo=scenario.id != status_quo_scenario.id
            and scenario.recommendation_score > status_quo_scenario.recommendation_score,
            explanation_tokens=list(scenario.explanation_tokens),
        )
        for index, scenario in enumerate(ranked_scenarios)
    ]

    return RecommendationOutcome(
        best_scenario_id=best_scenario.id,
        recommendation_code=recommendation_code,
        confidence=confidence,
        is_better_than_status_quo=is_better_than_status_quo,
        requires_human_followup_offer=requires_human_followup_offer,
        explanation_tokens=explanation_tokens,
        ranking=ranking,
    )
