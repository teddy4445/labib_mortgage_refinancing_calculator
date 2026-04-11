from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from backend.app.domain.exceptions import MarketDataNotFoundError, MarketDataStaleError
from backend.app.domain.market_data import (
    BoiBaseRateRecord,
    CpiRecord,
    InflationExpectationRecord,
    MortgageRateBucketRecord,
    is_snapshot_stale,
    select_cpi_record_for_period,
    select_latest_valid_snapshot_payload,
    select_snapshot_effective_at,
)
from backend.app.infrastructure.market_data import MarketDataRepository
from backend.app.infrastructure.market_data.catalog import get_source_definition
from backend.app.domain.market_data.selectors import select_bucket_record
from backend.app.schemas import MarketInputs


class MarketSnapshotService:
    def __init__(self, repository: MarketDataRepository) -> None:
        self._repository = repository

    async def _latest_valid_payload(self, source_key: str) -> dict:
        snapshots = await self._repository.get_valid_snapshots_for_source(source_key)
        if not snapshots:
            raise MarketDataNotFoundError(f"No valid snapshots available for source={source_key}")
        payload = select_latest_valid_snapshot_payload(snapshots)
        await self._ensure_not_stale(source_key, payload)
        return payload

    async def _ensure_not_stale(self, source_key: str, payload: dict) -> None:
        definition = get_source_definition(source_key)
        effective_at = select_snapshot_effective_at(payload)
        if is_snapshot_stale(
            effective_at=effective_at,
            reference_time=datetime.now(timezone.utc),
            expected_refresh_hours=definition.expected_refresh_hours,
        ):
            raise MarketDataStaleError(f"Latest snapshot for source={source_key} is stale.")

    async def get_latest_boi_base_rate(self) -> BoiBaseRateRecord:
        payload = await self._latest_valid_payload("boi_base_rate")
        record = payload["normalized_payload"]["records"][0]
        return BoiBaseRateRecord.model_validate(record)

    async def get_latest_cpi_value(self) -> CpiRecord:
        payload = await self._latest_valid_payload("cpi_series")
        records = [CpiRecord.model_validate(record) for record in payload["normalized_payload"]["records"]]
        return max(records, key=lambda record: record.release_date)

    async def get_cpi_for_period(self, period: str) -> CpiRecord:
        payload = await self._latest_valid_payload("cpi_series")
        records = [CpiRecord.model_validate(record) for record in payload["normalized_payload"]["records"]]
        return select_cpi_record_for_period(records, period)

    async def get_latest_mortgage_rate_bucket(
        self,
        *,
        remaining_months: int,
        track_family: str = "general",
    ) -> MortgageRateBucketRecord:
        payload = await self._latest_valid_payload("boi_mortgage_rate_buckets")
        records = [
            MortgageRateBucketRecord.model_validate(record)
            for record in payload["normalized_payload"]["records"]
        ]
        return select_bucket_record(records, remaining_months=remaining_months, track_family=track_family)

    async def get_latest_inflation_expectations(self) -> list[InflationExpectationRecord]:
        payload = await self._latest_valid_payload("inflation_expectations")
        return [
            InflationExpectationRecord.model_validate(record)
            for record in payload["normalized_payload"]["records"]
        ]

    async def resolve_market_inputs(self, provided: MarketInputs | None) -> MarketInputs:
        boi_base_rate = provided.boi_base_rate if provided else None
        current_cpi = provided.current_cpi if provided else None
        as_of = provided.as_of if provided else None

        if boi_base_rate is None:
            try:
                boi_base_rate = (await self.get_latest_boi_base_rate()).annual_rate_percent
            except MarketDataNotFoundError:
                boi_base_rate = None
            except MarketDataStaleError:
                boi_base_rate = None
        if current_cpi is None:
            try:
                current_cpi = (await self.get_latest_cpi_value()).index_value
            except MarketDataNotFoundError:
                current_cpi = None
            except MarketDataStaleError:
                current_cpi = None

        return MarketInputs(
            boi_base_rate=Decimal(str(boi_base_rate)) if boi_base_rate is not None else None,
            current_cpi=Decimal(str(current_cpi)) if current_cpi is not None else None,
            as_of=as_of,
        )
