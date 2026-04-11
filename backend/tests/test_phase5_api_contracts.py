from __future__ import annotations

import hashlib
from decimal import Decimal

import pytest

from backend.app import models
from backend.app.schemas import CalculationRequest, MarketInputs, MortgageInput, UserCreate


def _hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


async def _seed_market_data(testbed: dict) -> None:
    service = testbed["market_data_service"]
    await service.refresh_all_market_data()


async def _create_user(testbed: dict, *, email: str = "user@example.com", username: str = "user1") -> models.User:
    db_manager = testbed["db_manager"]
    return await db_manager.create_user(
        UserCreate(
            username=username,
            email=email,
            password="Secure123!",
            phone_number="0501234567",
            holding_period_years=8,
            risk_tolerance="balanced",
            payment_sensitivity="medium",
            preference_goal="monthly_payment",
            inflation_aversion="high",
            reset_risk_aversion="medium",
        ),
        password_hash=_hash_password("Secure123!"),
    )


def _mortgage_payload() -> MortgageInput:
    return MortgageInput(
        lender_name="Test Bank",
        property_city="Haifa",
        property_value=Decimal("1500000"),
        current_monthly_payment=Decimal("6450"),
        loan_purpose="home",
        occupancy_status="owner",
        prepayment_fee=Decimal("7000"),
        advisor_cost=Decimal("6000"),
        bank_cost=Decimal("3500"),
        appraisal_cost=Decimal("1500"),
        appraisal_required=True,
        years_since_origination=Decimal("6"),
        tracks=[
            {
                "track_id": "fixed-track",
                "label": "Fixed",
                "track_type": "fixed_non_linked",
                "outstanding_balance": Decimal("500000"),
                "current_rate": Decimal("4.8"),
                "original_rate": Decimal("4.8"),
                "remaining_term_months": 240,
                "years_since_origination": Decimal("6"),
            },
            {
                "track_id": "prime-track",
                "label": "Prime",
                "track_type": "prime_floating",
                "outstanding_balance": Decimal("300000"),
                "current_rate": Decimal("5.0"),
                "remaining_term_months": 240,
                "bank_margin": Decimal("-0.5"),
                "years_since_origination": Decimal("6"),
            },
            {
                "track_id": "linked-track",
                "label": "Linked",
                "track_type": "fixed_linked",
                "outstanding_balance": Decimal("200000"),
                "current_rate": Decimal("2.0"),
                "original_rate": Decimal("2.0"),
                "remaining_term_months": 180,
                "original_cpi": Decimal("92.5"),
                "years_since_origination": Decimal("6"),
            },
        ],
    )


def _calculation_payload() -> dict:
    return CalculationRequest(
        mortgage=_mortgage_payload(),
        proposed_full_refinance={
            "interest_rate": Decimal("3.2"),
            "term_months": 240,
            "upfront_costs": Decimal("0"),
        },
        proposed_partial_refinance={
            "interest_rate": Decimal("3.1"),
            "term_months": 240,
            "upfront_costs": Decimal("0"),
        },
        market_inputs=MarketInputs(
            boi_base_rate=Decimal("4.5"),
            current_cpi=Decimal("115.8"),
            as_of="2026-04-01",
            mortgage_rate_buckets=[
                {
                    "effective_date": "2026-04-01",
                    "track_family": "general",
                    "bucket_code": "up_to_5_years",
                    "remaining_months_min": 1,
                    "remaining_months_max": 60,
                    "annual_rate_percent": Decimal("4.1"),
                },
                {
                    "effective_date": "2026-04-01",
                    "track_family": "general",
                    "bucket_code": "five_to_ten_years",
                    "remaining_months_min": 61,
                    "remaining_months_max": 120,
                    "annual_rate_percent": Decimal("4.3"),
                },
                {
                    "effective_date": "2026-04-01",
                    "track_family": "general",
                    "bucket_code": "ten_to_fifteen_years",
                    "remaining_months_min": 121,
                    "remaining_months_max": 180,
                    "annual_rate_percent": Decimal("4.5"),
                },
                {
                    "effective_date": "2026-04-01",
                    "track_family": "general",
                    "bucket_code": "fifteen_to_twenty_years",
                    "remaining_months_min": 181,
                    "remaining_months_max": 240,
                    "annual_rate_percent": Decimal("4.7"),
                },
            ],
        ),
        holding_period_years=8,
    ).model_dump(mode="json")


async def _create_mortgage(testbed: dict, user_id: int) -> models.Mortgage:
    db_manager = testbed["db_manager"]
    payload = _mortgage_payload()
    raw_payload = {
        "costs": {
            "prepaymentFee": 7000,
            "advisor": 6000,
            "bankFees": 3500,
            "appraisal": 1500,
            "appraisalRequired": True,
        },
        "basic": {"yearsSinceOrigin": 6},
        "market_inputs": {
            "boi_base_rate": "4.5",
            "current_cpi": "115.8",
            "as_of": "2026-04-01",
        },
        "tracks": [
            {"label": "Fixed", "originalRate": "4.8"},
            {"label": "Prime", "bankMargin": "-0.5"},
            {"label": "Linked", "originalCpi": "92.5", "originalRate": "2.0"},
        ],
    }
    return await db_manager.create_mortgage(user_id=user_id, payload=payload, raw_payload=raw_payload)


