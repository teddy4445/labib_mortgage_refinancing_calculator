from __future__ import annotations

from decimal import Decimal

from backend.app.managers.calculator_manager import CalculatorManager
from backend.app.schemas import CalculationRequest, MarketInputs, MortgageInput


def _payload() -> CalculationRequest:
    return CalculationRequest(
        mortgage=MortgageInput(
            lender_name="Test Bank",
            property_city="Haifa",
            property_value=Decimal("1500000"),
            current_monthly_payment=Decimal("0"),
            loan_purpose="home",
            occupancy_status="owner",
            prepayment_fee=Decimal("7000"),
            advisor_cost=Decimal("6000"),
            bank_cost=Decimal("3500"),
            appraisal_cost=Decimal("1500"),
            tracks=[
                {
                    "label": "Fixed",
                    "track_type": "fixed_non_linked",
                    "outstanding_balance": Decimal("500000"),
                    "current_rate": Decimal("4.8"),
                    "remaining_term_months": 240,
                },
                {
                    "label": "Prime",
                    "track_type": "prime_floating",
                    "outstanding_balance": Decimal("300000"),
                    "current_rate": Decimal("5.0"),
                    "remaining_term_months": 240,
                    "bank_margin": Decimal("-0.5"),
                },
                {
                    "label": "Linked",
                    "track_type": "fixed_linked",
                    "outstanding_balance": Decimal("200000"),
                    "current_rate": Decimal("2.0"),
                    "remaining_term_months": 180,
                    "original_cpi": Decimal("92.5"),
                },
            ],
        ),
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
        market_inputs=MarketInputs(boi_base_rate=Decimal("4.0"), current_cpi=Decimal("115.0")),
        holding_period_years=8,
    )


def test_calculator_manager_returns_structured_scenarios_for_full_refinance() -> None:
    manager = CalculatorManager()
    result = manager.evaluate_refinance(_payload())

    assert result.current_summary is not None
    assert result.recommendation_summary is not None
    assert len(result.scenarios) == 2
    assert result.scenarios[0].id == result.recommendation_summary.best_scenario_id
    assert result.assumptions["engine_version"] == "phase3-scenarios-v1"


def test_calculator_manager_partial_refinance_returns_partial_candidates_and_serializable_output() -> None:
    manager = CalculatorManager()
    result = manager.evaluate_partial_refinance(_payload())

    assert result.current_summary is not None
    assert result.recommendation_summary is not None
    assert len(result.scenarios) >= 4
    assert any(scenario.scenario_type == "partial_refinance" for scenario in result.scenarios)
    assert result.recommendation_summary.ranking

    serialized = result.model_dump(mode="json")
    assert serialized["recommendation_summary"]["best_scenario_id"]
    assert serialized["scenarios"][0]["refinance_costs"]["total_refinance_cost"] is not None
