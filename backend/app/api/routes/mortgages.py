from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.app import models
from backend.app.api.response_utils import build_response_meta
from backend.app.dependencies import (
    get_analytics_manager,
    get_calculator_manager,
    get_captcha_manager,
    get_db_manager,
    get_market_snapshot_service,
    get_market_status_service,
    get_rate_limit_manager,
    get_validation_manager,
)
from backend.app.domain.exceptions import DomainError
from backend.app.managers.analytics_manager import AnalyticsManager
from backend.app.managers.calculator_manager import CalculatorManager
from backend.app.managers.database_manager import DataBaseManager
from backend.app.managers.security_manager import CaptchaManager, RateLimitManager, ValidationManager
from backend.app.schemas import (
    AlertSummaryView,
    AnalysisReadinessView,
    AnalysisSnapshotSummaryView,
    AnalyticsAckResponse,
    AnalyticsEventIn,
    CalculationRequest,
    CurrentMortgageSummary,
    CustomerRequestIn,
    DashboardAnalysisMetaView,
    DashboardRecommendationView,
    DashboardResponse,
    DashboardUrgencyView,
    DashboardView,
    InterestRequestIn,
    InterestRequestResponse,
    LatestMortgageResponse,
    MarketFreshnessSummaryView,
    MarketInputs,
    MortgageCreateRequest,
    MortgageCreateResponse,
    MortgageInput,
    MortgageSummaryView,
    MortgageTrackView,
    PendingFollowupRequestView,
    RecommendationResult,
)
from backend.app.services.market_snapshot_service import MarketSnapshotService
from backend.app.services.market_status_service import MarketStatusService


router = APIRouter()


class InterestRequestPayload(InterestRequestIn):
    captcha_token: str | None = None


def _extract_market_inputs(raw_payload: dict[str, Any] | None) -> MarketInputs | None:
    if not raw_payload:
        return None

    market_inputs = raw_payload.get("market_inputs")
    if isinstance(market_inputs, dict):
        return MarketInputs(**market_inputs)

    boi_base_rate = raw_payload.get("boi_base_rate")
    current_cpi = raw_payload.get("current_cpi")
    if boi_base_rate is None and current_cpi is None:
        return None
    return MarketInputs(boi_base_rate=boi_base_rate, current_cpi=current_cpi)


