from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class EmailPayload(BaseModel):
    to_email: EmailStr
    subject: str
    template_name: str
    context: dict[str, Any] = Field(default_factory=dict)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    age: int | None = Field(default=None, ge=18, le=120)
    gender: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    holding_period_years: int | None = Field(default=None, ge=1, le=30)
    risk_tolerance: str | None = None
    payment_sensitivity: str | None = None
    preference_goal: str | None = None
    inflation_aversion: str | None = None
    reset_risk_aversion: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class TrackInput(BaseModel):
    label: str
    track_type: str
    outstanding_balance: Decimal = Field(gt=0)
    current_rate: Decimal | None = Field(default=None, ge=0)
    remaining_term_months: int = Field(ge=1)
    linkage_type: str | None = None
    rate_type: str | None = None
    reset_interval: str | None = None
    next_reset_date: date | None = None
    amortization_method: str | None = None
    prepayment_penalty_rule: str | None = None
    original_cpi: Decimal | None = Field(default=None, gt=0)
    bank_margin: Decimal | None = None


class MarketInputs(BaseModel):
    boi_base_rate: Decimal | None = Field(default=None, ge=0)
    current_cpi: Decimal | None = Field(default=None, gt=0)
    as_of: date | None = None


class MortgageInput(BaseModel):
    lender_name: str
    property_city: str | None = None
    property_value: Decimal = Field(ge=0)
    current_monthly_payment: Decimal = Field(ge=0)
    loan_purpose: str | None = None
    occupancy_status: str | None = None
    prepayment_fee: Decimal = Field(default=Decimal("0"), ge=0)
    advisor_cost: Decimal = Field(default=Decimal("0"), ge=0)
    bank_cost: Decimal = Field(default=Decimal("0"), ge=0)
    appraisal_cost: Decimal = Field(default=Decimal("0"), ge=0)
    tracks: list[TrackInput] = Field(min_length=1)


class RefinanceOffer(BaseModel):
    interest_rate: Decimal = Field(ge=0)
    term_months: int = Field(ge=1)
    upfront_costs: Decimal = Field(default=Decimal("0"), ge=0)
    track_type: str | None = None
    label: str | None = None
    linkage_type: str | None = None
    rate_type: str | None = None
    bank_margin: Decimal | None = None
    original_cpi: Decimal | None = Field(default=None, gt=0)
    reset_interval: str | None = None
    next_reset_date: date | None = None


class CalculationRequest(BaseModel):
    mortgage: MortgageInput
    proposed_full_refinance: RefinanceOffer
    proposed_partial_refinance: RefinanceOffer | None = None
    market_inputs: MarketInputs | None = None
    holding_period_years: int = Field(default=8, ge=1, le=30)


class TrackPaymentBreakdown(BaseModel):
    label: str
    track_type: str
    monthly_payment: Decimal
    outstanding_balance: Decimal
    adjusted_balance: Decimal | None = None
    effective_annual_rate: Decimal
    monthly_rate: Decimal
    prepayment_penalty_applies: bool
    linkage_type: str | None = None
    rate_type: str | None = None
    reset_interval: str | None = None
    next_reset_date: date | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CurrentMortgageSummary(BaseModel):
    total_monthly_payment: Decimal
    total_outstanding_balance: Decimal
    total_adjusted_balance: Decimal
    track_breakdown: list[TrackPaymentBreakdown]
    assumptions: dict[str, Any] = Field(default_factory=dict)


class RefinanceCostComponentView(BaseModel):
    amount: Decimal
    source: str
    included: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class RefinanceCostBreakdownView(BaseModel):
    advisor_fee: RefinanceCostComponentView
    bank_fee: RefinanceCostComponentView
    appraisal_fee: RefinanceCostComponentView
    legacy_other_costs: RefinanceCostComponentView
    prepayment_penalty_total: Decimal
    track_penalties: list[dict[str, Any]] = Field(default_factory=list)
    total_refinance_cost: Decimal
    source: str
    warning_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BreakEvenView(BaseModel):
    break_even_months: int | None = None
    break_even_years: Decimal | None = None
    raw_break_even_months: Decimal | None = None
    monthly_savings: Decimal
    refinance_costs: Decimal
    is_viable: bool
    reason_code: str


