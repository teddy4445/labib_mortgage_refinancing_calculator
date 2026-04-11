from __future__ import annotations

from decimal import Decimal

import pytest

from backend.app.domain.analysis.breakeven import BreakEvenAnalysis, calculate_break_even
from backend.app.domain.analysis.npv import NpvAnalysis, calculate_npv
from backend.app.domain.analysis.recommendation import build_recommendation_outcome
from backend.app.domain.exceptions import MissingMarketInputError
from backend.app.domain.models import MarketContext, MortgageTrack, TrackType
from backend.app.domain.scenarios.evaluator import evaluate_scenario_portfolio
from backend.app.domain.scenarios.explanations import derive_recommendation_tokens, derive_scenario_tokens_and_risks
from backend.app.domain.scenarios.generator import build_status_quo_scenario, zero_refinance_cost_breakdown
from backend.app.domain.scenarios.models import CostComponent, RefinanceCostBreakdown, ScenarioEvaluation, ScenarioType
from backend.app.domain.scenarios.partial_refinance import generate_partial_track_subsets
from backend.app.domain.scenarios.ranking import rank_scenarios
from backend.app.domain.scenarios.robustness import evaluate_prime_robustness
from backend.app.domain.totals import calculate_total_monthly_payment


def _track(
    label: str,
    track_type: TrackType,
    *,
    balance: str = "100000",
    rate: str = "4.0",
    months: int = 240,
    original_cpi: str | None = None,
    bank_margin: str | None = None,
) -> MortgageTrack:
    return MortgageTrack(
        label=label,
        track_type=track_type,
        outstanding_balance=Decimal(balance),
        current_rate=Decimal(rate),
        remaining_term_months=months,
        original_cpi=Decimal(original_cpi) if original_cpi is not None else None,
        bank_margin=Decimal(bank_margin) if bank_margin is not None else None,
    )


def _costs(total: str) -> RefinanceCostBreakdown:
    amount = Decimal(total)
    return RefinanceCostBreakdown(
        advisor_fee=CostComponent(amount=Decimal("0"), source="default", included=False),
        bank_fee=CostComponent(amount=Decimal("0"), source="default", included=False),
        appraisal_fee=CostComponent(amount=Decimal("0"), source="default", included=False),
        legacy_other_costs=CostComponent(amount=amount, source="legacy", included=amount > 0),
        prepayment_penalty_total=Decimal("0"),
        total_refinance_cost=amount,
    )


def _scenario(
    *,
    scenario_id: str,
    scenario_type: ScenarioType,
    monthly_savings: str,
    npv_value: str,
    break_even_months: int | None,
    cost_total: str = "0",
) -> ScenarioEvaluation:
    scenario = ScenarioEvaluation(
        id=scenario_id,
        type=scenario_type,
        name_code=scenario_id.upper(),
        description_code=scenario_id.upper(),
        portfolio_tracks=[],
        refinanced_track_labels=[],
        kept_track_labels=[],
        current_monthly_payment=Decimal("8000"),
        proposed_monthly_payment=Decimal("8000") - Decimal(monthly_savings),
        monthly_savings=Decimal(monthly_savings),
        total_outstanding_balance=Decimal("600000"),
        total_adjusted_balance=Decimal("600000"),
        refinance_costs=_costs(cost_total),
        break_even=BreakEvenAnalysis(
            break_even_months=break_even_months,
            break_even_years=Decimal("2") if break_even_months else None,
            raw_break_even_months=Decimal(str(break_even_months)) if break_even_months else None,
            monthly_savings=Decimal(monthly_savings),
            refinance_costs=Decimal(cost_total),
            is_viable=break_even_months is not None,
            reason_code="BREAK_EVEN_AVAILABLE" if break_even_months else "ZERO_MONTHLY_SAVINGS",
        ),
        npv=NpvAnalysis(
            npv=Decimal(npv_value),
            total_present_value=Decimal(npv_value) + Decimal(cost_total),
            monthly_discount_rate=Decimal("0.0032737398"),
            annual_discount_rate=Decimal("4.0"),
            horizon_months=96,
            is_positive=Decimal(npv_value) > 0,
            reason_code="POSITIVE_NPV" if Decimal(npv_value) > 0 else "NON_POSITIVE_NPV",
        ),
    )
    return scenario


