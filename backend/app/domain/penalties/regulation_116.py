from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from backend.app.domain.costs.models import TrackPenaltyBreakdown
from backend.app.domain.exceptions import (
    MarketDataBucketLookupError,
    MissingPenaltyInputError,
    UnsupportedAdjustablePenaltyCaseError,
    ValidationError,
)
from backend.app.domain.market_data.models import MortgageRateBucketRecord
from backend.app.domain.models import MarketContext, MortgageTrack, TrackType
from backend.app.domain.penalties.discount_rules import statutory_discount_factor
from backend.app.domain.penalties.market_rate_selection import select_regulation_116_market_rate
from backend.app.domain.penalties.payment_stream import (
    build_remaining_payment_stream,
    present_value_of_payment_stream,
)
from backend.app.domain.rates import convert_annual_to_monthly_rate
from backend.app.domain.totals import calculate_total_monthly_payment


ONE_NIS = Decimal("1")


def _months_until(target_date: date, reference_date: date) -> int:
    months = (target_date.year - reference_date.year) * 12 + (target_date.month - reference_date.month)
    if target_date.day < reference_date.day:
        months -= 1
    return max(0, months)


def _track_years_since_origination(
    *,
    track: MortgageTrack,
    default_years_since_origination: Decimal | None,
) -> Decimal:
    years_since_origination = track.years_since_origination
    if years_since_origination is None:
        years_since_origination = default_years_since_origination
    if years_since_origination is None:
        raise MissingPenaltyInputError(
            f"Years since origination are required for Regulation 116 penalty calculation on track={track.label}"
        )
    return years_since_origination


def _contract_rate_for_penalty(track: MortgageTrack) -> Decimal:
    contract_rate = track.original_rate if track.original_rate is not None else track.current_rate
    if contract_rate is None:
        raise MissingPenaltyInputError(f"Contract/original annual rate is required for track={track.label}")
    return contract_rate


def _penalty_window_months(track: MortgageTrack, *, as_of: date | None) -> tuple[int, str, list[str]]:
    if track.track_type in {TrackType.FIXED_NON_LINKED, TrackType.FIXED_LINKED}:
        return track.remaining_term_months, "REG116_FIXED_TRACK", []

    if track.track_type == TrackType.PRIME_FLOATING:
        return 0, "REG116_NOT_APPLICABLE_PRIME", []

    if track.track_type in {TrackType.ADJUSTABLE_NON_LINKED, TrackType.ADJUSTABLE_LINKED}:
        if track.next_reset_date is None or not track.reset_interval:
            raise UnsupportedAdjustablePenaltyCaseError(
                f"Adjustable track={track.label} is missing next reset date or reset interval."
            )
        if as_of is None:
            raise UnsupportedAdjustablePenaltyCaseError(
                f"As-of date is required to evaluate adjustable track penalty window for track={track.label}."
            )

        months_until_reset = _months_until(track.next_reset_date, as_of)
        if months_until_reset <= 0:
            return 0, "REG116_ADJUSTABLE_AT_RESET_WINDOW", ["ADJUSTABLE_TRACK_AT_RESET_WINDOW"]

        return (
            min(track.remaining_term_months, months_until_reset),
            "REG116_ADJUSTABLE_UNTIL_NEXT_RESET",
            ["ADJUSTABLE_TRACK_TRUNCATED_TO_NEXT_RESET"],
        )

    raise ValidationError(f"Unsupported track type for Regulation 116 penalty: {track.track_type.value}")


