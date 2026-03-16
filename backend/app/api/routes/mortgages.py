from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from backend.app import models
from backend.app.dependencies import (
    get_analytics_manager,
    get_calculator_manager,
    get_captcha_manager,
    get_db_manager,
    get_rate_limit_manager,
    get_validation_manager,
)
from backend.app.managers.analytics_manager import AnalyticsManager
from backend.app.managers.calculator_manager import CalculatorManager
from backend.app.managers.database_manager import DataBaseManager
from backend.app.managers.security_manager import CaptchaManager, RateLimitManager, ValidationManager
from backend.app.schemas import AnalyticsEventIn, CalculationRequest, CustomerRequestIn, MortgageCreateRequest, MortgageInput


router = APIRouter()


class InterestRequest(CustomerRequestIn):
    captcha_token: str | None = None


@router.post("/calculate/full")
async def calculate_full_refinance(
    payload: CalculationRequest,
    calculator_manager: Annotated[CalculatorManager, Depends(get_calculator_manager)],
    validation_manager: Annotated[ValidationManager, Depends(get_validation_manager)],
) -> dict:
    validation_manager.validate_mortgage(payload.mortgage)
    return calculator_manager.evaluate_refinance(payload).model_dump(mode="json")


@router.post("/calculate/partial")
async def calculate_partial_refinance(
    payload: CalculationRequest,
    calculator_manager: Annotated[CalculatorManager, Depends(get_calculator_manager)],
    validation_manager: Annotated[ValidationManager, Depends(get_validation_manager)],
) -> dict:
    validation_manager.validate_mortgage(payload.mortgage)
    return calculator_manager.evaluate_partial_refinance(payload).model_dump(mode="json")


