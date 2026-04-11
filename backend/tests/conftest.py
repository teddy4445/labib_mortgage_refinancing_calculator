from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app import models as _models  # noqa: F401
from backend.app.core.config import Settings
from backend.app.core.database import Base
from backend.app.infrastructure.market_data import MarketDataRepository
from backend.app.managers.analytics_manager import AnalyticsManager
from backend.app.managers.calculator_manager import CalculatorManager
from backend.app.managers.database_manager import DataBaseManager
from backend.app.managers.data_gathering_manager import DataGatheringManager
from backend.app.managers.email_manager import EmailManager
from backend.app.managers.security_manager import CaptchaManager, RateLimitManager, ValidationManager
from backend.app.services.market_data_service import MarketDataService
from backend.app.services.market_snapshot_service import MarketSnapshotService
from backend.app.services.market_status_service import MarketStatusService


@pytest.fixture
async def market_data_testbed(tmp_path: Path) -> dict:
    db_path = tmp_path / "market_data_test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(
        db_url,
        future=True,
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    settings = Settings(
        _env_file=None,
        database_url=db_url,
        debug=False,
        market_data_use_static_fallbacks=True,
        market_data_retry_count=1,
    )
    db_manager = DataBaseManager(session_factory)
    analytics_manager = AnalyticsManager(db_manager)
    repository = MarketDataRepository(db_manager)
    market_data_service = MarketDataService(
        settings=settings,
        repository=repository,
        analytics_manager=analytics_manager,
    )
    snapshot_service = MarketSnapshotService(repository)
    status_service = MarketStatusService(repository, settings)
    calculator_manager = CalculatorManager(settings)

    try:
        yield {
            "settings": settings,
            "engine": engine,
            "db_manager": db_manager,
            "analytics_manager": analytics_manager,
            "repository": repository,
            "market_data_service": market_data_service,
            "snapshot_service": snapshot_service,
            "status_service": status_service,
            "calculator_manager": calculator_manager,
        }
    finally:
        await engine.dispose()


class DummyEmailManager(EmailManager):
    def __init__(self) -> None:
        self.sent = []

    def send_auth_email(self, to_email: str, verification_link: str, user_name: str) -> None:
        self.sent.append(("auth", to_email, verification_link, user_name))

    def send_password_reset(self, to_email: str, reset_link: str, user_name: str) -> None:
        self.sent.append(("reset", to_email, reset_link, user_name))


@pytest.fixture
async def api_client(market_data_testbed: dict) -> AsyncClient:
    from backend.app.dependencies import (
        get_analytics_manager,
        get_calculator_manager,
        get_captcha_manager,
        get_data_gathering_manager,
        get_db_manager,
        get_email_manager,
        get_market_snapshot_service,
        get_market_status_service,
        get_rate_limit_manager,
        get_validation_manager,
    )
    from backend.app.main import app

    email_manager = DummyEmailManager()
    rate_limit_manager = RateLimitManager(limit=500, window_seconds=60)
    validation_manager = ValidationManager()
    captcha_manager = CaptchaManager(secret_key=None, verify_url="https://example.com/verify")
    data_gathering_manager = DataGatheringManager(market_data_testbed["market_data_service"])

    app.dependency_overrides[get_db_manager] = lambda: market_data_testbed["db_manager"]
    app.dependency_overrides[get_analytics_manager] = lambda: market_data_testbed["analytics_manager"]
    app.dependency_overrides[get_calculator_manager] = lambda: market_data_testbed["calculator_manager"]
    app.dependency_overrides[get_market_snapshot_service] = lambda: market_data_testbed["snapshot_service"]
    app.dependency_overrides[get_market_status_service] = lambda: market_data_testbed["status_service"]
    app.dependency_overrides[get_email_manager] = lambda: email_manager
    app.dependency_overrides[get_rate_limit_manager] = lambda: rate_limit_manager
    app.dependency_overrides[get_validation_manager] = lambda: validation_manager
    app.dependency_overrides[get_captcha_manager] = lambda: captcha_manager
    app.dependency_overrides[get_data_gathering_manager] = lambda: data_gathering_manager

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
