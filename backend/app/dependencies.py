from functools import lru_cache

from backend.app.core.config import Settings, get_settings
from backend.app.core.database import SessionFactory
from backend.app.managers.analytics_manager import AnalyticsManager
from backend.app.managers.calculator_manager import CalculatorManager
from backend.app.managers.data_gathering_manager import DataGatheringManager
from backend.app.managers.database_manager import DataBaseManager
from backend.app.managers.email_manager import EmailManager
from backend.app.managers.security_manager import CaptchaManager, RateLimitManager, ValidationManager
from backend.app.infrastructure.market_data import MarketDataRepository
from backend.app.services.market_data_service import MarketDataService
from backend.app.services.market_snapshot_service import MarketSnapshotService
from backend.app.services.market_status_service import MarketStatusService


@lru_cache
def get_db_manager() -> DataBaseManager:
    return DataBaseManager(SessionFactory)


@lru_cache
def get_analytics_manager() -> AnalyticsManager:
    return AnalyticsManager(get_db_manager())


@lru_cache
def get_email_manager() -> EmailManager:
    return EmailManager(get_settings())


@lru_cache
def get_calculator_manager() -> CalculatorManager:
    return CalculatorManager(get_settings())


@lru_cache
def get_validation_manager() -> ValidationManager:
    return ValidationManager()


@lru_cache
def get_captcha_manager() -> CaptchaManager:
    settings: Settings = get_settings()
    return CaptchaManager(secret_key=settings.captcha_secret_key, verify_url=settings.captcha_verify_url)


@lru_cache
def get_rate_limit_manager() -> RateLimitManager:
    settings = get_settings()
    return RateLimitManager(
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


@lru_cache
def get_data_gathering_manager() -> DataGatheringManager:
    return DataGatheringManager(get_market_data_service())


@lru_cache
def get_market_data_repository() -> MarketDataRepository:
    return MarketDataRepository(get_db_manager())


@lru_cache
def get_market_data_service() -> MarketDataService:
    return MarketDataService(
        settings=get_settings(),
        repository=get_market_data_repository(),
        analytics_manager=get_analytics_manager(),
    )


@lru_cache
def get_market_snapshot_service() -> MarketSnapshotService:
    return MarketSnapshotService(get_market_data_repository())


@lru_cache
def get_market_status_service() -> MarketStatusService:
    return MarketStatusService(get_market_data_repository(), get_settings())
