from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from backend.app.domain.costs import (
    calculate_advisor_fee,
    calculate_appraisal_fee,
    calculate_bank_fee,
    calculate_refinance_cost_breakdown,
)
from backend.app.domain.exceptions import UnsupportedAdjustablePenaltyCaseError
from backend.app.domain.market_data.models import MortgageRateBucketRecord
from backend.app.domain.market_data.selectors import lookup_mortgage_bucket_by_remaining_months
from backend.app.domain.models import MarketContext, MortgageTrack, TrackType
from backend.app.domain.penalties import calculate_regulation_116_track_penalty, statutory_discount_factor
from backend.app.managers.calculator_manager import CalculatorManager
from backend.app.schemas import CalculationRequest, MarketInputs, MortgageInput


def _bucket_records(*, up_to_5: str = "4.1", five_to_ten: str = "4.3", ten_to_fifteen: str = "3.8", fifteen_to_twenty: str = "4.7") -> list[MortgageRateBucketRecord]:
    return [
        MortgageRateBucketRecord(
            effective_date=date(2026, 4, 1),
            track_family="general",
            bucket_code="up_to_5_years",
            remaining_months_min=1,
            remaining_months_max=60,
            annual_rate_percent=Decimal(up_to_5),
            source_key="test",
        ),
        MortgageRateBucketRecord(
            effective_date=date(2026, 4, 1),
            track_family="general",
            bucket_code="five_to_ten_years",
            remaining_months_min=61,
            remaining_months_max=120,
            annual_rate_percent=Decimal(five_to_ten),
            source_key="test",
        ),
        MortgageRateBucketRecord(
            effective_date=date(2026, 4, 1),
            track_family="general",
            bucket_code="ten_to_fifteen_years",
            remaining_months_min=121,
            remaining_months_max=180,
            annual_rate_percent=Decimal(ten_to_fifteen),
            source_key="test",
        ),
        MortgageRateBucketRecord(
            effective_date=date(2026, 4, 1),
            track_family="general",
            bucket_code="fifteen_to_twenty_years",
            remaining_months_min=181,
            remaining_months_max=240,
            annual_rate_percent=Decimal(fifteen_to_twenty),
            source_key="test",
        ),
    ]


def _fixed_track() -> MortgageTrack:
    return MortgageTrack(
        track_id="fixed-track",
        label="Fixed",
        track_type=TrackType.FIXED_NON_LINKED,
        outstanding_balance=Decimal("300000"),
        current_rate=Decimal("4.5"),
        original_rate=Decimal("4.5"),
        remaining_term_months=180,
        years_since_origination=Decimal("6"),
    )


def _linked_track() -> MortgageTrack:
    return MortgageTrack(
        track_id="linked-track",
        label="Linked",
        track_type=TrackType.FIXED_LINKED,
        outstanding_balance=Decimal("300000"),
        current_rate=Decimal("2.0"),
        original_rate=Decimal("2.0"),
        remaining_term_months=180,
        original_cpi=Decimal("92.5"),
        years_since_origination=Decimal("6"),
    )


def _prime_track() -> MortgageTrack:
    return MortgageTrack(
        track_id="prime-track",
        label="Prime",
        track_type=TrackType.PRIME_FLOATING,
        outstanding_balance=Decimal("300000"),
        current_rate=Decimal("5.0"),
        remaining_term_months=240,
        bank_margin=Decimal("-0.5"),
        years_since_origination=Decimal("6"),
    )


def _adjustable_track(*, supported: bool) -> MortgageTrack:
    return MortgageTrack(
        track_id="adjustable-track",
        label="Adjustable",
        track_type=TrackType.ADJUSTABLE_NON_LINKED,
        outstanding_balance=Decimal("250000"),
        current_rate=Decimal("4.2"),
        original_rate=Decimal("4.2"),
        remaining_term_months=180,
        reset_interval="60_months" if supported else None,
        next_reset_date=date(2028, 4, 1) if supported else None,
        years_since_origination=Decimal("4"),
    )


def _market_context() -> MarketContext:
    return MarketContext(boi_base_rate=Decimal("4.0"), current_cpi=Decimal("115.0"), as_of=date(2026, 4, 1))