class NpvView(BaseModel):
    npv: Decimal
    total_present_value: Decimal
    monthly_discount_rate: Decimal
    annual_discount_rate: Decimal
    horizon_months: int
    is_positive: bool
    reason_code: str


class PrimeRobustnessPathView(BaseModel):
    path_code: str
    boi_base_rate_start: Decimal
    boi_base_rate_end: Decimal
    projected_monthly_payment: Decimal
    monthly_savings_vs_status_quo: Decimal
    npv: Decimal
    remains_beneficial: bool
    warning_codes: list[str] = Field(default_factory=list)


class PrimeRobustnessView(BaseModel):
    has_prime_exposure: bool
    beneficial_under_all_paths: bool
    path_results: list[PrimeRobustnessPathView] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)


class ScenarioView(BaseModel):
    id: str
    scenario_type: str
    name_code: str
    description_code: str
    refinanced_track_labels: list[str] = Field(default_factory=list)
    kept_track_labels: list[str] = Field(default_factory=list)
    current_monthly_payment: Decimal
    proposed_monthly_payment: Decimal
    monthly_savings: Decimal
    total_outstanding_balance: Decimal
    total_adjusted_balance: Decimal
    refinance_costs: RefinanceCostBreakdownView
    break_even: BreakEvenView
    npv: NpvView
    risk_flags: list[str] = Field(default_factory=list)
    explanation_tokens: list[str] = Field(default_factory=list)
    robustness: PrimeRobustnessView | None = None
    recommendation_score: Decimal
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendationRankingItemView(BaseModel):
    scenario_id: str
    scenario_type: str
    rank: int
    score: Decimal
    is_better_than_status_quo: bool
    explanation_tokens: list[str] = Field(default_factory=list)


class RecommendationSummaryView(BaseModel):
    best_scenario_id: str
    recommendation_code: str
    confidence: str
    is_better_than_status_quo: bool
    requires_human_followup_offer: bool
    explanation_tokens: list[str] = Field(default_factory=list)
    ranking: list[RecommendationRankingItemView] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    current_monthly_payment: Decimal
    projected_monthly_payment: Decimal
    projected_net_savings: Decimal
    break_even_month: int | None = None
    npv: Decimal | None = None
    should_act_now: bool
    recommendation_type: str
    explanation: str
    assumptions: dict[str, Any] = Field(default_factory=dict)
    current_summary: CurrentMortgageSummary | None = None
    scenarios: list[ScenarioView] = Field(default_factory=list)
    recommendation_summary: RecommendationSummaryView | None = None
    explanation_tokens: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    analysis_kind: str | None = None
    calculated_at: datetime | None = None
    best_scenario: ScenarioView | None = None
    status_quo_scenario: ScenarioView | None = None
    alternative_scenarios: list[ScenarioView] = Field(default_factory=list)
    robustness_summary: PrimeRobustnessView | None = None
    found_better_alternative: bool = False
    requires_human_followup_offer: bool = False
    data_provenance: dict[str, Any] = Field(default_factory=dict)
    meta: ResponseMeta | None = None


class AnalyticsEventIn(BaseModel):
    session_id: str | None = None
    user_id: int | None = None
    event_type: str
    page: str | None = None
    traffic_source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerRequestIn(BaseModel):
    user_id: int | None = None
    request_type: str
    source_page: str | None = None
    notes: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class MortgageCreateRequest(BaseModel):
    user_id: int
    mortgage: MortgageInput
    raw_payload: dict[str, Any] | None = None


class MortgageCreateResponse(BaseModel):
    mortgage_id: int
    meta: ResponseMeta


class AnalyticsAckResponse(BaseModel):
    status: str
    meta: ResponseMeta


class ResponseMeta(BaseModel):
    request_id: str
    timestamp: datetime
    contract_version: str


class ErrorDetailItem(BaseModel):
    field: str
    message: str
    error_type: str | None = None


