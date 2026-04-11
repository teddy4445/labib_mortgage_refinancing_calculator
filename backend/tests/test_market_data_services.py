from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from backend.app import models
from backend.app.domain.exceptions import MarketDataBucketLookupError
from backend.app.domain.market_data.models import MarketDataSourceDefinition, MarketDataCategory
from backend.app.domain.market_data.normalization import normalize_base_rate_payload
from backend.app.infrastructure.market_data.catalog import get_source_definition
from backend.app.infrastructure.market_data.connectors.base import BaseMarketDataConnector
from backend.app.managers.data_gathering_manager import DataGatheringManager
from backend.app.schemas import MortgageInput
from backend.app.services.market_data_service import MarketDataService


class FailingConnector(BaseMarketDataConnector):
    def static_payload(self) -> dict:
        return {}

    def parse_payload(self, payload: dict) -> dict:
        raise RuntimeError("connector failed")


@pytest.mark.anyio
async def test_snapshot_persistence_is_immutable_and_idempotent(market_data_testbed: dict) -> None:
    market_data_service: MarketDataService = market_data_testbed["market_data_service"]
    repository = market_data_testbed["repository"]

    first = await market_data_service.refresh_source("boi_base_rate")
    second = await market_data_service.refresh_source("boi_base_rate")
    source = await repository.find_source_by_key("boi_base_rate")

    assert first.status == "healthy"
    assert first.snapshot_created is True
    assert second.status == "healthy"
    assert second.snapshot_created is False
    assert source is not None
    assert len(source.snapshots) == 1
    payload = source.snapshots[0].payload
    assert "raw_payload" in payload
    assert "normalized_payload" in payload


@pytest.mark.anyio
async def test_query_services_return_latest_market_data_and_support_calculator_integration(market_data_testbed: dict) -> None:
    market_data_service = market_data_testbed["market_data_service"]
    snapshot_service = market_data_testbed["snapshot_service"]
    calculator_manager = market_data_testbed["calculator_manager"]

    await market_data_service.refresh_source("boi_base_rate")
    await market_data_service.refresh_source("cpi_series")
    await market_data_service.refresh_source("boi_mortgage_rate_buckets")
    await market_data_service.refresh_source("inflation_expectations")

    base_rate = await snapshot_service.get_latest_boi_base_rate()
    latest_cpi = await snapshot_service.get_latest_cpi_value()
    specific_cpi = await snapshot_service.get_cpi_for_period("2026-03")
    bucket = await snapshot_service.get_latest_mortgage_rate_bucket(remaining_months=84)
    inflation = await snapshot_service.get_latest_inflation_expectations()
    market_inputs = await snapshot_service.resolve_market_inputs(None)

    assert base_rate.annual_rate_percent == Decimal("4.5")
    assert latest_cpi.index_value == Decimal("115.8")
    assert specific_cpi.period == "2026-03"
    assert bucket.bucket_code == "five_to_ten_years"
    assert inflation[0].horizon_months == 12
    assert market_inputs.boi_base_rate == Decimal("4.5")
    assert market_inputs.current_cpi == Decimal("115.8")
    assert market_inputs.as_of is not None

    summary = calculator_manager.summarize_current_mortgage(
        MortgageInput(
            lender_name="Test Bank",
            property_city="Haifa",
            property_value=Decimal("1500000"),
            current_monthly_payment=Decimal("0"),
            loan_purpose="home",
            occupancy_status="owner",
            tracks=[
                {
                    "label": "Prime",
                    "track_type": "prime_floating",
                    "outstanding_balance": Decimal("300000"),
                    "current_rate": Decimal("5.0"),
                    "remaining_term_months": 240,
                    "bank_margin": Decimal("-0.5"),
                },
                {
                    "label": "Linked",
                    "track_type": "fixed_linked",
                    "outstanding_balance": Decimal("200000"),
                    "current_rate": Decimal("2.0"),
                    "remaining_term_months": 180,
                    "original_cpi": Decimal("92.5"),
                },
            ],
        ),
        market_inputs=market_inputs,
    )
    assert summary.total_monthly_payment > 0
    assert len(summary.track_breakdown) == 2


