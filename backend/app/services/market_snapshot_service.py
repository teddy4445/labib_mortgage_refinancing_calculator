from __future__ import annotations

from datetime import date, datetime, timezone
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

    async def get_latest_all_mortgage_rate_buckets(self, *, track_family: str | None = None) -> list[MortgageRateBucketRecord]:
        payload = await self._latest_valid_payload("boi_mortgage_rate_buckets")
        records = [
            MortgageRateBucketRecord.model_validate(record)
            for record in payload["normalized_payload"]["records"]
        ]
        if track_family is None:
            return records
        return [record for record in records if record.track_family == track_family]

    async def get_latest_inflation_expectations(self) -> list[InflationExpectationRecord]:
        payload = await self._latest_valid_payload("inflation_expectations")
        return [
            InflationExpectationRecord.model_validate(record)
            for record in payload["normalized_payload"]["records"]
        ]

    @staticmethod
    def _extract_effective_date(value: object) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    def _resolve_market_inputs_as_of(
        self,
        *,
        explicit_as_of: date | None,
        boi_record: BoiBaseRateRecord | None,
        cpi_record: CpiRecord | None,
        mortgage_rate_buckets: list[object],
    ) -> date | None:
        if explicit_as_of is not None:
            return explicit_as_of

        candidates: list[date] = []
        if boi_record is not None:
            candidates.append(boi_record.effective_date)
        if cpi_record is not None:
            candidates.append(cpi_record.release_date)
        for bucket in mortgage_rate_buckets:
            if isinstance(bucket, MortgageRateBucketRecord):
                candidate = bucket.effective_date
            elif isinstance(bucket, dict):
                candidate = self._extract_effective_date(bucket.get("effective_date"))
            else:
                candidate = self._extract_effective_date(getattr(bucket, "effective_date", None))
            if candidate is not None:
                candidates.append(candidate)
        if not candidates:
            return None
        return max(candidates)

    async def resolve_market_inputs(self, provided: MarketInputs | None) -> MarketInputs:
        boi_base_rate = provided.boi_base_rate if provided else None
        current_cpi = provided.current_cpi if provided else None
        as_of = provided.as_of if provided else None
        mortgage_rate_buckets = list(provided.mortgage_rate_buckets) if provided else []
        boi_record: BoiBaseRateRecord | None = None
        cpi_record: CpiRecord | None = None

        if boi_base_rate is None:
            try:
                boi_record = await self.get_latest_boi_base_rate()
                boi_base_rate = boi_record.annual_rate_percent
            except MarketDataNotFoundError:
                boi_base_rate = None
            except MarketDataStaleError:
                boi_base_rate = None
        if current_cpi is None:
            try:
                cpi_record = await self.get_latest_cpi_value()
                current_cpi = cpi_record.index_value
            except MarketDataNotFoundError:
                current_cpi = None
            except MarketDataStaleError:
                current_cpi = None
        if not mortgage_rate_buckets:
            try:
                mortgage_rate_buckets = [
                    record.model_dump(mode="python")
                    for record in await self.get_latest_all_mortgage_rate_buckets(track_family="general")
                ]
            except MarketDataNotFoundError:
                mortgage_rate_buckets = []
            except MarketDataStaleError:
                mortgage_rate_buckets = []
        resolved_as_of = self._resolve_market_inputs_as_of(
            explicit_as_of=as_of,
            boi_record=boi_record,
            cpi_record=cpi_record,
            mortgage_rate_buckets=mortgage_rate_buckets,
        )

        return MarketInputs(
            boi_base_rate=Decimal(str(boi_base_rate)) if boi_base_rate is not None else None,
            current_cpi=Decimal(str(current_cpi)) if current_cpi is not None else None,
            as_of=resolved_as_of,
            mortgage_rate_buckets=mortgage_rate_buckets,
        )