def test_status_quo_scenario_has_zero_cost_and_no_artificial_savings() -> None:
    tracks = [_track("Fixed", TrackType.FIXED_NON_LINKED, balance="500000", rate="4.5", months=240)]
    summary = calculate_total_monthly_payment(tracks=tracks, context=MarketContext())

    scenario = build_status_quo_scenario(current_summary=summary, current_tracks=tracks)

    assert scenario.refinance_costs.total_refinance_cost == 0
    assert scenario.proposed_monthly_payment == scenario.current_monthly_payment
    assert scenario.monthly_savings == 0


def test_partial_refinance_generation_supports_exact_and_pruned_modes() -> None:
    three_tracks = [_track(f"T{index}", TrackType.FIXED_NON_LINKED) for index in range(3)]
    exact_subsets, exact_meta = generate_partial_track_subsets(three_tracks, max_scenarios=10)
    assert len(exact_subsets) == 6
    assert exact_meta["strategy"] == "exact"

    seven_tracks = [_track(f"S{index}", TrackType.FIXED_NON_LINKED) for index in range(7)]
    pruned_subsets, pruned_meta = generate_partial_track_subsets(seven_tracks, max_scenarios=10)
    assert len(pruned_subsets) == 10
    assert pruned_meta["strategy"] == "pruned_balance_priority"


def test_ranking_engine_prefers_beneficial_scenario_and_can_keep_status_quo() -> None:
    status_quo = _scenario(
        scenario_id="status_quo",
        scenario_type=ScenarioType.STATUS_QUO,
        monthly_savings="0",
        npv_value="0",
        break_even_months=None,
    )
    beneficial = _scenario(
        scenario_id="good_refi",
        scenario_type=ScenarioType.FULL_REFINANCE,
        monthly_savings="700",
        npv_value="22000",
        break_even_months=18,
        cost_total="8000",
    )
    harmful = _scenario(
        scenario_id="bad_refi",
        scenario_type=ScenarioType.FULL_REFINANCE,
        monthly_savings="-100",
        npv_value="-9000",
        break_even_months=None,
        cost_total="12000",
    )

    beneficial.explanation_tokens, beneficial.risk_flags = derive_scenario_tokens_and_risks(
        scenario=beneficial,
        status_quo=status_quo,
    )
    harmful.explanation_tokens, harmful.risk_flags = derive_scenario_tokens_and_risks(
        scenario=harmful,
        status_quo=status_quo,
    )
    status_quo.explanation_tokens, status_quo.risk_flags = derive_scenario_tokens_and_risks(
        scenario=status_quo,
        status_quo=status_quo,
    )

    ranked = rank_scenarios([harmful, status_quo, beneficial])
    assert ranked[0].id == "good_refi"
    assert ranked[-1].id == "bad_refi"

    only_bad_ranked = rank_scenarios([status_quo, harmful])
    assert only_bad_ranked[0].id == "status_quo"


def test_explanation_tokens_include_positive_and_negative_signals() -> None:
    status_quo = _scenario(
        scenario_id="status_quo",
        scenario_type=ScenarioType.STATUS_QUO,
        monthly_savings="0",
        npv_value="0",
        break_even_months=None,
    )
    positive = _scenario(
        scenario_id="positive",
        scenario_type=ScenarioType.PARTIAL_REFINANCE,
        monthly_savings="600",
        npv_value="15000",
        break_even_months=20,
        cost_total="9000",
    )
    negative = _scenario(
        scenario_id="negative",
        scenario_type=ScenarioType.FULL_REFINANCE,
        monthly_savings="-50",
        npv_value="-2500",
        break_even_months=None,
        cost_total="110000",
    )

    positive.explanation_tokens, positive.risk_flags = derive_scenario_tokens_and_risks(
        scenario=positive,
        status_quo=status_quo,
    )
    negative.explanation_tokens, negative.risk_flags = derive_scenario_tokens_and_risks(
        scenario=negative,
        status_quo=status_quo,
    )

    assert "LOWER_PAYMENT" in positive.explanation_tokens
    assert "POSITIVE_NPV" in positive.explanation_tokens
    assert "FAST_BREAK_EVEN" in positive.explanation_tokens
    assert "NEGATIVE_NPV" in negative.explanation_tokens
    assert "HIGH_UPFRONT_COST" in negative.explanation_tokens
    assert "HIGH_UPFRONT_COST" in negative.risk_flags


