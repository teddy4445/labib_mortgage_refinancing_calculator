from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any

from backend.app.domain.exceptions import MarketDataParseError
from backend.app.domain.market_data.models import (
    BoiBaseRateRecord,
    CpiRecord,
    InflationExpectationRecord,
    MarketDataCategory,
    MarketDataSnapshotEnvelope,
    MortgageRateBucketRecord,
)
from backend.app.domain.market_data.selectors import lookup_mortgage_bucket_by_remaining_months
from backend.app.domain.market_data.validation import (
    detect_single_value_jump,
    validate_base_rate_records,
    validate_cpi_records,
    validate_inflation_expectation_records,
    validate_mortgage_rate_bucket_records,
)


def _to_date(value: Any, *, field_name: str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise MarketDataParseError(f"Invalid date value for {field_name}: {value!r}")


def _to_datetime_from_date(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # noqa: BLE001
        raise MarketDataParseError(f"Invalid decimal value for {field_name}: {value!r}") from exc


def _build_envelope(
    *,
    source_key: str,
    category: MarketDataCategory,
    effective_at: datetime,
    records: list[dict[str, Any]],
    warning_codes: list[str],
    anomaly_flags: list[str],
    metadata: dict[str, Any] | None = None,
    connector_version: str = "phase4-market-data-v1",
) -> MarketDataSnapshotEnvelope:
    payload_for_hash = {
        "source_key": source_key,
        "category": category.value,
        "effective_at": effective_at.isoformat(),
        "records": records,
    }
    idempotency_key = hashlib.sha256(json.dumps(payload_for_hash, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return MarketDataSnapshotEnvelope(
        source_key=source_key,
        category=category,
        effective_at=effective_at,
        records=records,
        warning_codes=warning_codes,
        anomaly_flags=anomaly_flags,
        metadata=metadata or {},
        connector_version=connector_version,
        idempotency_key=idempotency_key,
    )


def normalize_base_rate_payload(
    *,
    source_key: str,
    payload: dict[str, Any],
    previous_payload: dict[str, Any] | None = None,
    anomaly_jump_threshold_percent: Decimal = Decimal("2.0"),
) -> MarketDataSnapshotEnvelope:
    effective_date = _to_date(payload.get("effective_date"), field_name="effective_date")
    record = BoiBaseRateRecord(
        effective_date=effective_date,
        annual_rate_percent=_to_decimal(payload.get("annual_rate_percent"), field_name="annual_rate_percent"),
        source_key=source_key,
    )
    validate_base_rate_records([record])
    previous_value = None
    if previous_payload:
        previous_records = previous_payload.get("normalized_payload", {}).get("records", [])
        if previous_records:
            previous_value = _to_decimal(previous_records[0].get("annual_rate_percent"), field_name="annual_rate_percent")
    anomaly_flags = detect_single_value_jump(
        current_value=record.annual_rate_percent,
        previous_value=previous_value,
        max_allowed_delta=anomaly_jump_threshold_percent,
        warning_code="LARGE_BASE_RATE_JUMP",
    )
    return _build_envelope(
        source_key=source_key,
        category=MarketDataCategory.BOI_BASE_RATE,
        effective_at=_to_datetime_from_date(effective_date),
        records=[record.model_dump(mode="json")],
        warning_codes=[],
        anomaly_flags=anomaly_flags,
    )


def normalize_mortgage_rate_buckets_payload(
    *,
    source_key: str,
    payload: dict[str, Any],
    previous_payload: dict[str, Any] | None = None,
    anomaly_jump_threshold_percent: Decimal = Decimal("3.0"),
) -> MarketDataSnapshotEnvelope:
    del previous_payload
    effective_date = _to_date(payload.get("effective_date"), field_name="effective_date")
    raw_buckets = payload.get("buckets")
    if not isinstance(raw_buckets, list):
        raise MarketDataParseError("Mortgage-rate bucket payload must contain a 'buckets' list.")

    records: list[MortgageRateBucketRecord] = []
    anomaly_flags: list[str] = []
    for bucket in raw_buckets:
        min_months = int(bucket.get("remaining_months_min"))
        max_months = int(bucket.get("remaining_months_max"))
        record = MortgageRateBucketRecord(
            effective_date=effective_date,
            track_family=str(bucket.get("track_family") or "general"),
            bucket_code=str(
                bucket.get("bucket_code")
                or lookup_mortgage_bucket_by_remaining_months(max(min_months, 1)).bucket_code
            ),
            remaining_months_min=min_months,
            remaining_months_max=max_months,
            annual_rate_percent=_to_decimal(bucket.get("annual_rate_percent"), field_name="annual_rate_percent"),
            source_key=source_key,
        )
        if record.annual_rate_percent > Decimal("15"):
            anomaly_flags.append("HIGH_MORTGAGE_BUCKET_RATE")
        records.append(record)

    validate_mortgage_rate_bucket_records(records)
    return _build_envelope(
        source_key=source_key,
        category=MarketDataCategory.BOI_MORTGAGE_RATE_BUCKETS,
        effective_at=_to_datetime_from_date(effective_date),
        records=[record.model_dump(mode="json") for record in records],
        warning_codes=[],
        anomaly_flags=sorted(set(anomaly_flags)),
        metadata={"anomaly_jump_threshold_percent": str(anomaly_jump_threshold_percent)},
    )


def normalize_cpi_series_payload(
    *,
    source_key: str,
    payload: dict[str, Any],
    previous_payload: dict[str, Any] | None = None,
    anomaly_jump_ratio: Decimal = Decimal("0.08"),
) -> MarketDataSnapshotEnvelope:
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        raise MarketDataParseError("CPI payload must contain a 'records' list.")
    records = [
        CpiRecord(
            period=str(item.get("period")),
            index_value=_to_decimal(item.get("index_value"), field_name="index_value"),
            release_date=_to_date(item.get("release_date"), field_name="release_date"),
            source_key=source_key,
        )
        for item in raw_records
    ]
    validate_cpi_records(records)
    latest = max(records, key=lambda record: record.release_date)
    previous_value = None
    if previous_payload:
        previous_records = previous_payload.get("normalized_payload", {}).get("records", [])
        if previous_records:
            previous_latest = max(previous_records, key=lambda record: record.get("release_date"))
            previous_value = _to_decimal(previous_latest.get("index_value"), field_name="index_value")
    anomaly_flags: list[str] = []
    if previous_value is not None and previous_value > 0:
        relative_change = abs(latest.index_value - previous_value) / previous_value
        if relative_change > anomaly_jump_ratio:
            anomaly_flags.append("LARGE_CPI_JUMP")
    return _build_envelope(
        source_key=source_key,
        category=MarketDataCategory.CPI_SERIES,
        effective_at=_to_datetime_from_date(latest.release_date),
        records=[record.model_dump(mode="json") for record in sorted(records, key=lambda record: record.period)],
        warning_codes=[],
        anomaly_flags=anomaly_flags,
    )


def normalize_inflation_expectations_payload(
    *,
    source_key: str,
    payload: dict[str, Any],
    previous_payload: dict[str, Any] | None = None,
    anomaly_jump_threshold_percent: Decimal = Decimal("4.0"),
) -> MarketDataSnapshotEnvelope:
    del previous_payload
    effective_date = _to_date(payload.get("effective_date"), field_name="effective_date")
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        raise MarketDataParseError("Inflation-expectations payload must contain a 'records' list.")
    records = [
        InflationExpectationRecord(
            horizon_months=int(item.get("horizon_months")),
            expected_inflation_percent=_to_decimal(
                item.get("expected_inflation_percent"),
                field_name="expected_inflation_percent",
            ),
            effective_date=effective_date,
            source_key=source_key,
        )
        for item in raw_records
    ]
    validate_inflation_expectation_records(records)
    anomaly_flags = [
        "HIGH_INFLATION_EXPECTATION"
        for record in records
        if abs(record.expected_inflation_percent) > anomaly_jump_threshold_percent
    ]
    return _build_envelope(
        source_key=source_key,
        category=MarketDataCategory.INFLATION_EXPECTATIONS,
        effective_at=_to_datetime_from_date(effective_date),
        records=[record.model_dump(mode="json") for record in sorted(records, key=lambda record: record.horizon_months)],
        warning_codes=[],
        anomaly_flags=sorted(set(anomaly_flags)),
    )
