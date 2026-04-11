from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.domain.market_data import derive_source_status_summary
from backend.app.infrastructure.market_data import MarketDataRepository, SOURCE_DEFINITIONS, normalize_source_key
from backend.app.schemas import DataSourceStatusView


class MarketStatusService:
    def __init__(self, repository: MarketDataRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    def _is_enabled(self, source_key: str, source_metadata: dict | None) -> bool:
        definition = SOURCE_DEFINITIONS[source_key]
        if source_metadata and "enabled" in source_metadata:
            return bool(source_metadata["enabled"])
        if definition.enabled_setting_name is None:
            return True
        return bool(getattr(self._settings, definition.enabled_setting_name))

    async def list_source_status_views(self) -> list[DataSourceStatusView]:
        sources = await self._repository.list_sources_with_snapshots()
        indexed = {normalize_source_key(source.source_key): source for source in sources}
        views: list[DataSourceStatusView] = []

        for source_key, definition in SOURCE_DEFINITIONS.items():
            source = indexed.get(source_key)
            latest_payload = None
            latest_snapshot_id = None
            snapshot_count = 0
            if source is not None:
                snapshot_count = len(source.snapshots)
                valid_snapshots = [
                    snapshot for snapshot in source.snapshots if isinstance(snapshot.payload, dict) and snapshot.payload.get("status") == "valid"
                ]
                if valid_snapshots:
                    latest_snapshot = sorted(valid_snapshots, key=lambda item: (item.as_of, item.id), reverse=True)[0]
                    latest_payload = latest_snapshot.payload
                    latest_snapshot_id = latest_snapshot.id

            summary = derive_source_status_summary(
                source_definition=definition,
                source_status=source.status.value if source is not None else None,
                enabled=self._is_enabled(source_key, source.source_metadata if source is not None else None),
                last_success_at=source.last_success_at if source is not None else None,
                last_attempt_at=source.last_attempt_at if source is not None else None,
                last_error=source.last_error if source is not None else None,
                latest_snapshot_id=latest_snapshot_id,
                snapshot_count=snapshot_count,
                latest_snapshot_payload=latest_payload,
            )
            views.append(
                DataSourceStatusView(
                    source_key=summary.source_key,
                    display_name=summary.display_name,
                    status=summary.status,
                    category=summary.category,
                    enabled=summary.enabled,
                    expected_refresh_hours=summary.expected_refresh_hours,
                    snapshot_count=summary.snapshot_count,
                    latest_snapshot_id=summary.latest_snapshot_id,
                    latest_effective_at=summary.latest_effective_at,
                    last_success_at=summary.last_success_at,
                    last_attempt_at=summary.last_attempt_at,
                    last_error=summary.last_error,
                    warning_codes=summary.warning_codes,
                    metadata=summary.metadata,
                )
            )
        return views
