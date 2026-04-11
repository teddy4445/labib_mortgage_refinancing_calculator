from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app import models
from backend.app.domain.exceptions import MarketDataBucketLookupError, MarketDataNotFoundError
from backend.app.domain.market_data.models import CpiRecord, MortgageRateBucketRecord


@dataclass(frozen=True)
class DurationBucket:
    bucket_code: str
    remaining_months_min: int
    remaining_months_max: int


DURATION_BUCKETS = (
    DurationBucket("up_to_5_years", 1, 60),
    DurationBucket("five_to_ten_years", 61, 120),
    DurationBucket("ten_to_fifteen_years", 121, 180),
    DurationBucket("fifteen_to_twenty_years", 181, 240),
    DurationBucket("twenty_to_twenty_five_years", 241, 300),
    DurationBucket("twenty_five_to_thirty_years", 301, 360),
)


def lookup_mortgage_bucket_by_remaining_months(remaining_months: int) -> DurationBucket:
    for bucket in DURATION_BUCKETS:
        if bucket.remaining_months_min <= remaining_months <= bucket.remaining_months_max:
            return bucket
    raise MarketDataBucketLookupError(f"No mortgage-rate bucket defined for remaining_months={remaining_months}")


def select_latest_valid_snapshot_payload(snapshots: list[models.MarketDataSnapshot]) -> dict[str, Any]:
    for snapshot in sorted(snapshots, key=lambda item: (item.as_of, item.id), reverse=True):
        payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
        if payload.get("status") == "valid":
            return payload
    raise MarketDataNotFoundError("No valid market-data snapshot found.")


def select_latest_valid_source_snapshot(snapshots: list[models.MarketDataSnapshot]) -> models.MarketDataSnapshot:
    for snapshot in sorted(snapshots, key=lambda item: (item.as_of, item.id), reverse=True):
        payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
        if payload.get("status") == "valid":
            return snapshot
    raise MarketDataNotFoundError("No valid market-data snapshot found.")


def select_snapshot_effective_at(payload: dict[str, Any]) -> datetime | None:
    normalized = payload.get("normalized_payload", {}) if isinstance(payload.get("normalized_payload"), dict) else {}
    effective_at = normalized.get("effective_at")
    if isinstance(effective_at, str):
        return datetime.fromisoformat(effective_at)
    return None


def select_cpi_record_for_period(records: list[CpiRecord], period: str) -> CpiRecord:
    for record in records:
        if record.period == period:
            return record
    raise MarketDataNotFoundError(f"No CPI record found for period={period}")


def select_bucket_record(
    records: list[MortgageRateBucketRecord],
    *,
    remaining_months: int,
    track_family: str = "general",
) -> MortgageRateBucketRecord:
    bucket = lookup_mortgage_bucket_by_remaining_months(remaining_months)
    matching = [
        record
        for record in records
        if record.bucket_code == bucket.bucket_code and record.track_family == track_family
    ]
    if not matching:
        raise MarketDataBucketLookupError(
            f"No mortgage-rate bucket record found for remaining_months={remaining_months}, track_family={track_family}"
        )
    return matching[0]