def test_advisor_fee_default_and_override() -> None:
    default_fee = calculate_advisor_fee(user_quote=None, default_amount=Decimal("7000"))
    override_fee = calculate_advisor_fee(user_quote=Decimal("8200"), default_amount=Decimal("7000"))

    assert default_fee.amount == Decimal("7000")
    assert default_fee.source == "default_estimate"
    assert override_fee.amount == Decimal("8200")
    assert override_fee.source == "user_override"


def test_bank_fee_default_and_override() -> None:
    default_fee = calculate_bank_fee(user_quote=None, default_amount=Decimal("3500"))
    override_fee = calculate_bank_fee(user_quote=Decimal("4100"), default_amount=Decimal("3500"))

    assert default_fee.amount == Decimal("3500")
    assert default_fee.source == "default_estimate"
    assert override_fee.amount == Decimal("4100")
    assert override_fee.source == "user_override"


def test_appraisal_fee_omitted_and_included() -> None:
    omitted = calculate_appraisal_fee(
        included=False,
        explicit_amount=None,
        default_amount=Decimal("2500"),
    )
    explicit = calculate_appraisal_fee(
        included=True,
        explicit_amount=Decimal("2800"),
        default_amount=Decimal("2500"),
    )
    defaulted = calculate_appraisal_fee(
        included=True,
        explicit_amount=None,
        default_amount=Decimal("2500"),
    )

    assert omitted.amount == Decimal("0")
    assert omitted.source == "not_applicable"
    assert explicit.amount == Decimal("2800")
    assert explicit.source == "user_override"
    assert defaulted.amount == Decimal("2500")
    assert defaulted.source == "default_estimate"


def test_penalty_applicability_for_fixed_prime_and_adjustable_cases() -> None:
    bucket_records = _bucket_records()
    fixed_penalty = calculate_regulation_116_track_penalty(
        track=_fixed_track(),
        market_context=_market_context(),
        market_rate_records=bucket_records,
        default_years_since_origination=Decimal("6"),
    )
    prime_penalty = calculate_regulation_116_track_penalty(
        track=_prime_track(),
        market_context=_market_context(),
        market_rate_records=bucket_records,
        default_years_since_origination=Decimal("6"),
    )

    assert fixed_penalty.applicable is True
    assert fixed_penalty.reason_code in {"REG116_FIXED_TRACK", "REG116_NO_ECONOMIC_LOSS"}
    assert prime_penalty.applicable is False
    assert prime_penalty.reason_code == "REG116_NOT_APPLICABLE_PRIME"

    with pytest.raises(UnsupportedAdjustablePenaltyCaseError):
        calculate_regulation_116_track_penalty(
            track=_adjustable_track(supported=False),
            market_context=_market_context(),
            market_rate_records=bucket_records,
            default_years_since_origination=Decimal("4"),
        )


def test_bucket_selection_boundaries() -> None:
    assert lookup_mortgage_bucket_by_remaining_months(60).bucket_code == "up_to_5_years"
    assert lookup_mortgage_bucket_by_remaining_months(61).bucket_code == "five_to_ten_years"
    assert lookup_mortgage_bucket_by_remaining_months(120).bucket_code == "five_to_ten_years"
    assert lookup_mortgage_bucket_by_remaining_months(121).bucket_code == "ten_to_fifteen_years"
    assert lookup_mortgage_bucket_by_remaining_months(180).bucket_code == "ten_to_fifteen_years"
    assert lookup_mortgage_bucket_by_remaining_months(181).bucket_code == "fifteen_to_twenty_years"


def test_discount_factor_boundaries() -> None:
    assert statutory_discount_factor(Decimal("2.9")) == Decimal("1.00")
    assert statutory_discount_factor(Decimal("3.0")) == Decimal("0.80")
    assert statutory_discount_factor(Decimal("4.9")) == Decimal("0.80")
    assert statutory_discount_factor(Decimal("5.0")) == Decimal("0.70")


