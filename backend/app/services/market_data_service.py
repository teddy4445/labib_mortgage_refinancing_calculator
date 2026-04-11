from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from backend.app import models
from backend.app.core.config import Settings
from backend.app.domain.exceptions import MarketDataError, MarketDataFetchError
from backend.app.domain.market_data.models import MarketDataSnapshotEnvelope
from backend.app.domain.market_data.normalization import (
    normalize_base_rate_payload,
    normalize_cpi_series_payload,
    normalize_inflation_expectations_payload,
    normalize_mortgage_rate_buckets_payload,
)
from backend.app.infrastructure.market_data import MarketDataRepository, get_source_definition, normalize_source_key
from backend.app.infrastructure.market_data.connectors import (
    BaseMarketDataConnector,
    BoiBaseRateConnector,
    CpiSeriesConnector,
    InflationExpectationsConnector,
    MortgageRateBucketsConnector,
)
from backend.app.managers.analytics_manager import AnalyticsManager


@dataclass(frozen=True)
class MarketDataRefreshResult:
    source_key: str
    status: str
    snapshot_id: int | None = None
    snapshot_created: bool = False
    effective_at: datetime | None = None
    warning_codes: list[str] = field(default_factory=list)
    anomaly_flags: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class MarketDataRefreshBatchResult:
    overall_status: str
    refreshed_at: datetime
    results: list[MarketDataRefreshResult] = field(default_factory=list)