@pytest.mark.anyio
async def test_dashboard_contract_contains_stable_keys_and_summaries(api_client, market_data_testbed: dict) -> None:
    await _seed_market_data(market_data_testbed)
    user = await _create_user(market_data_testbed, email="dash@example.com", username="dash-user")
    mortgage = await _create_mortgage(market_data_testbed, user.id)
    db_manager = market_data_testbed["db_manager"]
    await db_manager.create_alert(
        user_id=user.id,
        title="Rate opportunity",
        message="A better scenario was detected.",
        severity="warning",
        source="analysis",
        payload={"code": "RATE_DROP"},
    )

    response = await api_client.get(f"/api/v1/mortgages/dashboard?user_id={user.id}")
    assert response.status_code == 200
    payload = response.json()
    dashboard = payload["dashboard"]

    assert payload["meta"]["request_id"]
    assert response.headers["X-Request-ID"] == payload["meta"]["request_id"]
    assert dashboard["currentMonthlyPayment"] > 0
    assert dashboard["recommendationSummary"] is not None
    assert dashboard["mortgageSummary"]["id"] == mortgage.id
    assert dashboard["latestAnalysisSummary"]["source"] == "runtime_recalculation"
    assert dashboard["alertSummary"]["active_count"] == 1
    assert dashboard["marketDataFreshness"]["healthy_sources"] >= 1
    assert "hasBetterOption" in dashboard
    assert "topExplanationTokens" in dashboard
    assert "pendingFollowUpRequest" in dashboard


@pytest.mark.anyio
async def test_latest_mortgage_contract_includes_tracks_and_readiness(api_client, market_data_testbed: dict) -> None:
    await _seed_market_data(market_data_testbed)
    user = await _create_user(market_data_testbed, email="mortgage@example.com", username="mortgage-user")
    await _create_mortgage(market_data_testbed, user.id)

    response = await api_client.get(f"/api/v1/mortgages/latest?user_id={user.id}")
    assert response.status_code == 200
    payload = response.json()
    mortgage = payload["mortgage"]

    assert payload["meta"]["contract_version"]
    assert mortgage["tracks"]
    assert mortgage["analysis_readiness"]["ready"] is True
    assert mortgage["normalized_values"]["track_count"] == 3
    assert mortgage["latest_analysis_summary"] is None


@pytest.mark.anyio
async def test_full_refinance_contract_has_structured_analysis(api_client) -> None:
    response = await api_client.post("/api/v1/mortgages/calculate/full", json=_calculation_payload())
    assert response.status_code == 200
    payload = response.json()

    assert payload["analysis_kind"] == "full_refinance_analysis"
    assert payload["best_scenario"] is not None
    assert payload["status_quo_scenario"] is not None
    assert payload["recommendation_summary"] is not None
    assert payload["best_scenario"]["break_even"]["reason_code"]
    assert payload["best_scenario"]["refinance_costs"]["total_refinance_cost"] is not None
    assert payload["explanation_tokens"]
    assert payload["risk_flags"] is not None
    assert payload["meta"]["request_id"]


@pytest.mark.anyio
async def test_partial_refinance_contract_has_ranked_scenarios_and_best_scenario(api_client) -> None:
    response = await api_client.post("/api/v1/mortgages/calculate/partial", json=_calculation_payload())
    assert response.status_code == 200
    payload = response.json()

    assert payload["analysis_kind"] == "partial_refinance_analysis"
    assert len(payload["scenarios"]) >= 4
    assert any(scenario["scenario_type"] == "partial_refinance" for scenario in payload["scenarios"])
    assert payload["best_scenario"]["id"] == payload["recommendation_summary"]["best_scenario_id"]
    assert payload["alternative_scenarios"]
    assert "robustness_summary" in payload


