from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from backend.app.domain.costs.advisor_fee import calculate_advisor_fee
from backend.app.domain.costs.appraisal import calculate_appraisal_fee
from backend.app.domain.costs.bank_fee import calculate_bank_fee
from backend.app.domain.costs.models import CostComponent, RefinanceCostBreakdown, TrackPenaltyBreakdown
from backend.app.domain.exceptions import UnsupportedAdjustablePenaltyCaseError, ValidationError
from backend.app.domain.market_data.models import MortgageRateBucketRecord
from backend.app.domain.models import MarketContext, MortgageTrack, TrackType
from backend.app.domain.penalties.regulation_116 import calculate_regulation_116_track_penalty


ZERO = Decimal("0")
ONE_NIS = Decimal("1")


def _other_cost_component(*, upfront_costs: Decimal, allocation_ratio: Decimal) -> CostComponent:
    if upfront_costs < 0:
        raise ValidationError("Additional upfront costs cannot be negative.")
    amount = upfront_costs * allocation_ratio
    return CostComponent(
        amount=amount,
        source="explicit_input" if amount > 0 else "not_applicable",
        included=amount > 0,
        metadata={"allocation_ratio": str(allocation_ratio)},
    )


def _unsupported_adjustable_penalty(
    *,
    track: MortgageTrack,
    reason_code: str,
    warning_codes: list[str],
    amount: Decimal = ZERO,
    metadata: dict[str, str] | None = None,
) -> TrackPenaltyBreakdown:
    return TrackPenaltyBreakdown(
        track_id=track.track_id or track.label,
        track_label=track.label,
        applicable=False,
        reason_code=reason_code,
        remaining_months=track.remaining_term_months,
        market_rate_bucket=None,
        market_annual_rate_percent=None,
        contract_annual_rate_percent=track.original_rate if track.original_rate is not None else track.current_rate,
        market_monthly_rate=None,
        contract_monthly_rate=None,
        pv_market_nis=None,
        pv_contract_nis=None,
        economic_loss_nis=amount,
        discount_factor=None,
        penalty_before_discount_nis=amount,
        penalty_after_discount_nis=amount,
        rounded_penalty_nis=amount,
        warning_codes=warning_codes,
        metadata=metadata or {},
    )


def _allocate_fallback_penalty_amounts(
    *,
    tracks: list[MortgageTrack],
    total_amount: Decimal,
) -> dict[str, Decimal]:
    if not tracks or total_amount <= 0:
        return {}

    total_balance = sum((track.outstanding_balance for track in tracks), ZERO)
    if total_balance <= 0:
        return {}

    remaining_amount = total_amount.quantize(ONE_NIS, rounding=ROUND_HALF_UP)
    allocations: dict[str, Decimal] = {}

    for index, track in enumerate(tracks):
        key = track.track_id or track.label
        if index == len(tracks) - 1:
            allocations[key] = remaining_amount
            continue

        share = track.outstanding_balance / total_balance
        amount = (remaining_amount * share).quantize(ONE_NIS, rounding=ROUND_HALF_UP)
        if amount > remaining_amount:
            amount = remaining_amount
        allocations[key] = amount
        remaining_amount -= amount

    return allocations