def test_prime_robustness_returns_stable_and_rising_paths() -> None:
    status_track = _track("Prime", TrackType.PRIME_FLOATING, balance="300000", rate="5.0", months=240, bank_margin="-0.5")
    status_summary = calculate_total_monthly_payment(
        tracks=[status_track],
        context=MarketContext(boi_base_rate=Decimal("4.0")),
    )
    status_quo = build_status_quo_scenario(current_summary=status_summary, current_tracks=[status_track])
    candidate = evaluate_scenario_portfolio(
        scenario_id="full_refi",
        scenario_type=ScenarioType.FULL_REFINANCE,
        name_code="FULL_REFINANCE",
        description_code="REFINANCE_ALL_TRACKS",
        portfolio_tracks=[_track("FixedNew", TrackType.FIXED_NON_LINKED, balance="300000", rate="3.0", months=240)],
        current_monthly_payment=status_summary.total_monthly_payment,
        refinance_costs=_costs("5000"),
        market_context=MarketContext(boi_base_rate=Decimal("4.0")),
        horizon_months=96,
        annual_discount_rate_percent=Decimal("4.0"),
        refinanced_track_labels=["Prime"],
        kept_track_labels=[],
    )

    robustness = evaluate_prime_robustness(
        scenario=candidate,
        status_quo=status_quo,
        base_context=MarketContext(boi_base_rate=Decimal("4.0")),
        annual_discount_rate_percent=Decimal("4.0"),
        holding_period_months=96,
        modest_annual_increase_percent=Decimal("0.25"),
    )

    assert len(robustness.path_results) == 2
    assert {path.path_code for path in robustness.path_results} == {"STABLE_BOI", "MODEST_BOI_INCREASE"}
    assert robustness.beneficial_under_all_paths is True


def test_prime_robustness_requires_boi_input_when_prime_exists() -> None:
    status_track = _track("Prime", TrackType.PRIME_FLOATING, balance="300000", rate="5.0", months=240, bank_margin="-0.5")
    status_summary = calculate_total_monthly_payment(
        tracks=[status_track],
        context=MarketContext(boi_base_rate=Decimal("4.0")),
    )
    status_quo = build_status_quo_scenario(current_summary=status_summary, current_tracks=[status_track])
    candidate = _scenario(
        scenario_id="candidate",
        scenario_type=ScenarioType.FULL_REFINANCE,
        monthly_savings="400",
        npv_value="12000",
        break_even_months=16,
    )

    with pytest.raises(MissingMarketInputError):
        evaluate_prime_robustness(
            scenario=candidate,
            status_quo=status_quo,
            base_context=MarketContext(),
            annual_discount_rate_percent=Decimal("4.0"),
            holding_period_months=96,
            modest_annual_increase_percent=Decimal("0.25"),
        )


def test_recommendation_tokens_and_summary_include_partial_outperformance() -> None:
    status_quo = _scenario(
        scenario_id="status_quo",
        scenario_type=ScenarioType.STATUS_QUO,
        monthly_savings="0",
        npv_value="0",
        break_even_months=None,
    )
    full = _scenario(
        scenario_id="full_refi",
        scenario_type=ScenarioType.FULL_REFINANCE,
        monthly_savings="450",
        npv_value="9000",
        break_even_months=28,
        cost_total="12000",
    )
    partial = _scenario(
        scenario_id="partial_refi",
        scenario_type=ScenarioType.PARTIAL_REFINANCE,
        monthly_savings="520",
        npv_value="14000",
        break_even_months=16,
        cost_total="7000",
    )

    for scenario in (status_quo, full, partial):
        scenario.explanation_tokens, scenario.risk_flags = derive_scenario_tokens_and_risks(
            scenario=scenario,
            status_quo=status_quo,
        )

    ranked = rank_scenarios([status_quo, full, partial])
    tokens = derive_recommendation_tokens(ranked_scenarios=ranked, status_quo=status_quo)
    outcome = build_recommendation_outcome(
        ranked_scenarios=ranked,
        status_quo_scenario=status_quo,
        explanation_tokens=tokens,
    )

    assert ranked[0].id == "partial_refi"
    assert "PARTIAL_REFI_OUTPERFORMS_FULL" in tokens
    assert outcome.best_scenario_id == "partial_refi"
    assert outcome.requires_human_followup_offer is True
