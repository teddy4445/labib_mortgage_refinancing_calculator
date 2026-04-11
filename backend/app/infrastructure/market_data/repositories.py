from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from backend.app import models
from backend.app.domain.market_data.models import MarketDataSnapshotEnvelope, MarketDataSourceDefinition
from backend.app.managers.database_manager import DataBaseManager


class MarketDataRepository:
    def __init__(self, db_manager: DataBaseManager) -> None:
        self._db = db_manager

    async def ensure_source(
        self,
        *,
        definition: MarketDataSourceDefinition,
        status: models.DataSourceStatus,
        metadata: dict[str, Any] | None = None,
        last_success_at: datetime | None = None,
        last_error: str | None = None,
    ) -> models.MarketDataSource:
        return await self._db.upsert_market_source(
            source_key=definition.source_key,
            display_name=definition.display_name,
            status=status,
            last_success_at=last_success_at,
            last_error=last_error,
            metadata={
                "category": definition.category.value,
                "provider": definition.provider,
                "source_type": definition.source_type,
                "expected_refresh_hours": definition.expected_refresh_hours,
                **(metadata or {}),
            },
        )

    async def find_source_by_key(self, source_key: str) -> models.MarketDataSource | None:
        async with self._db.session_scope() as session:
            result = await session.execute(
                select(models.MarketDataSource)
                .where(models.MarketDataSource.source_key == source_key)
                .options(selectinload(models.MarketDataSource.snapshots))
            )
            return result.scalar_one_or_none()

    async def list_sources_with_snapshots(self) -> list[models.MarketDataSource]:
        async with self._db.session_scope() as session:
            result = await session.execute(
                select(models.MarketDataSource)
                .order_by(models.MarketDataSource.updated_at.desc())
                .options(selectinload(models.MarketDataSource.snapshots))
            )
            return list(result.scalars().all())

    async def get_latest_snapshot_for_source(self, source_key: str) -> models.MarketDataSnapshot | None:
        async with self._db.session_scope() as session:
            source = await session.scalar(
                select(models.MarketDataSource).where(models.MarketDataSource.source_key == source_key)
            )
            if source is None:
                return None
            result = await session.execute(
                select(models.MarketDataSnapshot)
                .where(models.MarketDataSnapshot.source_id == source.id)
                .order_by(models.MarketDataSnapshot.as_of.desc(), models.MarketDataSnapshot.id.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_valid_snapshots_for_source(self, source_key: str) -> list[models.MarketDataSnapshot]:
        async with self._db.session_scope() as session:
            source = await session.scalar(
                select(models.MarketDataSource).where(models.MarketDataSource.source_key == source_key)
            )
            if source is None:
                return []
            result = await session.execute(
                select(models.MarketDataSnapshot)
                .where(models.MarketDataSnapshot.source_id == source.id)
                .order_by(models.MarketDataSnapshot.as_of.desc(), models.MarketDataSnapshot.id.desc())
            )
            snapshots = list(result.scalars().all())
            return [
                snapshot
                for snapshot in snapshots
                if isinstance(snapshot.payload, dict) and snapshot.payload.get("status") == "valid"
            ]

    async def snapshot_count_for_source(self, source_id: int) -> int:
        async with self._db.session_scope() as session:
            count = await session.scalar(
                select(func.count()).select_from(models.MarketDataSnapshot).where(
                    models.MarketDataSnapshot.source_id == source_id
                )
            )
            return int(count or 0)

    async def persist_snapshot(
        self,
        *,
        definition: MarketDataSourceDefinition,
        source: models.MarketDataSource,
        raw_payload: dict[str, Any],
        normalized_snapshot: MarketDataSnapshotEnvelope,
    ) -> tuple[models.MarketDataSnapshot, bool]:
        async with self._db.session_scope() as session:
            existing_rows = await session.execute(
                select(models.MarketDataSnapshot)
                .where(models.MarketDataSnapshot.source_id == source.id)
                .where(models.MarketDataSnapshot.as_of == normalized_snapshot.effective_at)
                .order_by(models.MarketDataSnapshot.id.desc())
            )
            for existing in existing_rows.scalars().all():
                payload = existing.payload if isinstance(existing.payload, dict) else {}
                if payload.get("idempotency_key") == normalized_snapshot.idempotency_key:
                    return existing, False

            snapshot_payload = {
                "source_key": definition.source_key,
                "category": definition.category.value,
                "schema_version": normalized_snapshot.schema_version,
                "connector_version": normalized_snapshot.connector_version,
                "status": normalized_snapshot.status,
                "warning_codes": normalized_snapshot.warning_codes,
                "anomaly_flags": normalized_snapshot.anomaly_flags,
                "metadata": normalized_snapshot.metadata,
                "idempotency_key": normalized_snapshot.idempotency_key,
                "raw_payload": raw_payload,
                "normalized_payload": normalized_snapshot.model_dump(mode="json"),
            }
            snapshot = models.MarketDataSnapshot(
                source_id=source.id,
                as_of=normalized_snapshot.effective_at,
                payload=snapshot_payload,
            )
            session.add(snapshot)
            await session.flush()
            await session.refresh(snapshot)
            return snapshot, True
