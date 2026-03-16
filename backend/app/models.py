from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    LOCKED = "locked"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    HISTORY = "history"
    DISMISSED = "dismissed"


class RequestStatus(str, enum.Enum):
    OPEN = "open"
    FORWARDED = "forwarded"
    CLOSED = "closed"


class DataSourceStatus(str, enum.Enum):
    HEALTHY = "healthy"
    DELAYED = "delayed"
    FAILED = "failed"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(40))
    first_name: Mapped[str | None] = mapped_column(String(80))
    last_name: Mapped[str | None] = mapped_column(String(80))
    age: Mapped[int | None]
    gender: Mapped[str | None] = mapped_column(String(30))
    marital_status: Mapped[str | None] = mapped_column(String(30))
    occupation: Mapped[str | None] = mapped_column(String(120))
    holding_period_years: Mapped[int | None]
    risk_tolerance: Mapped[str | None] = mapped_column(String(30))
    payment_sensitivity: Mapped[str | None] = mapped_column(String(30))
    preference_goal: Mapped[str | None] = mapped_column(String(30))
    inflation_aversion: Mapped[str | None] = mapped_column(String(30))
    reset_risk_aversion: Mapped[str | None] = mapped_column(String(30))
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    expert_contact_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.PENDING)

    mortgages: Mapped[list["Mortgage"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    requests: Mapped[list["CustomerRequest"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    analytics_events: Mapped[list["AnalyticsEvent"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class EmailVerificationToken(TimestampMixin, Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordResetToken(TimestampMixin, Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Mortgage(TimestampMixin, Base):
    __tablename__ = "mortgages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lender_name: Mapped[str] = mapped_column(String(120))
    property_city: Mapped[str | None] = mapped_column(String(120))
    property_value: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    current_monthly_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    loan_purpose: Mapped[str | None] = mapped_column(String(60))
    occupancy_status: Mapped[str | None] = mapped_column(String(60))
    outstanding_balance_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    estimated_refinance_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="mortgages")
    tracks: Mapped[list["MortgageTrack"]] = relationship(back_populates="mortgage", cascade="all, delete-orphan")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="mortgage", cascade="all, delete-orphan"
    )


class MortgageTrack(TimestampMixin, Base):
    __tablename__ = "mortgage_tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    mortgage_id: Mapped[int] = mapped_column(ForeignKey("mortgages.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(120))
    track_type: Mapped[str] = mapped_column(String(60))
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    current_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    remaining_term_months: Mapped[int]
    linkage_type: Mapped[str | None] = mapped_column(String(60))
    rate_type: Mapped[str | None] = mapped_column(String(60))
    reset_interval: Mapped[str | None] = mapped_column(String(120))
    next_reset_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    amortization_method: Mapped[str | None] = mapped_column(String(60))
    prepayment_penalty_rule: Mapped[str | None] = mapped_column(String(255))

    mortgage: Mapped["Mortgage"] = relationship(back_populates="tracks")


class AnalysisRun(TimestampMixin, Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    mortgage_id: Mapped[int] = mapped_column(ForeignKey("mortgages.id", ondelete="CASCADE"), index=True)
    recommendation_type: Mapped[str] = mapped_column(String(60))
    should_act_now: Mapped[bool] = mapped_column(Boolean, default=False)
    current_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    proposed_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    projected_net_savings: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    upfront_costs: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    break_even_month: Mapped[int | None]
    npv: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    risk_reduction_summary: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_output: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    mortgage: Mapped["Mortgage"] = relationship(back_populates="analysis_runs")


class Alert(TimestampMixin, Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    source: Mapped[str | None] = mapped_column(String(60))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="alerts")


class CustomerRequest(TimestampMixin, Base):
    __tablename__ = "customer_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    request_type: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.OPEN)
    source_page: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="requests")


class AnalyticsEvent(TimestampMixin, Base):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    session_id: Mapped[str | None] = mapped_column(String(120), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    page: Mapped[str | None] = mapped_column(String(120))
    traffic_source: Mapped[str | None] = mapped_column(String(120), index=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="analytics_events")


class ErrorEvent(TimestampMixin, Base):
    __tablename__ = "error_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    service: Mapped[str] = mapped_column(String(80), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class MarketDataSource(TimestampMixin, Base):
    __tablename__ = "market_data_sources"
    __table_args__ = (UniqueConstraint("source_key", name="uq_market_data_source_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(120), index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    status: Mapped[DataSourceStatus] = mapped_column(Enum(DataSourceStatus), default=DataSourceStatus.HEALTHY)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    source_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    snapshots: Mapped[list["MarketDataSnapshot"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class MarketDataSnapshot(TimestampMixin, Base):
    __tablename__ = "market_data_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("market_data_sources.id", ondelete="CASCADE"), index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    source: Mapped["MarketDataSource"] = relationship(back_populates="snapshots")
