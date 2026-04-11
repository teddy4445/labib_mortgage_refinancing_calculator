from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from backend.app import models
from backend.app.api.response_utils import build_response_meta
from backend.app.dependencies import (
    get_analytics_manager,
    get_data_gathering_manager,
    get_db_manager,
    get_market_status_service,
)
from backend.app.managers.analytics_manager import AnalyticsManager
from backend.app.managers.data_gathering_manager import DataGatheringManager
from backend.app.managers.database_manager import DataBaseManager
from backend.app.schemas import (
    AdminLockUserResponse,
    AdminOverviewEnvelope,
    MarketRefreshBatchEnvelope,
    MarketRefreshBatchResponse,
    MarketRefreshResultEnvelope,
    MarketRefreshResultView,
)
from backend.app.services.market_status_service import MarketStatusService


router = APIRouter()


@router.get("/overview", response_model=AdminOverviewEnvelope)
async def admin_overview(
    request: Request,
    analytics_manager: Annotated[AnalyticsManager, Depends(get_analytics_manager)],
    market_status_service: Annotated[MarketStatusService, Depends(get_market_status_service)],
) -> AdminOverviewEnvelope:
    overview = await analytics_manager.admin_overview()
    hydrated = overview.model_copy(update={"data_sources": await market_status_service.list_source_status_views()})
    return AdminOverviewEnvelope(**hydrated.model_dump(mode="python"), meta=build_response_meta(request))


@router.post("/data-refresh", response_model=MarketRefreshBatchEnvelope)
async def run_data_refresh(
    request: Request,
    gathering_manager: Annotated[DataGatheringManager, Depends(get_data_gathering_manager)],
) -> MarketRefreshBatchEnvelope:
    batch = await gathering_manager.refresh_all_market_data()
    response = MarketRefreshBatchResponse(
        overall_status=batch.overall_status,
        refreshed_at=batch.refreshed_at,
        results=[
            MarketRefreshResultView(
                source_key=result.source_key,
                status=result.status,
                snapshot_id=result.snapshot_id,
                snapshot_created=result.snapshot_created,
                effective_at=result.effective_at,
                warning_codes=result.warning_codes,
                anomaly_flags=result.anomaly_flags,
                error=result.error,
            )
            for result in batch.results
        ],
    )
    return MarketRefreshBatchEnvelope(**response.model_dump(mode="python"), meta=build_response_meta(request))


@router.post("/data-refresh/{source_key}", response_model=MarketRefreshResultEnvelope)
async def run_single_source_refresh(
    source_key: str,
    request: Request,
    gathering_manager: Annotated[DataGatheringManager, Depends(get_data_gathering_manager)],
) -> MarketRefreshResultEnvelope:
    result = await gathering_manager.refresh_source(source_key)
    response = MarketRefreshResultView(
        source_key=result.source_key,
        status=result.status,
        snapshot_id=result.snapshot_id,
        snapshot_created=result.snapshot_created,
        effective_at=result.effective_at,
        warning_codes=result.warning_codes,
        anomaly_flags=result.anomaly_flags,
        error=result.error,
    )
    return MarketRefreshResultEnvelope(**response.model_dump(mode="python"), meta=build_response_meta(request))


@router.post("/users/{user_id}/lock", response_model=AdminLockUserResponse)
async def lock_user(
    user_id: int,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> AdminLockUserResponse:
    user = await db_manager.update_user_status(user_id, models.UserStatus.LOCKED)
    if user is None:
        return AdminLockUserResponse(status="not_found", user_id=None, meta=build_response_meta(request))
    return AdminLockUserResponse(status="locked", user_id=user.id, meta=build_response_meta(request))
