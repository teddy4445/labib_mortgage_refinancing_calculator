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
    outstanding_balance: Decimal = Field(ge=0)
    current_rate: Decimal = Field(ge=0)
    remaining_term_months: int = Field(ge=1)
    linkage_type: str | None = None
    rate_type: str | None = None
    reset_interval: str | None = None
    next_reset_date: date | None = None
    amortization_method: str | None = None
    prepayment_penalty_rule: str | None = None


class MortgageInput(BaseModel):
    lender_name: str
    property_city: str | None = None
    property_value: Decimal = Field(ge=0)
    current_monthly_payment: Decimal = Field(ge=0)
    loan_purpose: str | None = None
    occupancy_status: str | None = None
    prepayment_fee: Decimal = Field(default=Decimal("0"), ge=0)
    advisor_cost: Decimal = Field(default=Decimal("0"), ge=0)
    tracks: list[TrackInput] = Field(min_length=1)


class RefinanceOffer(BaseModel):
    interest_rate: Decimal = Field(ge=0)
    term_months: int = Field(ge=1)
    upfront_costs: Decimal = Field(default=Decimal("0"), ge=0)


class CalculationRequest(BaseModel):
    mortgage: MortgageInput
    proposed_full_refinance: RefinanceOffer
    proposed_partial_refinance: RefinanceOffer | None = None
    holding_period_years: int = Field(default=8, ge=1, le=30)


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
    last_success_at: datetime | None = None
    last_error: str | None = None


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
