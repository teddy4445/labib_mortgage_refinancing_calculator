from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MarketDataCategory(str, Enum):
    BOI_BASE_RATE = "BOI_BASE_RATE"
    BOI_MORTGAGE_RATE_BUCKETS = "BOI_MORTGAGE_RATE_BUCKETS"
    CPI_SERIES = "CPI_SERIES"
    INFLATION_EXPECTATIONS = "INFLATION_EXPECTATIONS"


class MarketDataSourceHealth(str, Enum):
    HEALTHY = "healthy"
    DELAYED = "delayed"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass(frozen=True)
class MarketDataSourceDefinition:
    source_key: str
    display_name: str
    category: MarketDataCategory
    provider: str
    source_type: str
    expected_refresh_hours: int
    endpoint_setting_name: str | None = None
    enabled_setting_name: str | None = None
    notes: str | None = None
    aliases: tuple[str, ...] = ()


class BoiBaseRateRecord(BaseModel):
    effective_date: date
    annual_rate_percent: Decimal = Field(ge=0, le=25)
    source_key: str


class MortgageRateBucketRecord(BaseModel):
    effective_date: date
    track_family: str
    bucket_code: str
    remaining_months_min: int = Field(ge=1)
    remaining_months_max: int = Field(ge=1)
    annual_rate_percent: Decimal = Field(ge=0, le=25)
    source_key: str


class CpiRecord(BaseModel):
    period: str
    index_value: Decimal = Field(gt=0)
    release_date: date
    source_key: str


class InflationExpectationRecord(BaseModel):
    horizon_months: int = Field(ge=1)
    expected_inflation_percent: Decimal = Field(ge=-5, le=30)
    effective_date: date
    source_key: str


class MarketDataSnapshotEnvelope(BaseModel):
    source_key: str
    category: MarketDataCategory
    effective_at: datetime
    schema_version: str = "2026-04-11"
    connector_version: str = "phase4-market-data-v1"
    records: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "valid"
    warning_codes: list[str] = Field(default_factory=list)
    anomaly_flags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str


@dataclass(frozen=True)
class MarketSourceStatusSummary:
    source_key: str
    display_name: str
    category: str
    status: str
    enabled: bool
    expected_refresh_hours: int
    snapshot_count: int
    latest_snapshot_id: int | None
    latest_effective_at: datetime | None
    last_success_at: datetime | None
    last_attempt_at: datetime | None
    last_error: str | None
    warning_codes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