@pytest.mark.anyio
async def test_customer_interest_request_flow_links_to_latest_mortgage_and_analysis(api_client, market_data_testbed: dict) -> None:
    await _seed_market_data(market_data_testbed)
    user = await _create_user(market_data_testbed, email="interest@example.com", username="interest-user")
    mortgage = await _create_mortgage(market_data_testbed, user.id)
    calculator_manager = market_data_testbed["calculator_manager"]
    db_manager = market_data_testbed["db_manager"]
    analysis_result = calculator_manager.evaluate_partial_refinance(CalculationRequest(**_calculation_payload()))
    analysis_run = await db_manager.create_analysis_run(mortgage_id=mortgage.id, result=analysis_result)

    response = await api_client.post(
        "/api/v1/mortgages/requests/interest",
        json={
            "user_id": user.id,
            "request_type": "interest",
            "source_page": "dashboard",
            "details": {"recommendation": "CONSIDER_PARTIAL_REFINANCE"},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    stored_request = await db_manager.get_latest_request(user_id=user.id, request_type="interest")

    assert payload["status"] == "forwarded"
    assert payload["linked_mortgage_id"] == mortgage.id
    assert payload["linked_analysis_run_id"] == analysis_run.id
    assert payload["confirmation_code"] == "REQUEST_FORWARDED"
    assert stored_request is not None
    assert stored_request.status == models.RequestStatus.FORWARDED
    assert stored_request.details["mortgage_id"] == mortgage.id
    assert stored_request.details["analysis_run_id"] == analysis_run.id


@pytest.mark.anyio
async def test_alerts_contract_and_dismiss_flow(api_client, market_data_testbed: dict) -> None:
    user = await _create_user(market_data_testbed, email="alerts@example.com", username="alerts-user")
    db_manager = market_data_testbed["db_manager"]
    active = await db_manager.create_alert(
        user_id=user.id,
        title="New recommendation",
        message="Savings improved.",
        severity="high",
        source="analysis",
        payload={"code": "NEW_RECOMMENDATION", "action_code": "VIEW_ANALYSIS"},
    )
    history = await db_manager.create_alert(
        user_id=user.id,
        title="History item",
        message="Older alert.",
        severity="warning",
        source="analysis",
    )
    dismissed = await db_manager.create_alert(
        user_id=user.id,
        title="Dismissed item",
        message="Dismissed alert.",
        severity="warning",
        source="system",
    )
    await db_manager.update_alert_status(history.id, models.AlertStatus.HISTORY)
    await db_manager.update_alert_status(dismissed.id, models.AlertStatus.DISMISSED)

    response = await api_client.get(f"/api/v1/alerts?user_id={user.id}")
    assert response.status_code == 200
    payload = response.json()

    assert payload["summary"]["active_count"] == 1
    assert payload["summary"]["history_count"] == 1
    assert payload["summary"]["dismissed_count"] == 1
    assert payload["active"][0]["code"] == "NEW_RECOMMENDATION"
    assert payload["active"][0]["dismissed"] is False

    dismiss_response = await api_client.post(f"/api/v1/alerts/{active.id}/dismiss")
    assert dismiss_response.status_code == 200
    dismiss_payload = dismiss_response.json()
    assert dismiss_payload["status"] == "dismissed"
    assert dismiss_payload["alert_id"] == active.id
    assert dismiss_payload["meta"]["request_id"]


@pytest.mark.anyio
async def test_error_contract_is_consistent_for_validation_and_auth(api_client, market_data_testbed: dict) -> None:
    user = await _create_user(market_data_testbed, email="auth@example.com", username="auth-user")

    auth_response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "wrong-password"},
    )
    assert auth_response.status_code == 401
    auth_payload = auth_response.json()
    assert auth_payload["detail"] == "Invalid credentials."
    assert auth_payload["error"]["code"] == "INVALID_CREDENTIALS"
    assert auth_payload["meta"]["request_id"]

    validation_response = await api_client.post(
        "/api/v1/mortgages",
        json={
            "user_id": user.id,
            "mortgage": {
                "lender_name": "Broken Bank",
                "property_city": "Haifa",
                "property_value": 1000000,
                "current_monthly_payment": 0,
                "tracks": [],
            },
        },
    )
    assert validation_response.status_code == 422
    validation_payload = validation_response.json()
    assert validation_payload["error"]["code"] == "VALIDATION_ERROR"
    assert validation_payload["meta"]["request_id"]


@pytest.mark.anyio
async def test_backward_compatibility_smoke_for_existing_frontend_flows(api_client, market_data_testbed: dict) -> None:
    await _seed_market_data(market_data_testbed)

    register_response = await api_client.post(
        "/api/v1/auth/register",
        json={
            "username": "frontend-user",
            "email": "frontend@example.com",
            "password": "Secure123!",
            "phone_number": "0507654321",
        },
    )
    assert register_response.status_code == 200
    user_id = register_response.json()["user_id"]

    login_response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "frontend@example.com", "password": "Secure123!"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["role"] == "user"

    mortgage_response = await api_client.post(
        "/api/v1/mortgages",
        json={
            "user_id": user_id,
            "mortgage": _mortgage_payload().model_dump(mode="json"),
            "raw_payload": {
                "tracks": [
                    {"label": "Fixed"},
                    {"label": "Prime", "bankMargin": "-0.5"},
                    {"label": "Linked", "originalCpi": "92.5"},
                ]
            },
        },
    )
    assert mortgage_response.status_code == 200

    dashboard_response = await api_client.get(f"/api/v1/mortgages/dashboard?user_id={user_id}")
    assert dashboard_response.status_code == 200
    assert "dashboard" in dashboard_response.json()

    alerts_response = await api_client.get(f"/api/v1/alerts?user_id={user_id}")
    assert alerts_response.status_code == 200
    assert "active" in alerts_response.json()

    admin_response = await api_client.get("/api/v1/admin/overview")
    assert admin_response.status_code == 200
    assert "metrics" in admin_response.json()
