from __future__ import annotations

from backend.app.domain.market_data.models import MarketDataCategory, MarketDataSourceDefinition


SOURCE_DEFINITIONS = {
    "boi_base_rate": MarketDataSourceDefinition(
        source_key="boi_base_rate",
        display_name="Bank of Israel Base Rate",
        category=MarketDataCategory.BOI_BASE_RATE,
        provider="bank_of_israel",
        source_type="http_json",
        expected_refresh_hours=48,
        endpoint_setting_name="market_data_boi_base_rate_url",
        enabled_setting_name="market_data_enable_boi_base_rate",
        notes="Used for prime-linked current-payment and robustness logic.",
        aliases=("bank_of_israel_rates", "prime_rate"),
    ),
    "boi_mortgage_rate_buckets": MarketDataSourceDefinition(
        source_key="boi_mortgage_rate_buckets",
        display_name="Bank of Israel Mortgage Rate Buckets",
        category=MarketDataCategory.BOI_MORTGAGE_RATE_BUCKETS,
        provider="bank_of_israel",
        source_type="http_json",
        expected_refresh_hours=168,
        endpoint_setting_name="market_data_boi_mortgage_rate_buckets_url",
        enabled_setting_name="market_data_enable_boi_mortgage_rate_buckets",
        notes="Used for remaining-duration market-rate lookup in penalty calculations.",
        aliases=("mortgage_offers_feed",),
    ),
    "cpi_series": MarketDataSourceDefinition(
        source_key="cpi_series",
        display_name="Consumer Price Index Series",
        category=MarketDataCategory.CPI_SERIES,
        provider="central_statistics",
        source_type="http_json",
        expected_refresh_hours=960,
        endpoint_setting_name="market_data_cpi_series_url",
        enabled_setting_name="market_data_enable_cpi_series",
        notes="Latest released CPI used for CPI-linked track adjustment.",
        aliases=("inflation_index",),
    ),
    "inflation_expectations": MarketDataSourceDefinition(
        source_key="inflation_expectations",
        display_name="Inflation Expectations",
        category=MarketDataCategory.INFLATION_EXPECTATIONS,
        provider="market_composite",
        source_type="http_json",
        expected_refresh_hours=168,
        endpoint_setting_name="market_data_inflation_expectations_url",
        enabled_setting_name="market_data_enable_inflation_expectations",
        notes="Used for future scenario and sensitivity work.",
    ),
}

SOURCE_KEY_ALIASES = {
    alias: definition.source_key
    for definition in SOURCE_DEFINITIONS.values()
    for alias in definition.aliases
}


def normalize_source_key(source_key: str) -> str:
    normalized = source_key.strip().lower()
    return SOURCE_KEY_ALIASES.get(normalized, normalized)


def get_source_definition(source_key: str) -> MarketDataSourceDefinition:
    normalized = normalize_source_key(source_key)
    try:
        return SOURCE_DEFINITIONS[normalized]
    except KeyError as exc:
        raise KeyError(f"Unknown market-data source key: {source_key}") from exc