class ErrorDetailView(BaseModel):
    code: str
    message: str
    fields: list[ErrorDetailItem] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    detail: str
    error: ErrorDetailView
    meta: ResponseMeta


class RegisterResponse(BaseModel):
    status: str
    user_id: int
    meta: ResponseMeta


class LoginResponse(BaseModel):
    status: str
    role: str
    user_id: int
    username: str
    email: EmailStr
    account_status: str | None = None
    email_verified: bool | None = None
    meta: ResponseMeta


class EmailAvailabilityResponse(BaseModel):
    available: bool
    code: str
    meta: ResponseMeta


class ForgotPasswordResponse(BaseModel):
    status: str
    email: EmailStr | None = None
    meta: ResponseMeta


class ResetPasswordResponse(BaseModel):
    status: str
    meta: ResponseMeta


class MortgageTrackView(BaseModel):
    id: int
    label: str
    track_type: str
    outstanding_balance: float
    current_rate: float | None = None
    remaining_term_months: int
    linkage_type: str | None = None
    rate_type: str | None = None
    reset_interval: str | None = None
    next_reset_date: str | None = None
    amortization_method: str | None = None
    prepayment_penalty_rule: str | None = None


class AnalysisReadinessView(BaseModel):
    ready: bool
    missing_data_flags: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)


class AnalysisSnapshotSummaryView(BaseModel):
    analysis_run_id: int | None = None
    recommendation_code: str | None = None
    should_act_now: bool | None = None
    break_even_month: int | None = None
    projected_net_savings: Decimal | None = None
    created_at: datetime | None = None
    source: str


class MortgageSummaryView(BaseModel):
    id: int
    user_id: int
    lender_name: str
    property_city: str | None = None
    property_value: float
    current_monthly_payment: float
    loan_purpose: str | None = None
    occupancy_status: str | None = None
    outstanding_balance_total: float
    estimated_refinance_cost: float
    tracks: list[MortgageTrackView] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    normalized_values: dict[str, Any] = Field(default_factory=dict)
    analysis_readiness: AnalysisReadinessView
    latest_analysis_summary: AnalysisSnapshotSummaryView | None = None


class LatestMortgageResponse(BaseModel):
    mortgage: MortgageSummaryView | None = None
    meta: ResponseMeta


class DashboardRecommendationView(BaseModel):
    headline: str
    tone: str
    reason: str
    recommendation_code: str | None = None


class DashboardUrgencyView(BaseModel):
    label: str
    description: str
    code: str


class AlertSummaryView(BaseModel):
    active_count: int
    history_count: int
    dismissed_count: int
    top_severity: str | None = None


class MarketFreshnessSummaryView(BaseModel):
    status: str
    healthy_sources: int
    delayed_sources: int
    failed_sources: int
    latest_success_at: datetime | None = None
    warning_codes: list[str] = Field(default_factory=list)


class PendingFollowupRequestView(BaseModel):
    exists: bool
    request_id: int | None = None
    status: str | None = None
    created_at: datetime | None = None
    mortgage_id: int | None = None
    analysis_run_id: int | None = None
    request_type: str | None = None
    source_page: str | None = None


class DashboardAnalysisMetaView(BaseModel):
    source: str
    engine_version: str | None = None
    calculated_at: datetime
    market_as_of: date | None = None


class DashboardView(BaseModel):
    recommendation: DashboardRecommendationView
    urgency: DashboardUrgencyView
    currentMonthlyPayment: float
    estimatedRefinancePayment: float
    projectedNetSavings: float
    breakEvenMonths: int
    lastAnalysisTime: datetime
    currentSummary: CurrentMortgageSummary | None = None
    recommendationSummary: RecommendationSummaryView | None = None
    scenarios: list[ScenarioView] = Field(default_factory=list)
    explanationTokens: list[str] = Field(default_factory=list)
    riskFlags: list[str] = Field(default_factory=list)
    analysisVersion: str | None = None
    mortgageSummary: MortgageSummaryView
    latestAnalysisSummary: AnalysisSnapshotSummaryView
    hasBetterOption: bool
    topExplanationTokens: list[str] = Field(default_factory=list)
    topRiskFlags: list[str] = Field(default_factory=list)
    alertSummary: AlertSummaryView
    marketDataFreshness: MarketFreshnessSummaryView
    pendingFollowUpRequest: PendingFollowupRequestView
    analysisMeta: DashboardAnalysisMetaView


