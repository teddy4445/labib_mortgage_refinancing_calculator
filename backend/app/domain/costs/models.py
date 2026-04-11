from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class CostComponent:
    amount: Decimal
    source: str
    included: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TrackPenaltyBreakdown:
    track_id: str
    track_label: str
    applicable: bool
    reason_code: str
    remaining_months: int
    market_rate_bucket: str | None
    market_annual_rate_percent: Decimal | None
    contract_annual_rate_percent: Decimal | None
    market_monthly_rate: Decimal | None
    contract_monthly_rate: Decimal | None
    pv_market_nis: Decimal | None
    pv_contract_nis: Decimal | None
    economic_loss_nis: Decimal | None
    discount_factor: Decimal | None
    penalty_before_discount_nis: Decimal
    penalty_after_discount_nis: Decimal
    rounded_penalty_nis: Decimal
    warning_codes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RefinanceCostBreakdown:
    advisor_fee: CostComponent
    bank_fee: CostComponent
    appraisal_fee: CostComponent
    legacy_other_costs: CostComponent
    prepayment_penalty_total: Decimal
    track_penalties: list[TrackPenaltyBreakdown] = field(default_factory=list)
    total_refinance_cost: Decimal = Decimal("0")
    source: str = "phase2_refinance_cost_engine"
    warning_codes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
