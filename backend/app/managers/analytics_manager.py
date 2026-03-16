from __future__ import annotations

from datetime import date, datetime, timedelta

from backend.app.schemas import AdminMetric, AdminOverviewResponse, AnalyticsEventIn, DataSourceStatusView, SeriesPoint, UserListItem
from backend.app.managers.database_manager import DataBaseManager


class AnalyticsManager:
    def __init__(self, db_manager: DataBaseManager) -> None:
        self._db = db_manager

    async def track_event(self, payload: AnalyticsEventIn) -> None:
        await self._db.log_analytics_event(payload)

    async def track_dropoff(self, *, page: str, session_id: str | None, metadata: dict | None = None) -> None:
        await self.track_event(
            AnalyticsEventIn(
                event_type="wizard_dropoff",
                page=page,
                session_id=session_id,
                metadata=metadata or {},
            )
        )

    async def track_conversion(self, *, page: str, session_id: str | None, source: str | None = None) -> None:
        await self.track_event(
            AnalyticsEventIn(
                event_type="conversion",
                page=page,
                session_id=session_id,
                traffic_source=source,
            )
        )

    async def track_email_failure(self, *, template_name: str, error: str) -> None:
        await self._db.log_error(service="email", category=template_name, message=error)

    async def track_api_health(self, *, source_key: str, ok: bool, error: str | None = None) -> None:
        if not ok:
            await self._db.log_error(service="data_gathering", category=source_key, message=error or "Unknown failure")

    async def capture_exception(self, *, service: str, category: str, error: Exception) -> None:
        await self._db.log_error(service=service, category=category, message=str(error))

    async def admin_overview(self) -> AdminOverviewResponse:
        raw = await self._db.admin_overview()
        today = date.today()

        def build_series(rows: list[tuple]) -> list[SeriesPoint]:
            totals = {row[0]: int(row[1]) for row in rows}
            return [
                SeriesPoint(date=today - timedelta(days=offset), value=totals.get(today - timedelta(days=offset), 0))
                for offset in reversed(range(30))
            ]

        return AdminOverviewResponse(
            metrics=[
                AdminMetric(label="Users", value=raw["metrics"]["users"]),
                AdminMetric(label="Mortgages", value=raw["metrics"]["mortgages"]),
                AdminMetric(label="Open requests", value=raw["metrics"]["open_requests"]),
                AdminMetric(label="Active alerts", value=raw["metrics"]["active_alerts"]),
            ],
            wizard_usage_last_30_days=build_series(raw["wizard_usage"]),
            help_requests_last_30_days=build_series(raw["help_requests"]),
            data_sources=[
                DataSourceStatusView(
                    source_key=source.source_key,
                    display_name=source.display_name,
                    status=source.status.value,
                    last_success_at=source.last_success_at,
                    last_error=source.last_error,
                )
                for source in raw["data_sources"]
            ],
            users=[
                UserListItem(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    phone_number=user.phone_number,
                    status=user.status.value,
                    role=user.role.value,
                    created_at=user.created_at,
                )
                for user in raw["users"]
            ],
        )
