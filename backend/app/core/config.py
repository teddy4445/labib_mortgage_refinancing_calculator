from functools import lru_cache
from pathlib import Path
from decimal import Decimal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Labib Mortgage Monitor API"
    app_env: str = "development"
    debug: bool = True
    frontend_url: str = "http://localhost:8000"
    api_prefix: str = "/api/v1"
    api_contract_version: str = "2026-04-phase5"

    database_url: str = "sqlite+aiosqlite:///./labib_mortgage.db"

    sendgrid_api_key: str | None = None
    email_from: str = "no-reply@labib.example"
    email_from_name: str = "Labib Mortgage Monitor"
    email_templates_dir: Path = BASE_DIR / "backend" / "app" / "templates" / "email"

    captcha_provider: str = "turnstile"
    captcha_secret_key: str | None = None
    captcha_verify_url: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60

    analytics_enabled: bool = True
    refinance_default_advisor_fee: Decimal = Decimal("7000")
    refinance_default_bank_fee: Decimal = Decimal("3500")
    refinance_default_appraisal_fee: Decimal = Decimal("2500")
    analysis_default_annual_discount_rate: Decimal = Decimal("4.0")
    analysis_prime_modest_annual_increase: Decimal = Decimal("0.25")
    analysis_partial_subset_limit: int = 64
    market_data_use_static_fallbacks: bool = True
    market_data_fetch_timeout_seconds: int = 20
    market_data_retry_count: int = 2
    market_data_enable_boi_base_rate: bool = True
    market_data_enable_boi_mortgage_rate_buckets: bool = True
    market_data_enable_cpi_series: bool = True
    market_data_enable_inflation_expectations: bool = True
    market_data_boi_base_rate_url: str | None = None
    market_data_boi_mortgage_rate_buckets_url: str | None = None
    market_data_cpi_series_url: str | None = None
    market_data_inflation_expectations_url: str | None = None
    market_data_anomaly_base_rate_jump_percent: Decimal = Decimal("2.0")
    market_data_anomaly_bucket_rate_jump_percent: Decimal = Decimal("3.0")
    market_data_anomaly_cpi_jump_ratio: Decimal = Decimal("0.08")
    market_data_anomaly_inflation_jump_percent: Decimal = Decimal("4.0")
    market_sources: list[str] = Field(
        default_factory=lambda: [
            "boi_base_rate",
            "boi_mortgage_rate_buckets",
            "cpi_series",
            "inflation_expectations",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
