from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from backend.app import models
from backend.app.core.config import Settings
from backend.app.managers.analytics_manager import AnalyticsManager
from backend.app.managers.database_manager import DataBaseManager


class DataGatheringManager:
    def __init__(
        self,
        settings: Settings,
        db_manager: DataBaseManager,
        analytics_manager: AnalyticsManager,
    ) -> None:
        self._settings = settings
        self._db = db_manager
        self._analytics = analytics_manager

    async def fetch_json(self, url: str, *, headers: dict[str, str] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def refresh_source(self, source_key: str) -> models.DataSourceStatus:
        display_name = source_key.replace("_", " ").title()
        try:
            payload = {
                "source_key": source_key,
                "fetched_at": datetime.utcnow().isoformat(),
                "status": "mocked",
            }
            source = await self._db.upsert_market_source(
                source_key=source_key,
                display_name=display_name,
                status=models.DataSourceStatus.HEALTHY,
                last_success_at=datetime.utcnow(),
                metadata={"mode": "placeholder"},
            )
            await self._db.add_market_snapshot(source_id=source.id, payload=payload)
            await self._analytics.track_api_health(source_key=source_key, ok=True)
            return models.DataSourceStatus.HEALTHY
        except Exception as exc:
            await self._db.upsert_market_source(
                source_key=source_key,
                display_name=display_name,
                status=models.DataSourceStatus.FAILED,
                last_error=str(exc),
            )
            await self._analytics.track_api_health(source_key=source_key, ok=False, error=str(exc))
            raise

    async def run_daily_refresh(self) -> dict[str, str]:
        results: dict[str, str] = {}
        for source_key in self._settings.market_sources:
            status = await self.refresh_source(source_key)
            results[source_key] = status.value
        return results