def calculate_refinance_cost_breakdown(
    *,
    tracks: list[MortgageTrack],
    market_context: MarketContext,
    market_rate_records: list[MortgageRateBucketRecord],
    years_since_origination: Decimal | None,
    advisor_fee_override: Decimal | None,
    bank_fee_override: Decimal | None,
    appraisal_included: bool,
    appraisal_amount: Decimal | None,
    additional_costs: Decimal,
    aggregated_prepayment_fee_override: Decimal | None,
    default_advisor_fee: Decimal,
    default_bank_fee: Decimal,
    default_appraisal_fee: Decimal,
    allocation_ratio: Decimal = Decimal("1"),
) -> RefinanceCostBreakdown:
    if allocation_ratio <= 0:
        raise ValidationError("Cost allocation ratio must be greater than zero.")
    if aggregated_prepayment_fee_override is not None and aggregated_prepayment_fee_override < 0:
        raise ValidationError("Aggregated prepayment fee override cannot be negative.")

    advisor_fee = calculate_advisor_fee(
        user_quote=advisor_fee_override,
        default_amount=default_advisor_fee,
        allocation_ratio=allocation_ratio,
    )
    bank_fee = calculate_bank_fee(
        user_quote=bank_fee_override,
        default_amount=default_bank_fee,
        allocation_ratio=allocation_ratio,
    )
    appraisal_fee = calculate_appraisal_fee(
        included=appraisal_included,
        explicit_amount=appraisal_amount,
        default_amount=default_appraisal_fee,
        allocation_ratio=allocation_ratio,
    )
    other_costs = _other_cost_component(upfront_costs=additional_costs, allocation_ratio=allocation_ratio)

    computed_penalties: list[TrackPenaltyBreakdown] = []
    unsupported_adjustable_tracks: list[MortgageTrack] = []

    for track in tracks:
        if track.track_type == TrackType.PRIME_FLOATING:
            computed_penalties.append(
                calculate_regulation_116_track_penalty(
                    track=track,
                    market_context=market_context,
                    market_rate_records=market_rate_records,
                    default_years_since_origination=years_since_origination,
                )
            )
            continue

        try:
            computed_penalties.append(
                calculate_regulation_116_track_penalty(
                    track=track,
                    market_context=market_context,
                    market_rate_records=market_rate_records,
                    default_years_since_origination=years_since_origination,
                )
            )
        except UnsupportedAdjustablePenaltyCaseError:
            unsupported_adjustable_tracks.append(track)

    warning_codes: list[str] = []
    computed_penalty_total = sum((item.rounded_penalty_nis for item in computed_penalties), ZERO)

    if unsupported_adjustable_tracks:
        warning_codes.append("ADJUSTABLE_TRACK_METADATA_INSUFFICIENT")
        fallback_total = ZERO
        if aggregated_prepayment_fee_override is not None and aggregated_prepayment_fee_override > 0:
            fallback_total = max(ZERO, (aggregated_prepayment_fee_override * allocation_ratio) - computed_penalty_total)
        allocated_amounts = _allocate_fallback_penalty_amounts(
            tracks=unsupported_adjustable_tracks,
            total_amount=fallback_total,
        )

        for track in unsupported_adjustable_tracks:
            allocated_amount = ZERO
            if fallback_total > 0:
                allocated_amount = allocated_amounts.get(track.track_id or track.label, ZERO)
                computed_penalties.append(
                    _unsupported_adjustable_penalty(
                        track=track,
                        reason_code="LEGACY_FALLBACK_ADJUSTABLE_TRACK",
                        warning_codes=["ADJUSTABLE_TRACK_METADATA_INSUFFICIENT", "LEGACY_FALLBACK_USED"],
                        amount=allocated_amount,
                        metadata={"allocation_method": "aggregated_override_balance_pro_rata"},
                    )
                )
                warning_codes.append("LEGACY_FALLBACK_USED")
            else:
                computed_penalties.append(
                    _unsupported_adjustable_penalty(
                        track=track,
                        reason_code="ADJUSTABLE_PENALTY_UNSUPPORTED",
                        warning_codes=["ADJUSTABLE_TRACK_METADATA_INSUFFICIENT"],
                    )
                )

    prepayment_penalty_total = sum((item.rounded_penalty_nis for item in computed_penalties), ZERO)
    total_refinance_cost = (
        advisor_fee.amount
        + bank_fee.amount
        + appraisal_fee.amount
        + other_costs.amount
        + prepayment_penalty_total
    )

    metadata = {
        "allocation_ratio": str(allocation_ratio),
        "cost_engine": "phase2_reg116_v1",
    }
    if unsupported_adjustable_tracks:
        metadata["unsupported_adjustable_tracks"] = ",".join(track.label for track in unsupported_adjustable_tracks)

    return RefinanceCostBreakdown(
        advisor_fee=advisor_fee,
        bank_fee=bank_fee,
        appraisal_fee=appraisal_fee,
        legacy_other_costs=other_costs,
        prepayment_penalty_total=prepayment_penalty_total,
        track_penalties=computed_penalties,
        total_refinance_cost=total_refinance_cost,
        source="phase2_refinance_cost_engine",
        warning_codes=sorted(set(warning_codes)),
        metadata=metadata,
    )