def _raw_track_details(raw_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not raw_payload:
        return {}

    details: dict[str, dict[str, Any]] = {}
    tracks = raw_payload.get("tracks")
    if not isinstance(tracks, list):
        return details

    for track in tracks:
        if not isinstance(track, dict):
            continue
        label = track.get("label") or track.get("name")
        if label:
            details[str(label)] = track
    return details


def _dashboard_headline(recommendation_code: str) -> tuple[str, str]:
    mapping = {
        "CONSIDER_PARTIAL_REFINANCE": ("Partial refinance looks worthwhile", "success"),
        "CONSIDER_FULL_REFINANCE": ("Full refinance looks worthwhile", "success"),
        "KEEP_CURRENT": ("Keeping the current mortgage is preferable for now", "warning"),
    }
    return mapping.get(recommendation_code, ("Analysis completed", "warning"))


def _dashboard_reason(tokens: list[str]) -> str:
    if "PARTIAL_REFI_OUTPERFORMS_FULL" in tokens:
        return "A selective track refinance currently outperforms both status quo and full refinance."
    if "BENEFICIAL_UNDER_BOTH_RATE_SCENARIOS" in tokens:
        return "The recommendation remains favorable under both stable and modestly rising Bank of Israel rate paths."
    if "KEEPING_CURRENT_IS_PREFERRED" in tokens:
        return "Current savings, costs, and robustness do not support acting now."
    if "POSITIVE_NPV" in tokens and "FAST_BREAK_EVEN" in tokens:
        return "Projected savings are positive, discounted value remains favorable, and break-even is relatively quick."
    if "LOWER_PAYMENT" in tokens:
        return "Projected monthly payment decreases compared with the current mortgage."
    return "The recommendation is based on payment, cost, break-even, NPV, and rate-path robustness comparisons."


def _analysis_readiness(
    *,
    mortgage: models.Mortgage,
    raw_track_details: dict[str, dict[str, Any]],
    market_inputs: MarketInputs | None,
) -> AnalysisReadinessView:
    missing_flags: list[str] = []

    has_prime_track = any(track.track_type == "prime_floating" for track in mortgage.tracks)
    if has_prime_track and (market_inputs is None or market_inputs.boi_base_rate is None):
        missing_flags.append("MISSING_BOI_BASE_RATE")

    has_linked_track = any(track.track_type in {"fixed_linked", "adjustable_linked"} for track in mortgage.tracks)
    if has_linked_track and (market_inputs is None or market_inputs.current_cpi is None):
        missing_flags.append("MISSING_CURRENT_CPI")

    for track in mortgage.tracks:
        if track.track_type in {"fixed_linked", "adjustable_linked"}:
            raw = raw_track_details.get(track.label, {})
            original_cpi = raw.get("originalCpi") or raw.get("original_cpi")
            if original_cpi in (None, ""):
                missing_flags.append(f"MISSING_ORIGINAL_CPI:{track.label}")

        if track.track_type == "prime_floating":
            raw = raw_track_details.get(track.label, {})
            bank_margin = raw.get("bankMargin") or raw.get("bank_margin")
            if bank_margin in (None, ""):
                missing_flags.append(f"MISSING_BANK_MARGIN:{track.label}")

    return AnalysisReadinessView(
        ready=not missing_flags,
        missing_data_flags=missing_flags,
        warning_codes=[],
    )


def _analysis_summary_from_run(run: models.AnalysisRun | None) -> AnalysisSnapshotSummaryView | None:
    if run is None:
        return None
    return AnalysisSnapshotSummaryView(
        analysis_run_id=run.id,
        recommendation_code=run.recommendation_type,
        should_act_now=run.should_act_now,
        break_even_month=run.break_even_month,
        projected_net_savings=run.projected_net_savings,
        created_at=run.created_at,
        source="persisted_analysis_run",
    )


def _runtime_analysis_summary(result: RecommendationResult) -> AnalysisSnapshotSummaryView:
    recommendation_code = (
        result.recommendation_summary.recommendation_code
        if result.recommendation_summary is not None
        else result.explanation
    )
    return AnalysisSnapshotSummaryView(
        analysis_run_id=None,
        recommendation_code=recommendation_code,
        should_act_now=result.should_act_now,
        break_even_month=result.break_even_month,
        projected_net_savings=result.projected_net_savings,
        created_at=result.calculated_at or datetime.now(timezone.utc),
        source="runtime_recalculation",
    )


def _mortgage_track_view(track: models.MortgageTrack) -> MortgageTrackView:
    return MortgageTrackView(
        id=track.id,
        label=track.label,
        track_type=track.track_type,
        outstanding_balance=float(track.outstanding_balance),
        current_rate=float(track.current_rate) if track.current_rate is not None else None,
        remaining_term_months=track.remaining_term_months,
        linkage_type=track.linkage_type,
        rate_type=track.rate_type,
        reset_interval=track.reset_interval,
        next_reset_date=track.next_reset_date.isoformat() if track.next_reset_date else None,
        amortization_method=track.amortization_method,
        prepayment_penalty_rule=track.prepayment_penalty_rule,
    )


def _mortgage_summary_view(
    *,
    mortgage: models.Mortgage,
    readiness: AnalysisReadinessView,
    latest_analysis_summary: AnalysisSnapshotSummaryView | None,
    market_inputs: MarketInputs | None,
) -> MortgageSummaryView:
    normalized_values = {
        "track_count": len(mortgage.tracks),
        "market_inputs": market_inputs.model_dump(mode="json") if market_inputs is not None else None,
    }
    return MortgageSummaryView(
        id=mortgage.id,
        user_id=mortgage.user_id,
        lender_name=mortgage.lender_name,
        property_city=mortgage.property_city,
        property_value=float(mortgage.property_value),
        current_monthly_payment=float(mortgage.current_monthly_payment),
        loan_purpose=mortgage.loan_purpose,
        occupancy_status=mortgage.occupancy_status,
        outstanding_balance_total=float(mortgage.outstanding_balance_total),
        estimated_refinance_cost=float(mortgage.estimated_refinance_cost),
        tracks=[_mortgage_track_view(track) for track in mortgage.tracks],
        raw_payload=mortgage.raw_payload if isinstance(mortgage.raw_payload, dict) else {},
        created_at=mortgage.created_at,
        updated_at=mortgage.updated_at,
        normalized_values=normalized_values,
        analysis_readiness=readiness,
        latest_analysis_summary=latest_analysis_summary,
    )


def _alert_summary(alerts: list[models.Alert]) -> AlertSummaryView:
    active = [alert for alert in alerts if alert.status == models.AlertStatus.ACTIVE]
    history = [alert for alert in alerts if alert.status == models.AlertStatus.HISTORY]
    dismissed = [alert for alert in alerts if alert.status == models.AlertStatus.DISMISSED]
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


def _market_freshness_summary(status_views: list[Any]) -> MarketFreshnessSummaryView:
    healthy = sum(1 for item in status_views if item.status == "healthy")
    delayed = sum(1 for item in status_views if item.status == "delayed")
    failed = sum(1 for item in status_views if item.status == "failed")
    latest_success = None
    warning_codes: list[str] = []

    for item in status_views:
        if item.last_success_at and (latest_success is None or item.last_success_at > latest_success):
            latest_success = item.last_success_at
        warning_codes.extend(item.warning_codes)

    if failed:
        status_code = "failed"
    elif delayed:
        status_code = "delayed"
    else:
        status_code = "healthy"

    return MarketFreshnessSummaryView(
        status=status_code,
        healthy_sources=healthy,
        delayed_sources=delayed,
        failed_sources=failed,
        latest_success_at=latest_success,
        warning_codes=sorted(set(warning_codes)),
    )


def _pending_followup_request_view(
    request_item: models.CustomerRequest | None,
    *,
    mortgage_id: int,
) -> PendingFollowupRequestView:
    if request_item is None:
        return PendingFollowupRequestView(exists=False)

    details = request_item.details if isinstance(request_item.details, dict) else {}
    return PendingFollowupRequestView(
        exists=True,
        request_id=request_item.id,
        status=request_item.status.value,
        created_at=request_item.created_at,
        mortgage_id=details.get("mortgage_id", mortgage_id),
        analysis_run_id=details.get("analysis_run_id"),
        request_type=request_item.request_type,
        source_page=request_item.source_page,
    )


def _build_dashboard_response(
    *,
    mortgage_summary: MortgageSummaryView,
    result: RecommendationResult | None,
    persisted_analysis_summary: AnalysisSnapshotSummaryView | None,
    alert_summary: AlertSummaryView,
    freshness_summary: MarketFreshnessSummaryView,
    pending_request: PendingFollowupRequestView,
    market_inputs: MarketInputs | None,
    calculated_at: datetime,
) -> DashboardView:
    if result is None:
        latest_analysis_summary = persisted_analysis_summary or AnalysisSnapshotSummaryView(
            analysis_run_id=None,
            recommendation_code="ANALYSIS_UNAVAILABLE",
            should_act_now=False,
            break_even_month=None,
            projected_net_savings=Decimal("0"),
            created_at=calculated_at,
            source="runtime_recalculation",
        )
        return DashboardView(
            recommendation=DashboardRecommendationView(
                headline="Analysis unavailable",
                tone="warning",
                reason="Current mortgage payment could not be recomputed because required market inputs are missing.",
                recommendation_code="ANALYSIS_UNAVAILABLE",
            ),
            urgency=DashboardUrgencyView(
                label="No immediate urgency",
                description="Complete missing mortgage or market inputs before relying on the recommendation.",
                code="INSUFFICIENT_DATA",
            ),
            currentMonthlyPayment=mortgage_summary.current_monthly_payment,
            estimatedRefinancePayment=mortgage_summary.current_monthly_payment,
            projectedNetSavings=0.0,
            breakEvenMonths=0,
            lastAnalysisTime=calculated_at,
            currentSummary=None,
            recommendationSummary=None,
            scenarios=[],
            explanationTokens=["LOW_CONFIDENCE_INPUTS"],
            riskFlags=["LOW_CONFIDENCE_INPUTS"],
            analysisVersion=None,
            mortgageSummary=mortgage_summary,
            latestAnalysisSummary=latest_analysis_summary,
            hasBetterOption=False,
            topExplanationTokens=["LOW_CONFIDENCE_INPUTS"],
            topRiskFlags=["LOW_CONFIDENCE_INPUTS"],
            alertSummary=alert_summary,
            marketDataFreshness=freshness_summary,
            pendingFollowUpRequest=pending_request,
            analysisMeta=DashboardAnalysisMetaView(
                source="runtime_recalculation",
                engine_version=None,
                calculated_at=calculated_at,
                market_as_of=market_inputs.as_of if market_inputs is not None else None,
            ),
        )

    recommendation_code = (
        result.recommendation_summary.recommendation_code
        if result.recommendation_summary is not None
        else result.explanation
    )
    headline, tone = _dashboard_headline(recommendation_code)
    recommendation_reason = _dashboard_reason(result.explanation_tokens)
    break_even = result.break_even_month or 0
    urgent = bool(break_even and break_even <= 12)
    should_act_now = result.should_act_now
    latest_analysis_summary = _runtime_analysis_summary(result)

    return DashboardView(
        recommendation=DashboardRecommendationView(
            headline=headline,
            tone=tone,
            reason=recommendation_reason,
            recommendation_code=recommendation_code,
        ),
        urgency=DashboardUrgencyView(
            label="High urgency" if urgent else "Moderate urgency" if should_act_now else "No immediate urgency",
            description="Break-even is relatively short."
            if urgent
            else "The recommendation should be weighed against the user's holding period and preferences.",
            code="HIGH_URGENCY" if urgent else "REVIEW_SOON" if should_act_now else "NO_IMMEDIATE_URGENCY",
        ),
        currentMonthlyPayment=float(result.current_summary.total_monthly_payment) if result.current_summary else float(result.current_monthly_payment),
        estimatedRefinancePayment=float(result.projected_monthly_payment),
        projectedNetSavings=float(result.projected_net_savings),
        breakEvenMonths=break_even,
        lastAnalysisTime=result.calculated_at or calculated_at,
        currentSummary=result.current_summary,
        recommendationSummary=result.recommendation_summary,
        scenarios=result.scenarios,
        explanationTokens=result.explanation_tokens,
        riskFlags=result.risk_flags,
        analysisVersion=result.assumptions.get("engine_version"),
        mortgageSummary=mortgage_summary,
        latestAnalysisSummary=latest_analysis_summary,
        hasBetterOption=result.found_better_alternative,
        topExplanationTokens=result.explanation_tokens[:5],
        topRiskFlags=result.risk_flags[:5],
        alertSummary=alert_summary,
        marketDataFreshness=freshness_summary,
        pendingFollowUpRequest=pending_request,
        analysisMeta=DashboardAnalysisMetaView(
            source="runtime_recalculation",
            engine_version=result.assumptions.get("engine_version"),
            calculated_at=result.calculated_at or calculated_at,
            market_as_of=market_inputs.as_of if market_inputs is not None else None,
        ),
    )


@router.post("/calculate/full", response_model=RecommendationResult)
async def calculate_full_refinance(
    payload: CalculationRequest,
    request: Request,
    calculator_manager: Annotated[CalculatorManager, Depends(get_calculator_manager)],
    market_snapshot_service: Annotated[MarketSnapshotService, Depends(get_market_snapshot_service)],
    validation_manager: Annotated[ValidationManager, Depends(get_validation_manager)],
) -> RecommendationResult:
    validation_manager.validate_mortgage(payload.mortgage)
    enriched_payload = payload.model_copy(
        update={"market_inputs": await market_snapshot_service.resolve_market_inputs(payload.market_inputs)}
    )
    result = calculator_manager.evaluate_refinance(enriched_payload)
    return result.model_copy(update={"meta": build_response_meta(request)})


@router.post("/calculate/partial", response_model=RecommendationResult)
async def calculate_partial_refinance(
    payload: CalculationRequest,
    request: Request,
    calculator_manager: Annotated[CalculatorManager, Depends(get_calculator_manager)],
    market_snapshot_service: Annotated[MarketSnapshotService, Depends(get_market_snapshot_service)],
    validation_manager: Annotated[ValidationManager, Depends(get_validation_manager)],
) -> RecommendationResult:
    validation_manager.validate_mortgage(payload.mortgage)
    enriched_payload = payload.model_copy(
        update={"market_inputs": await market_snapshot_service.resolve_market_inputs(payload.market_inputs)}
    )
    result = calculator_manager.evaluate_partial_refinance(enriched_payload)
    return result.model_copy(update={"meta": build_response_meta(request)})


@router.post("", response_model=MortgageCreateResponse)
async def create_mortgage(
    payload: MortgageCreateRequest,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    validation_manager: Annotated[ValidationManager, Depends(get_validation_manager)],
) -> MortgageCreateResponse:
    validation_manager.validate_mortgage(payload.mortgage)
    user = await db_manager.get_by_id(models.User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    mortgage = await db_manager.create_mortgage(
        user_id=payload.user_id,
        payload=payload.mortgage,
        raw_payload=payload.raw_payload,
    )
    return MortgageCreateResponse(mortgage_id=mortgage.id, meta=build_response_meta(request))


@router.get("/latest", response_model=LatestMortgageResponse)
async def latest_mortgage(
    user_id: int,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    market_snapshot_service: Annotated[MarketSnapshotService, Depends(get_market_snapshot_service)],
) -> LatestMortgageResponse:
    mortgage = await db_manager.get_latest_mortgage(user_id)
    if mortgage is None:
        return LatestMortgageResponse(mortgage=None, meta=build_response_meta(request))

    raw_payload = mortgage.raw_payload if isinstance(mortgage.raw_payload, dict) else {}
    raw_track_details = _raw_track_details(raw_payload)
    market_inputs = await market_snapshot_service.resolve_market_inputs(_extract_market_inputs(raw_payload))
    readiness = _analysis_readiness(mortgage=mortgage, raw_track_details=raw_track_details, market_inputs=market_inputs)
    latest_analysis = _analysis_summary_from_run(await db_manager.get_latest_analysis_run(mortgage.id))
    mortgage_summary = _mortgage_summary_view(
        mortgage=mortgage,
        readiness=readiness,
        latest_analysis_summary=latest_analysis,
        market_inputs=market_inputs,
    )
    return LatestMortgageResponse(mortgage=mortgage_summary, meta=build_response_meta(request))


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard_view(
    user_id: int,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    calculator_manager: Annotated[CalculatorManager, Depends(get_calculator_manager)],
    market_snapshot_service: Annotated[MarketSnapshotService, Depends(get_market_snapshot_service)],
    market_status_service: Annotated[MarketStatusService, Depends(get_market_status_service)],
) -> DashboardResponse:
    mortgage = await db_manager.get_latest_mortgage(user_id)
    if mortgage is None:
        return DashboardResponse(dashboard=None, meta=build_response_meta(request))

    user = await db_manager.get_by_id(models.User, user_id)
    raw_payload = mortgage.raw_payload if isinstance(mortgage.raw_payload, dict) else {}
    raw_track_details = _raw_track_details(raw_payload)
    raw_costs = raw_payload.get("costs", {}) if isinstance(raw_payload.get("costs"), dict) else {}
    market_inputs = await market_snapshot_service.resolve_market_inputs(_extract_market_inputs(raw_payload))
    readiness = _analysis_readiness(mortgage=mortgage, raw_track_details=raw_track_details, market_inputs=market_inputs)
    latest_analysis_run = await db_manager.get_latest_analysis_run(mortgage.id)
    persisted_analysis_summary = _analysis_summary_from_run(latest_analysis_run)
    mortgage_summary = _mortgage_summary_view(
        mortgage=mortgage,
        readiness=readiness,
        latest_analysis_summary=persisted_analysis_summary,
        market_inputs=market_inputs,
    )

    alerts = await db_manager.list_alerts(user_id=user_id)
    pending_request = _pending_followup_request_view(
        await db_manager.get_latest_request(user_id=user_id, request_type="interest"),
        mortgage_id=mortgage.id,
    )
    freshness_summary = _market_freshness_summary(await market_status_service.list_source_status_views())
    calculated_at = datetime.now(timezone.utc)

    total_balance = mortgage.outstanding_balance_total
    avg_rate = 0.0
    if mortgage.tracks and float(total_balance) > 0:
        weighted = sum(float(track.current_rate) * float(track.outstanding_balance) for track in mortgage.tracks)
        avg_rate = weighted / float(total_balance)

    proposed_rate = max(avg_rate - 0.6, 2.0)
    term_months = max(track.remaining_term_months for track in mortgage.tracks) if mortgage.tracks else 240
    holding_period = user.holding_period_years if user and user.holding_period_years else 8
    mortgage_input = MortgageInput(
        lender_name=mortgage.lender_name,
        property_city=mortgage.property_city,
        property_value=mortgage.property_value,
        current_monthly_payment=mortgage.current_monthly_payment,
        loan_purpose=mortgage.loan_purpose,
        occupancy_status=mortgage.occupancy_status,
        prepayment_fee=Decimal(str(raw_costs.get("prepaymentFee", 0) or 0)),
        advisor_cost=Decimal(str(raw_costs.get("advisor", 0) or 0)),
        bank_cost=Decimal(str((raw_costs.get("legalFee", 0) or 0) + (raw_costs.get("registration", 0) or 0))),
        appraisal_cost=Decimal(str(raw_costs.get("appraisal", 0) or 0)),
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
                "original_cpi": raw_track_details.get(track.label, {}).get("originalCpi")
                or raw_track_details.get(track.label, {}).get("original_cpi"),
                "bank_margin": raw_track_details.get(track.label, {}).get("bankMargin")
                or raw_track_details.get(track.label, {}).get("bank_margin"),
            }
            for track in mortgage.tracks
        ],
    )
    calculation_payload = CalculationRequest(
        mortgage=mortgage_input,
        proposed_full_refinance={
            "interest_rate": proposed_rate,
            "term_months": term_months,
            "upfront_costs": Decimal("0"),
        },
        proposed_partial_refinance={
            "interest_rate": proposed_rate,
            "term_months": term_months,
            "upfront_costs": Decimal("0"),
        },
        market_inputs=market_inputs,
        holding_period_years=holding_period,
    )

    result: RecommendationResult | None
    try:
        result = calculator_manager.evaluate_partial_refinance(calculation_payload)
    except DomainError:
        result = None

    dashboard = _build_dashboard_response(
        mortgage_summary=mortgage_summary,
        result=result,
        persisted_analysis_summary=persisted_analysis_summary,
        alert_summary=_alert_summary(alerts),
        freshness_summary=freshness_summary,
        pending_request=pending_request,
        market_inputs=market_inputs,
        calculated_at=calculated_at,
    )
    return DashboardResponse(dashboard=dashboard, meta=build_response_meta(request))