class DashboardResponse(BaseModel):
    dashboard: DashboardView | None = None
    meta: ResponseMeta


class AlertView(BaseModel):
    id: int
    code: str
    title: str
    message: str
    description: str
    severity: str
    category: str
    timestamp: datetime
    status: str
    dismissed: bool
    explanation_tokens: list[str] = Field(default_factory=list)
    related_mortgage_id: int | None = None
    related_analysis_run_id: int | None = None
    action_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertsListResponse(BaseModel):
    active: list[AlertView] = Field(default_factory=list)
    history: list[AlertView] = Field(default_factory=list)
    dismissed: list[AlertView] = Field(default_factory=list)
    summary: AlertSummaryView
    meta: ResponseMeta


class AlertDismissResponse(BaseModel):
    status: str
    alert_id: int | None = None
    meta: ResponseMeta


class InterestRequestIn(CustomerRequestIn):
    mortgage_id: int | None = None
    analysis_run_id: int | None = None
    recommendation_code: str | None = None
    contact_preference: str | None = None


class InterestRequestResponse(BaseModel):
    status: str
    request_id: int | None = None
    created_at: datetime | None = None
    request_type: str | None = None
    linked_mortgage_id: int | None = None
    linked_analysis_run_id: int | None = None
    confirmation_code: str | None = None
    meta: ResponseMeta


class AdminMetric(BaseModel):
    label: str
    value: int | float | str
    change: str | None = None


class SeriesPoint(BaseModel):
    date: date
    value: int


class DataSourceStatusView(BaseModel):
    source_key: str
    display_name: str
    status: str
    category: str | None = None
    enabled: bool = True
    expected_refresh_hours: int | None = None
    snapshot_count: int | None = None
    latest_snapshot_id: int | None = None
    latest_effective_at: datetime | None = None
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    last_error: str | None = None
    warning_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MarketRefreshResultView(BaseModel):
    source_key: str
    status: str
    snapshot_id: int | None = None
    snapshot_created: bool = False
    effective_at: datetime | None = None
    warning_codes: list[str] = Field(default_factory=list)
    anomaly_flags: list[str] = Field(default_factory=list)
    error: str | None = None


class MarketRefreshBatchResponse(BaseModel):
    overall_status: str
    refreshed_at: datetime
    results: list[MarketRefreshResultView] = Field(default_factory=list)


class UserListItem(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: str | None = None
    status: str
    role: str
    created_at: datetime


class AdminOverviewResponse(BaseModel):
    metrics: list[AdminMetric]
    wizard_usage_last_30_days: list[SeriesPoint]
    help_requests_last_30_days: list[SeriesPoint]
    data_sources: list[DataSourceStatusView]
    users: list[UserListItem]


class AdminOverviewEnvelope(BaseModel):
    metrics: list[AdminMetric]
    wizard_usage_last_30_days: list[SeriesPoint]
    help_requests_last_30_days: list[SeriesPoint]
    data_sources: list[DataSourceStatusView]
    users: list[UserListItem]
    meta: ResponseMeta


class MarketRefreshBatchEnvelope(BaseModel):
    overall_status: str
    refreshed_at: datetime
    results: list[MarketRefreshResultView] = Field(default_factory=list)
    meta: ResponseMeta


class MarketRefreshResultEnvelope(BaseModel):
    source_key: str
    status: str
    snapshot_id: int | None = None
    snapshot_created: bool = False
    effective_at: datetime | None = None
    warning_codes: list[str] = Field(default_factory=list)
    anomaly_flags: list[str] = Field(default_factory=list)
    error: str | None = None
    meta: ResponseMeta


class AdminLockUserResponse(BaseModel):
    status: str
    user_id: int | None = None
    meta: ResponseMeta


class HealthResponse(BaseModel):
    status: str
    meta: ResponseMeta
