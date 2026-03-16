from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Labib Mortgage Monitor API"
    app_env: str = "development"
    debug: bool = True
    frontend_url: str = "http://localhost:8000"
    api_prefix: str = "/api/v1"

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
    market_sources: list[str] = Field(
        default_factory=lambda: [
            "bank_of_israel_rates",
            "inflation_index",
            "prime_rate",
            "mortgage_offers_feed",
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