@router.post("/requests/interest", response_model=InterestRequestResponse)
async def create_interest_request(
    payload: InterestRequestPayload,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    analytics_manager: Annotated[AnalyticsManager, Depends(get_analytics_manager)],
    captcha_manager: Annotated[CaptchaManager, Depends(get_captcha_manager)],
    rate_limit_manager: Annotated[RateLimitManager, Depends(get_rate_limit_manager)],
) -> InterestRequestResponse:
    rate_limit_manager.check(
        key=rate_limit_manager.build_key(["interest-request", request.client.host if request.client else "unknown"])
    )
    if not await captcha_manager.verify(payload.captcha_token, request.client.host if request.client else None):
        return InterestRequestResponse(status="captcha_failed", meta=build_response_meta(request))

    linked_mortgage_id = payload.mortgage_id
    linked_analysis_run_id = payload.analysis_run_id
    if payload.user_id is not None and linked_mortgage_id is None:
        latest_mortgage = await db_manager.get_latest_mortgage(payload.user_id)
        if latest_mortgage is not None:
            linked_mortgage_id = latest_mortgage.id
            if linked_analysis_run_id is None:
                latest_analysis = await db_manager.get_latest_analysis_run(latest_mortgage.id)
                linked_analysis_run_id = latest_analysis.id if latest_analysis is not None else None

    details = dict(payload.details)
    details.update(
        {
            "mortgage_id": linked_mortgage_id,
            "analysis_run_id": linked_analysis_run_id,
            "recommendation_code": payload.recommendation_code,
            "contact_preference": payload.contact_preference,
        }
    )
    customer_request = await db_manager.create_request(
        CustomerRequestIn(
            user_id=payload.user_id,
            request_type=payload.request_type,
            source_page=payload.source_page,
            notes=payload.notes,
            details={key: value for key, value in details.items() if value is not None},
        ),
        status=models.RequestStatus.FORWARDED,
    )
    await analytics_manager.track_conversion(
        page=payload.source_page or "unknown",
        session_id=None,
        source="interest_request",
    )
    return InterestRequestResponse(
        status="forwarded",
        request_id=customer_request.id,
        created_at=customer_request.created_at,
        request_type=customer_request.request_type,
        linked_mortgage_id=linked_mortgage_id,
        linked_analysis_run_id=linked_analysis_run_id,
        confirmation_code="REQUEST_FORWARDED",
        meta=build_response_meta(request),
    )


@router.post("/analytics/dropoff", response_model=AnalyticsAckResponse)
async def track_dropoff(
    payload: AnalyticsEventIn,
    request: Request,
    analytics_manager: Annotated[AnalyticsManager, Depends(get_analytics_manager)],
) -> AnalyticsAckResponse:
    await analytics_manager.track_dropoff(page=payload.page or "unknown", session_id=payload.session_id, metadata=payload.metadata)
    return AnalyticsAckResponse(status="tracked", meta=build_response_meta(request))