def test_regulation_116_returns_zero_when_no_economic_loss() -> None:
    penalty = calculate_regulation_116_track_penalty(
        track=_fixed_track(),
        market_context=_market_context(),
        market_rate_records=_bucket_records(ten_to_fifteen="5.5"),
        default_years_since_origination=Decimal("6"),
    )

    assert penalty.economic_loss_nis == Decimal("0")
    assert penalty.rounded_penalty_nis == Decimal("0")
    assert penalty.reason_code == "REG116_NO_ECONOMIC_LOSS"


def test_regulation_116_returns_discounted_positive_penalty() -> None:
    penalty = calculate_regulation_116_track_penalty(
        track=_fixed_track(),
        market_context=_market_context(),
        market_rate_records=_bucket_records(ten_to_fifteen="3.8"),
        default_years_since_origination=Decimal("6"),
    )

    assert penalty.economic_loss_nis is not None
    assert penalty.economic_loss_nis > 0
    assert penalty.discount_factor == Decimal("0.70")
    assert penalty.penalty_after_discount_nis > 0
    assert penalty.rounded_penalty_nis > 0


def test_refinance_cost_aggregation_and_adjustable_fallback_warning() -> None:
    breakdown = calculate_refinance_cost_breakdown(
        tracks=[_fixed_track(), _prime_track(), _adjustable_track(supported=False)],
        market_context=_market_context(),
        market_rate_records=_bucket_records(),
        years_since_origination=Decimal("6"),
        advisor_fee_override=None,
        bank_fee_override=Decimal("3200"),
        appraisal_included=True,
        appraisal_amount=None,
        additional_costs=Decimal("900"),
        aggregated_prepayment_fee_override=Decimal("11000"),
        default_advisor_fee=Decimal("7000"),
        default_bank_fee=Decimal("3500"),
        default_appraisal_fee=Decimal("2500"),
    )

    assert breakdown.advisor_fee.amount == Decimal("7000")
    assert breakdown.advisor_fee.source == "default_estimate"
    assert breakdown.bank_fee.amount == Decimal("3200")
    assert breakdown.bank_fee.source == "user_override"
    assert breakdown.appraisal_fee.amount == Decimal("2500")
    assert breakdown.appraisal_fee.source == "default_estimate"
    assert breakdown.prepayment_penalty_total == sum(item.rounded_penalty_nis for item in breakdown.track_penalties)
    assert breakdown.total_refinance_cost == (
        breakdown.advisor_fee.amount
        + breakdown.bank_fee.amount
        + breakdown.appraisal_fee.amount
        + breakdown.legacy_other_costs.amount
        + breakdown.prepayment_penalty_total
    )
    assert any(item.reason_code == "LEGACY_FALLBACK_ADJUSTABLE_TRACK" for item in breakdown.track_penalties)
    assert "LEGACY_FALLBACK_USED" in breakdown.warning_codes


def test_calculator_manager_integration_uses_phase2_cost_engine() -> None:
    manager = CalculatorManager()
    result = manager.evaluate_refinance(
        CalculationRequest(
            mortgage=MortgageInput(
                lender_name="Test Bank",
                property_city="Haifa",
                property_value=Decimal("1500000"),
                current_monthly_payment=Decimal("0"),
                loan_purpose="home",
                occupancy_status="owner",
                prepayment_fee=Decimal("0"),
                advisor_cost=Decimal("0"),
                bank_cost=Decimal("0"),
                appraisal_cost=Decimal("0"),
                appraisal_required=False,
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
                ],
            ),
            proposed_full_refinance={
                "interest_rate": Decimal("3.2"),
                "term_months": 240,
                "upfront_costs": Decimal("0"),
            },
            market_inputs=MarketInputs(
                boi_base_rate=Decimal("4.0"),
                current_cpi=Decimal("115.0"),
                as_of="2026-04-01",
                mortgage_rate_buckets=[item.model_dump(mode="python") for item in _bucket_records()],
            ),
            holding_period_years=8,
        )
    )

    cost_breakdown = result.best_scenario.refinance_costs
    assert cost_breakdown.source == "phase2_refinance_cost_engine"
    assert "LEGACY_COST_BREAKDOWN_USED" not in cost_breakdown.warning_codes
    assert cost_breakdown.track_penalties
    assert cost_breakdown.track_penalties[0].reason_code in {"REG116_FIXED_TRACK", "REG116_NO_ECONOMIC_LOSS"}
