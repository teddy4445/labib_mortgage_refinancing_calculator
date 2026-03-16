from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app import models
from backend.app.dependencies import get_analytics_manager, get_data_gathering_manager, get_db_manager
from backend.app.managers.analytics_manager import AnalyticsManager
from backend.app.managers.data_gathering_manager import DataGatheringManager
from backend.app.managers.database_manager import DataBaseManager


router = APIRouter()


@router.get("/overview")
async def admin_overview(
    analytics_manager: Annotated[AnalyticsManager, Depends(get_analytics_manager)],
) -> dict:
    return (await analytics_manager.admin_overview()).model_dump(mode="json")


@router.post("/data-refresh")
async def run_data_refresh(
    gathering_manager: Annotated[DataGatheringManager, Depends(get_data_gathering_manager)],
) -> dict[str, str]:
    return await gathering_manager.run_daily_refresh()


@router.post("/users/{user_id}/lock")
async def lock_user(
    user_id: int,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> dict[str, str]:
    user = await db_manager.update_user_status(user_id, models.UserStatus.LOCKED)
    if user is None:
        return {"status": "not_found"}
    return {"status": "locked"}