@router.post("")
async def create_mortgage(
    payload: MortgageCreateRequest,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    validation_manager: Annotated[ValidationManager, Depends(get_validation_manager)],
) -> dict[str, int]:
    validation_manager.validate_mortgage(payload.mortgage)
    user = await db_manager.get_by_id(models.User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    mortgage = await db_manager.create_mortgage(
        user_id=payload.user_id,
        payload=payload.mortgage,
        raw_payload=payload.raw_payload,
    )
    return {"mortgage_id": mortgage.id}


@router.get("/latest")
async def latest_mortgage(
    user_id: int,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> dict:
    mortgage = await db_manager.get_latest_mortgage(user_id)
    if mortgage is None:
        return {"mortgage": None}
    return {
        "mortgage": {
            "id": mortgage.id,
            "user_id": mortgage.user_id,
            "lender_name": mortgage.lender_name,
            "property_city": mortgage.property_city,
            "property_value": float(mortgage.property_value),
            "current_monthly_payment": float(mortgage.current_monthly_payment),
            "loan_purpose": mortgage.loan_purpose,
            "occupancy_status": mortgage.occupancy_status,
            "outstanding_balance_total": float(mortgage.outstanding_balance_total),
            "estimated_refinance_cost": float(mortgage.estimated_refinance_cost),
            "tracks": [
                {
                    "id": track.id,
                    "label": track.label,
                    "track_type": track.track_type,
                    "outstanding_balance": float(track.outstanding_balance),
                    "current_rate": float(track.current_rate),
                    "remaining_term_months": track.remaining_term_months,
                    "linkage_type": track.linkage_type,
                    "rate_type": track.rate_type,
                    "reset_interval": track.reset_interval,
                    "next_reset_date": track.next_reset_date.isoformat() if track.next_reset_date else None,
                    "amortization_method": track.amortization_method,
                    "prepayment_penalty_rule": track.prepayment_penalty_rule,
                }
                for track in mortgage.tracks
            ],
            "raw_payload": mortgage.raw_payload,
            "created_at": mortgage.created_at.isoformat(),
        }
    }


@router.get("/dashboard")
async def dashboard_view(
    user_id: int,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    calculator_manager: Annotated[CalculatorManager, Depends(get_calculator_manager)],
) -> dict:
    mortgage = await db_manager.get_latest_mortgage(user_id)
    if mortgage is None:
        return {"dashboard": None}

    user = await db_manager.get_by_id(models.User, user_id)
    total_balance = mortgage.outstanding_balance_total
    avg_rate = 0.0
    if mortgage.tracks and float(total_balance) > 0:
        weighted = sum(float(track.current_rate) * float(track.outstanding_balance) for track in mortgage.tracks)
        avg_rate = weighted / float(total_balance)

    proposed_rate = max(avg_rate - 0.6, 2.0)
    term_months = max(track.remaining_term_months for track in mortgage.tracks) if mortgage.tracks else 240
    holding_period = user.holding_period_years if user and user.holding_period_years else 8
    calculation_payload = CalculationRequest(
        mortgage=MortgageInput(
            lender_name=mortgage.lender_name,
            property_city=mortgage.property_city,
            property_value=mortgage.property_value,
            current_monthly_payment=mortgage.current_monthly_payment,
            loan_purpose=mortgage.loan_purpose,
            occupancy_status=mortgage.occupancy_status,
            prepayment_fee=0,
            advisor_cost=0,
            tracks=[
                {
                    "label": track.label,
                    "track_type": track.track_type,
                    "outstanding_balance": track.outstanding_balance,
                    "current_rate": track.current_rate,
                    "remaining_term_months": track.remaining_term_months,
                    "linkage_type": track.linkage_type,
                    "rate_type": track.rate_type,
                    "reset_interval": track.reset_interval,
                    "next_reset_date": track.next_reset_date,
                    "amortization_method": track.amortization_method,
                    "prepayment_penalty_rule": track.prepayment_penalty_rule,
                }
                for track in mortgage.tracks
            ],
        ),
        proposed_full_refinance={
            "interest_rate": proposed_rate,
            "term_months": term_months,
            "upfront_costs": mortgage.estimated_refinance_cost,
        },
        holding_period_years=holding_period,
    )
    result = calculator_manager.evaluate_refinance(calculation_payload)
    break_even = result.break_even_month or 0
    urgent = break_even and break_even <= 12
    dashboard = {
        "recommendation": {
            "headline": "מומלץ לשקול מחזור" if result.should_act_now else "מומלץ להמשיך מעקב כרגע",
            "tone": "success" if result.should_act_now else "warning",
            "reason": result.explanation,
        },
        "urgency": {
            "label": "דחיפות גבוהה" if urgent else "דחיפות בינונית" if result.should_act_now else "אין דחיפות מיידית",
            "description": "החיסכון צפוי להתחיל בתוך שנה" if urgent else "נדרש מעקב רציף אחר ריביות ושינויים בשוק",
        },
        "currentMonthlyPayment": float(result.current_monthly_payment),
        "estimatedRefinancePayment": float(result.projected_monthly_payment),
        "projectedNetSavings": float(result.projected_net_savings),
        "breakEvenMonths": break_even,
        "lastAnalysisTime": datetime.utcnow().isoformat(),
    }
    return {"dashboard": dashboard}


@router.post("/requests/interest")
async def create_interest_request(
    payload: InterestRequest,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    analytics_manager: Annotated[AnalyticsManager, Depends(get_analytics_manager)],
    captcha_manager: Annotated[CaptchaManager, Depends(get_captcha_manager)],
    rate_limit_manager: Annotated[RateLimitManager, Depends(get_rate_limit_manager)],
) -> dict[str, str | int]:
    rate_limit_manager.check(
        key=rate_limit_manager.build_key(["interest-request", request.client.host if request.client else "unknown"])
    )
    if not await captcha_manager.verify(payload.captcha_token, request.client.host if request.client else None):
        return {"status": "captcha_failed"}

    customer_request = await db_manager.create_request(payload)
    await analytics_manager.track_conversion(page=payload.source_page or "unknown", session_id=None, source="interest_request")
    return {"status": "forwarded", "request_id": customer_request.id}


@router.post("/analytics/dropoff")
async def track_dropoff(
    payload: AnalyticsEventIn,
    analytics_manager: Annotated[AnalyticsManager, Depends(get_analytics_manager)],
) -> dict[str, str]:
    await analytics_manager.track_dropoff(page=payload.page or "unknown", session_id=payload.session_id, metadata=payload.metadata)
    return {"status": "tracked"}