@pytest.mark.anyio
async def test_status_service_flags_stale_snapshots_correctly(market_data_testbed: dict) -> None:
    repository = market_data_testbed["repository"]
    status_service = market_data_testbed["status_service"]
    definition = get_source_definition("boi_base_rate")

    source = await repository.ensure_source(
        definition=definition,
        status=models.DataSourceStatus.HEALTHY,
        metadata={"enabled": True},
        last_success_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    stale_snapshot = normalize_base_rate_payload(
        source_key="boi_base_rate",
        payload={"effective_date": (datetime.now(timezone.utc) - timedelta(days=10)).date().isoformat(), "annual_rate_percent": "4.0"},
    )
    await repository.persist_snapshot(
        definition=definition,
        source=source,
        raw_payload={"effective_date": stale_snapshot.effective_at.date().isoformat(), "annual_rate_percent": "4.0"},
        normalized_snapshot=stale_snapshot,
    )

    views = await status_service.list_source_status_views()
    base_rate_view = next(view for view in views if view.source_key == "boi_base_rate")

    assert base_rate_view.status == "delayed"
    assert "STALE_SNAPSHOT" in base_rate_view.warning_codes


@pytest.mark.anyio
async def test_refresh_all_reports_partial_failures_without_hiding_successes(market_data_testbed: dict) -> None:
    settings = market_data_testbed["settings"]
    repository = market_data_testbed["repository"]
    analytics_manager = market_data_testbed["analytics_manager"]
    good_service = market_data_testbed["market_data_service"]

    failing_definition = get_source_definition("inflation_expectations")
    connectors = dict(good_service._connectors)
    connectors["inflation_expectations"] = FailingConnector(
        source_definition=failing_definition,
        endpoint=None,
        use_static_fallbacks=True,
        timeout_seconds=20,
    )
    service = MarketDataService(
        settings=settings,
        repository=repository,
        analytics_manager=analytics_manager,
        connectors=connectors,
    )

    batch = await service.refresh_all_market_data()

    assert batch.overall_status == "partial_failure"
    assert any(result.status == "healthy" for result in batch.results)
    assert any(result.status == "failed" for result in batch.results)


@pytest.mark.anyio
async def test_data_gathering_manager_and_status_views_return_structured_results(market_data_testbed: dict) -> None:
    data_gathering_manager = DataGatheringManager(market_data_testbed["market_data_service"])
    status_service = market_data_testbed["status_service"]

    batch = await data_gathering_manager.refresh_all_market_data()
    statuses = await status_service.list_source_status_views()

    assert batch.overall_status == "healthy"
    assert len(batch.results) == 4
    assert len(statuses) == 4
    assert all(status.snapshot_count is not None for status in statuses)


@pytest.mark.anyio
async def test_disabled_source_is_reported_without_fetching(market_data_testbed: dict) -> None:
    settings = market_data_testbed["settings"]
    settings.market_data_enable_inflation_expectations = False
    service = MarketDataService(
        settings=settings,
        repository=market_data_testbed["repository"],
        analytics_manager=market_data_testbed["analytics_manager"],
    )
    status_service = market_data_testbed["status_service"]

    result = await service.refresh_source("inflation_expectations")
    statuses = await status_service.list_source_status_views()
    view = next(item for item in statuses if item.source_key == "inflation_expectations")

    assert result.status == "disabled"
    assert view.status == "disabled"


@pytest.mark.anyio
async def test_missing_mortgage_rate_bucket_raises_clear_error(market_data_testbed: dict) -> None:
    market_data_service = market_data_testbed["market_data_service"]
    snapshot_service = market_data_testbed["snapshot_service"]

    await market_data_service.refresh_source("boi_mortgage_rate_buckets")

    with pytest.raises(MarketDataBucketLookupError):
        await snapshot_service.get_latest_mortgage_rate_bucket(remaining_months=84, track_family="fixed_linked")
