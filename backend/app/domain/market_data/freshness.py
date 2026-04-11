from __future__ import annotations

from datetime import datetime, timedelta, timezone


def is_snapshot_stale(
    *,
    effective_at: datetime | None,
    reference_time: datetime,
    expected_refresh_hours: int,
) -> bool:
    if effective_at is None:
        return True
    effective = effective_at if effective_at.tzinfo is not None else effective_at.replace(tzinfo=timezone.utc)
    reference = reference_time if reference_time.tzinfo is not None else reference_time.replace(tzinfo=timezone.utc)
    return reference - effective > timedelta(hours=expected_refresh_hours)