class MarketDataService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: MarketDataRepository,
        analytics_manager: AnalyticsManager,
        connectors: dict[str, BaseMarketDataConnector] | None = None,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._analytics = analytics_manager
        self._connectors = connectors or self._build_default_connectors()

    def _build_default_connectors(self) -> dict[str, BaseMarketDataConnector]:
        return {
            "boi_base_rate": BoiBaseRateConnector(
                source_definition=get_source_definition("boi_base_rate"),
                endpoint=self._settings.market_data_boi_base_rate_url,
                use_static_fallbacks=self._settings.market_data_use_static_fallbacks,
                timeout_seconds=self._settings.market_data_fetch_timeout_seconds,
            ),
            "boi_mortgage_rate_buckets": MortgageRateBucketsConnector(
                source_definition=get_source_definition("boi_mortgage_rate_buckets"),
                endpoint=self._settings.market_data_boi_mortgage_rate_buckets_url,
                use_static_fallbacks=self._settings.market_data_use_static_fallbacks,
                timeout_seconds=self._settings.market_data_fetch_timeout_seconds,
            ),
            "cpi_series": CpiSeriesConnector(
                source_definition=get_source_definition("cpi_series"),
                endpoint=self._settings.market_data_cpi_series_url,
                use_static_fallbacks=self._settings.market_data_use_static_fallbacks,
                timeout_seconds=self._settings.market_data_fetch_timeout_seconds,
            ),
            "inflation_expectations": InflationExpectationsConnector(
                source_definition=get_source_definition("inflation_expectations"),
                endpoint=self._settings.market_data_inflation_expectations_url,
                use_static_fallbacks=self._settings.market_data_use_static_fallbacks,
                timeout_seconds=self._settings.market_data_fetch_timeout_seconds,
            ),
        }

    def _is_source_enabled(self, source_key: str) -> bool:
        definition = get_source_definition(source_key)
        if definition.enabled_setting_name is None:
            return True
        return bool(getattr(self._settings, definition.enabled_setting_name))

    async def _previous_snapshot_payload(self, source_key: str) -> dict | None:
        latest = await self._repository.get_latest_snapshot_for_source(source_key)
        if latest is None or not isinstance(latest.payload, dict):
            return None
        return latest.payload

    def _normalize_payload(
        self,
        *,
        source_key: str,
        parsed_payload: dict,
        previous_payload: dict | None,
    ) -> MarketDataSnapshotEnvelope:
        normalized_key = normalize_source_key(source_key)
        if normalized_key == "boi_base_rate":
            return normalize_base_rate_payload(
                source_key=normalized_key,
                payload=parsed_payload,
                previous_payload=previous_payload,
                anomaly_jump_threshold_percent=self._settings.market_data_anomaly_base_rate_jump_percent,
            )
        if normalized_key == "boi_mortgage_rate_buckets":
            return normalize_mortgage_rate_buckets_payload(
                source_key=normalized_key,
                payload=parsed_payload,
                previous_payload=previous_payload,
                anomaly_jump_threshold_percent=self._settings.market_data_anomaly_bucket_rate_jump_percent,
            )
        if normalized_key == "cpi_series":
            return normalize_cpi_series_payload(
                source_key=normalized_key,
                payload=parsed_payload,
                previous_payload=previous_payload,
                anomaly_jump_ratio=self._settings.market_data_anomaly_cpi_jump_ratio,
            )
        if normalized_key == "inflation_expectations":
            return normalize_inflation_expectations_payload(
                source_key=normalized_key,
                payload=parsed_payload,
                previous_payload=previous_payload,
                anomaly_jump_threshold_percent=self._settings.market_data_anomaly_inflation_jump_percent,
            )
        raise MarketDataFetchError(f"No normalization strategy configured for {source_key}")

    async def refresh_source(self, source_key: str) -> MarketDataRefreshResult:
        normalized_key = normalize_source_key(source_key)
        definition = get_source_definition(normalized_key)
        connector = self._connectors[definition.source_key]

        if not self._is_source_enabled(definition.source_key):
            await self._repository.ensure_source(
                definition=definition,
                status=models.DataSourceStatus.DELAYED,
                metadata={"enabled": False},
                last_error=None,
            )
            return MarketDataRefreshResult(source_key=definition.source_key, status="disabled")

        try:
            previous_payload = await self._previous_snapshot_payload(definition.source_key)
            raw_payload = None
            last_exc: Exception | None = None
            for _attempt in range(self._settings.market_data_retry_count + 1):
                try:
                    raw_payload = await connector.fetch_payload()
                    last_exc = None
                    break
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
            if raw_payload is None:
                assert last_exc is not None
                raise last_exc
            normalized_snapshot = self._normalize_payload(
                source_key=definition.source_key,
                parsed_payload=raw_payload,
                previous_payload=previous_payload,
            )
            source = await self._repository.ensure_source(
                definition=definition,
                status=models.DataSourceStatus.HEALTHY,
                metadata={
                    "enabled": True,
                    "latest_effective_at": normalized_snapshot.effective_at.isoformat(),
                },
                last_success_at=datetime.now(timezone.utc),
                last_error=None,
            )
            snapshot, created = await self._repository.persist_snapshot(
                definition=definition,
                source=source,
                raw_payload=raw_payload,
                normalized_snapshot=normalized_snapshot,
            )
            await self._analytics.track_api_health(source_key=definition.source_key, ok=True)
            return MarketDataRefreshResult(
                source_key=definition.source_key,
                status="healthy",
                snapshot_id=snapshot.id,
                snapshot_created=created,
                effective_at=normalized_snapshot.effective_at,
                warning_codes=normalized_snapshot.warning_codes,
                anomaly_flags=normalized_snapshot.anomaly_flags,
            )
        except Exception as exc:  # noqa: BLE001
            await self._repository.ensure_source(
                definition=definition,
                status=models.DataSourceStatus.FAILED,
                metadata={"enabled": True},
                last_error=str(exc),
            )
            await self._analytics.track_api_health(source_key=definition.source_key, ok=False, error=str(exc))
            return MarketDataRefreshResult(
                source_key=definition.source_key,
                status="failed",
                error=str(exc),
            )

    async def refresh_all_market_data(self) -> MarketDataRefreshBatchResult:
        results: list[MarketDataRefreshResult] = []
        for source_key in self._settings.market_sources:
            results.append(await self.refresh_source(source_key))

        failed_count = sum(1 for result in results if result.status == "failed")
        if failed_count == 0:
            overall_status = "healthy"
        elif failed_count == len(results):
            overall_status = "failed"
        else:
            overall_status = "partial_failure"

        return MarketDataRefreshBatchResult(
            overall_status=overall_status,
            refreshed_at=datetime.now(timezone.utc),
            results=results,
        )
