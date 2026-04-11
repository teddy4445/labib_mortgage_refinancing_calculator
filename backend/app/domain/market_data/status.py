from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.app.domain.market_data.freshness import is_snapshot_stale
from backend.app.domain.market_data.models import (
    MarketDataSourceDefinition,
    MarketDataSourceHealth,
    MarketSourceStatusSummary,
)
from backend.app.domain.market_data.selectors import select_snapshot_effective_at


def derive_source_status_summary(
    *,
    source_definition: MarketDataSourceDefinition,
    source_status: str | None,
    enabled: bool,
    last_success_at: datetime | None,
    last_attempt_at: datetime | None,
    last_error: str | None,
    latest_snapshot_id: int | None,
    snapshot_count: int,
    latest_snapshot_payload: dict[str, Any] | None,
    reference_time: datetime | None = None,
) -> MarketSourceStatusSummary:
    now = reference_time or datetime.now(timezone.utc)
    latest_effective_at = select_snapshot_effective_at(latest_snapshot_payload or {}) if latest_snapshot_payload else None
    warning_codes = []

    if not enabled:
        status = MarketDataSourceHealth.DISABLED.value
    elif source_status == "failed":
        status = MarketDataSourceHealth.FAILED.value
    elif latest_snapshot_payload is None:
        status = MarketDataSourceHealth.FAILED.value
        warning_codes.append("NO_VALID_SNAPSHOT")
    elif is_snapshot_stale(
        effective_at=latest_effective_at,
        reference_time=now,
        expected_refresh_hours=source_definition.expected_refresh_hours,
    ):
        status = MarketDataSourceHealth.DELAYED.value
        warning_codes.append("STALE_SNAPSHOT")
    else:
        status = MarketDataSourceHealth.HEALTHY.value

    if latest_snapshot_payload:
        warning_codes.extend(latest_snapshot_payload.get("warning_codes", []))
        warning_codes.extend(latest_snapshot_payload.get("anomaly_flags", []))

    return MarketSourceStatusSummary(
        source_key=source_definition.source_key,
        display_name=source_definition.display_name,
        category=source_definition.category.value,
        status=status,
        enabled=enabled,
        expected_refresh_hours=source_definition.expected_refresh_hours,
        snapshot_count=snapshot_count,
        latest_snapshot_id=latest_snapshot_id,
        latest_effective_at=latest_effective_at,
        last_success_at=last_success_at,
        last_attempt_at=last_attempt_at,
        last_error=last_error,
        warning_codes=sorted(set(warning_codes)),
        metadata={"provider": source_definition.provider, "source_type": source_definition.source_type},
    )
