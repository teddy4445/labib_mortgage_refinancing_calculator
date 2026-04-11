from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from backend.app import models
from backend.app.api.response_utils import build_response_meta
from backend.app.dependencies import get_db_manager
from backend.app.managers.database_manager import DataBaseManager
from backend.app.schemas import AlertDismissResponse, AlertsListResponse, AlertSummaryView, AlertView


router = APIRouter()


def _alert_view(alert: models.Alert) -> AlertView:
    payload = alert.payload if isinstance(alert.payload, dict) else {}
    return AlertView(
        id=alert.id,
        code=payload.get("code") or (alert.source or "system").upper(),
        title=alert.title,
        message=alert.message,
        description=alert.message,
        severity=alert.severity,
        category=alert.source or "system",
        timestamp=alert.created_at,
        status=alert.status.value,
        dismissed=alert.status == models.AlertStatus.DISMISSED,
        explanation_tokens=payload.get("explanation_tokens", []),
        related_mortgage_id=payload.get("mortgage_id"),
        related_analysis_run_id=payload.get("analysis_run_id"),
        action_code=payload.get("action_code"),
        metadata=payload,
    )


def _summary(active: list[models.Alert], history: list[models.Alert], dismissed: list[models.Alert]) -> AlertSummaryView:
    severity_rank = {"high": 3, "warning": 2, "medium": 1, "success": 0}
    top_severity = None
    if active:
        top_severity = max((alert.severity for alert in active), key=lambda item: severity_rank.get(item, 0))
    return AlertSummaryView(
        active_count=len(active),
        history_count=len(history),
        dismissed_count=len(dismissed),
        top_severity=top_severity,
    )


@router.get("", response_model=AlertsListResponse)
async def list_alerts(
    user_id: int,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> AlertsListResponse:
    alerts = await db_manager.list_alerts(user_id=user_id)
    active = [alert for alert in alerts if alert.status == models.AlertStatus.ACTIVE]
    history = [alert for alert in alerts if alert.status == models.AlertStatus.HISTORY]
    dismissed = [alert for alert in alerts if alert.status == models.AlertStatus.DISMISSED]
    return AlertsListResponse(
        active=[_alert_view(alert) for alert in active],
        history=[_alert_view(alert) for alert in history],
        dismissed=[_alert_view(alert) for alert in dismissed],
        summary=_summary(active, history, dismissed),
        meta=build_response_meta(request),
    )


@router.post("/{alert_id}/dismiss", response_model=AlertDismissResponse)
async def dismiss_alert(
    alert_id: int,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> AlertDismissResponse:
    alert = await db_manager.update_alert_status(alert_id, models.AlertStatus.DISMISSED)
    if alert is None:
        return AlertDismissResponse(status="not_found", alert_id=None, meta=build_response_meta(request))
    return AlertDismissResponse(status="dismissed", alert_id=alert.id, meta=build_response_meta(request))
