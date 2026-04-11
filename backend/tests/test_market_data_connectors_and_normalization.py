from __future__ import annotations

from decimal import Decimal

import pytest

from backend.app.core.config import Settings
from backend.app.domain.exceptions import MarketDataParseError
from backend.app.domain.market_data.normalization import (
    normalize_base_rate_payload,
    normalize_cpi_series_payload,
    normalize_inflation_expectations_payload,
    normalize_mortgage_rate_buckets_payload,
)
from backend.app.domain.market_data.selectors import lookup_mortgage_bucket_by_remaining_months
from backend.app.infrastructure.market_data.catalog import get_source_definition
from backend.app.infrastructure.market_data.connectors import (
    BoiBaseRateConnector,
    CpiSeriesConnector,
    InflationExpectationsConnector,
    MortgageRateBucketsConnector,
)


def _connector(cls, source_key: str):
    return cls(
        source_definition=get_source_definition(source_key),
        endpoint=None,
        use_static_fallbacks=True,
        timeout_seconds=20,
    )


def test_connectors_parse_representative_payloads() -> None:
    base_payload = _connector(BoiBaseRateConnector, "boi_base_rate").parse_payload(
        {"effectiveDate": "2026-04-01", "ratePercent": 4.5}
    )
    bucket_payload = _connector(MortgageRateBucketsConnector, "boi_mortgage_rate_buckets").parse_payload(
        {
            "effectiveDate": "2026-04-01",
            "buckets": [{"bucketCode": "up_to_5_years", "monthsMin": 1, "monthsMax": 60, "annualRatePercent": 4.1}],
        }
    )
    cpi_payload = _connector(CpiSeriesConnector, "cpi_series").parse_payload(
        {"records": [{"period": "2026-03", "indexValue": 115.8, "releaseDate": "2026-04-15"}]}
    )
    inflation_payload = _connector(InflationExpectationsConnector, "inflation_expectations").parse_payload(
        {"effectiveDate": "2026-04-01", "records": [{"horizonMonths": 12, "expectedInflationPercent": 2.6}]}
    )

    assert base_payload["annual_rate_percent"] == 4.5
    assert bucket_payload["buckets"][0]["bucket_code"] == "up_to_5_years"
    assert cpi_payload["records"][0]["period"] == "2026-03"
    assert inflation_payload["records"][0]["horizon_months"] == 12


@pytest.mark.parametrize(
    ("connector_cls", "source_key", "payload"),
    [
        (BoiBaseRateConnector, "boi_base_rate", {"ratePercent": 4.5}),
        (MortgageRateBucketsConnector, "boi_mortgage_rate_buckets", {"effectiveDate": "2026-04-01"}),
        (CpiSeriesConnector, "cpi_series", {"records": [{"period": "2026-03"}]}),
        (InflationExpectationsConnector, "inflation_expectations", {"effectiveDate": "2026-04-01"}),
    ],
)
def test_invalid_connector_payloads_fail_clearly(connector_cls, source_key: str, payload: dict) -> None:
    connector = _connector(connector_cls, source_key)
    with pytest.raises(MarketDataParseError):
        connector.parse_payload(payload)


def test_normalization_maps_provider_payloads_to_canonical_structures() -> None:
    base_snapshot = normalize_base_rate_payload(
        source_key="boi_base_rate",
        payload={"effective_date": "2026-04-01", "annual_rate_percent": "4.5"},
    )
    bucket_snapshot = normalize_mortgage_rate_buckets_payload(
        source_key="boi_mortgage_rate_buckets",
        payload={
            "effective_date": "2026-04-01",
            "buckets": [
                {
                    "bucket_code": "up_to_5_years",
                    "remaining_months_min": 1,
                    "remaining_months_max": 60,
                    "annual_rate_percent": "4.1",
                }
            ],
        },
    )
    cpi_snapshot = normalize_cpi_series_payload(
        source_key="cpi_series",
        payload={"records": [{"period": "2026-03", "index_value": "115.8", "release_date": "2026-04-15"}]},
    )
    inflation_snapshot = normalize_inflation_expectations_payload(
        source_key="inflation_expectations",
        payload={
            "effective_date": "2026-04-01",
            "records": [{"horizon_months": 12, "expected_inflation_percent": "2.6"}],
        },
    )

    assert base_snapshot.records[0]["annual_rate_percent"] == "4.5"
    assert base_snapshot.schema_version == "2026-04-11"
    assert bucket_snapshot.records[0]["bucket_code"] == "up_to_5_years"
    assert cpi_snapshot.records[0]["period"] == "2026-03"
    assert inflation_snapshot.records[0]["horizon_months"] == 12
    assert base_snapshot.idempotency_key


def test_bucket_selector_maps_remaining_months_to_expected_boundaries() -> None:
    assert lookup_mortgage_bucket_by_remaining_months(60).bucket_code == "up_to_5_years"
    assert lookup_mortgage_bucket_by_remaining_months(61).bucket_code == "five_to_ten_years"
    assert lookup_mortgage_bucket_by_remaining_months(360).bucket_code == "twenty_five_to_thirty_years"


def test_settings_load_market_data_controls() -> None:
    settings = Settings(
        _env_file=None,
        market_data_retry_count=4,
        market_data_enable_inflation_expectations=False,
    )

    assert settings.market_data_retry_count == 4
    assert settings.market_data_enable_inflation_expectations is False
