from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app import models
from backend.app.dependencies import get_db_manager
from backend.app.managers.database_manager import DataBaseManager


router = APIRouter()


def _alert_view(alert: models.Alert) -> dict:
    return {
        "id": alert.id,
        "title": alert.title,
        "message": alert.message,
        "description": alert.message,
        "severity": alert.severity,
        "category": alert.source or "system",
        "timestamp": alert.created_at.isoformat(),
        "status": alert.status.value,
    }


@router.get("")
async def list_alerts(
    user_id: int,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> dict[str, list[dict]]:
    alerts = await db_manager.list_alerts(user_id=user_id)
    active = [alert for alert in alerts if alert.status == models.AlertStatus.ACTIVE]
    history = [alert for alert in alerts if alert.status == models.AlertStatus.HISTORY]
    dismissed = [alert for alert in alerts if alert.status == models.AlertStatus.DISMISSED]
    return {
        "active": [_alert_view(alert) for alert in active],
        "history": [_alert_view(alert) for alert in history],
        "dismissed": [_alert_view(alert) for alert in dismissed],
    }


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: int,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> dict[str, str]:
    alert = await db_manager.update_alert_status(alert_id, models.AlertStatus.DISMISSED)
    if alert is None:
        return {"status": "not_found"}
    return {"status": "dismissed"}