def calculate_regulation_116_track_penalty(
    *,
    track: MortgageTrack,
    market_context: MarketContext,
    market_rate_records: list[MortgageRateBucketRecord],
    default_years_since_origination: Decimal | None = None,
) -> TrackPenaltyBreakdown:
    track_id = track.track_id or track.label

    if track.track_type == TrackType.PRIME_FLOATING:
        return TrackPenaltyBreakdown(
            track_id=track_id,
            track_label=track.label,
            applicable=False,
            reason_code="REG116_NOT_APPLICABLE_PRIME",
            remaining_months=track.remaining_term_months,
            market_rate_bucket=None,
            market_annual_rate_percent=None,
            contract_annual_rate_percent=track.current_rate,
            market_monthly_rate=None,
            contract_monthly_rate=None,
            pv_market_nis=None,
            pv_contract_nis=None,
            economic_loss_nis=Decimal("0"),
            discount_factor=None,
            penalty_before_discount_nis=Decimal("0"),
            penalty_after_discount_nis=Decimal("0"),
            rounded_penalty_nis=Decimal("0"),
            warning_codes=[],
        )

    penalty_months, reason_code, warning_codes = _penalty_window_months(track, as_of=market_context.as_of)
    if penalty_months == 0:
        return TrackPenaltyBreakdown(
            track_id=track_id,
            track_label=track.label,
            applicable=False,
            reason_code=reason_code,
            remaining_months=0,
            market_rate_bucket=None,
            market_annual_rate_percent=None,
            contract_annual_rate_percent=track.current_rate,
            market_monthly_rate=None,
            contract_monthly_rate=None,
            pv_market_nis=None,
            pv_contract_nis=None,
            economic_loss_nis=Decimal("0"),
            discount_factor=None,
            penalty_before_discount_nis=Decimal("0"),
            penalty_after_discount_nis=Decimal("0"),
            rounded_penalty_nis=Decimal("0"),
            warning_codes=warning_codes,
        )

    years_since_origination = _track_years_since_origination(
        track=track,
        default_years_since_origination=default_years_since_origination,
    )
    contract_rate = _contract_rate_for_penalty(track)
    summary = calculate_total_monthly_payment(tracks=[track], context=market_context)
    track_result = summary.track_results[0]
    principal = track_result.adjusted_balance if track_result.adjusted_balance is not None else track.outstanding_balance
    stream = build_remaining_payment_stream(
        principal_nis=principal,
        annual_rate_percent=contract_rate,
        remaining_months=penalty_months,
    )

    try:
        bucket_record = select_regulation_116_market_rate(
            records=market_rate_records,
            remaining_months=penalty_months,
            track_family="general",
        )
    except MarketDataBucketLookupError as exc:
        raise MissingPenaltyInputError(
            f"Relevant market-rate bucket data is required for Regulation 116 penalty calculation on track={track.label}"
        ) from exc
    market_rate = bucket_record.annual_rate_percent
    pv_market = present_value_of_payment_stream(payment_stream=stream, annual_rate_percent=market_rate)
    pv_contract = present_value_of_payment_stream(payment_stream=stream, annual_rate_percent=contract_rate)

    # Sign convention:
    # - When the contract/original rate is above the relevant market rate, the same future
    #   payment stream has a higher present value under the market discount curve than under the
    #   contract-rate curve, which represents the bank's compensable economic loss on early repayment.
    # - The borrower should only pay when that economic loss is positive.
    economic_loss = max(Decimal("0"), pv_market - pv_contract)
    discount_factor = statutory_discount_factor(years_since_origination)
    penalty_after_discount = economic_loss * discount_factor
    rounded_penalty = penalty_after_discount.quantize(ONE_NIS, rounding=ROUND_HALF_UP)

    final_reason_code = reason_code if economic_loss > 0 else "REG116_NO_ECONOMIC_LOSS"
    return TrackPenaltyBreakdown(
        track_id=track_id,
        track_label=track.label,
        applicable=True,
        reason_code=final_reason_code,
        remaining_months=penalty_months,
        market_rate_bucket=bucket_record.bucket_code,
        market_annual_rate_percent=market_rate,
        contract_annual_rate_percent=contract_rate,
        market_monthly_rate=convert_annual_to_monthly_rate(market_rate),
        contract_monthly_rate=convert_annual_to_monthly_rate(contract_rate),
        pv_market_nis=pv_market,
        pv_contract_nis=pv_contract,
        economic_loss_nis=economic_loss,
        discount_factor=discount_factor,
        penalty_before_discount_nis=economic_loss,
        penalty_after_discount_nis=penalty_after_discount,
        rounded_penalty_nis=rounded_penalty,
        warning_codes=warning_codes,
        metadata={
            "principal_for_penalty": str(principal),
            "years_since_origination": str(years_since_origination),
        },
    )
