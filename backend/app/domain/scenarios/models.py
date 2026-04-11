from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

from backend.app.domain.analysis.breakeven import BreakEvenAnalysis
from backend.app.domain.analysis.npv import NpvAnalysis
from backend.app.domain.models import MortgageTrack


class ScenarioType(str, Enum):
    STATUS_QUO = "status_quo"
    FULL_REFINANCE = "full_refinance"
    PARTIAL_REFINANCE = "partial_refinance"


@dataclass(frozen=True)
class CostComponent:
    amount: Decimal
    source: str
    included: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RefinanceCostBreakdown:
    advisor_fee: CostComponent
    bank_fee: CostComponent
    appraisal_fee: CostComponent
    legacy_other_costs: CostComponent
    prepayment_penalty_total: Decimal
    track_penalties: list[dict[str, Any]] = field(default_factory=list)
    total_refinance_cost: Decimal = Decimal("0")
    source: str = "legacy_inputs"
    warning_codes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PrimeRobustnessPathResult:
    path_code: str
    boi_base_rate_start: Decimal
    boi_base_rate_end: Decimal
    projected_monthly_payment: Decimal
    monthly_savings_vs_status_quo: Decimal
    npv: Decimal
    remains_beneficial: bool
    warning_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PrimeRobustnessAnalysis:
    has_prime_exposure: bool
    beneficial_under_all_paths: bool
    path_results: list[PrimeRobustnessPathResult] = field(default_factory=list)
    warning_codes: list[str] = field(default_factory=list)


@dataclass
class ScenarioEvaluation:
    id: str
    type: ScenarioType
    name_code: str
    description_code: str
    portfolio_tracks: list[MortgageTrack]
    refinanced_track_labels: list[str]
    kept_track_labels: list[str]
    current_monthly_payment: Decimal
    proposed_monthly_payment: Decimal
    monthly_savings: Decimal
    total_outstanding_balance: Decimal
    total_adjusted_balance: Decimal
    refinance_costs: RefinanceCostBreakdown
    break_even: BreakEvenAnalysis
    npv: NpvAnalysis
    risk_flags: list[str] = field(default_factory=list)
    explanation_tokens: list[str] = field(default_factory=list)
    robustness: PrimeRobustnessAnalysis | None = None
    recommendation_score: Decimal = Decimal("0")
    metadata: dict[str, Any] = field(default_factory=dict)
