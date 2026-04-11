from __future__ import annotations

from decimal import Decimal

import pytest

from backend.app.domain.exceptions import MissingFieldError, UnsupportedTrackTypeError, ValidationError
from backend.app.domain.models import MarketContext, MortgageTrack, TrackType
from backend.app.domain.totals import calculate_total_monthly_payment
from backend.app.domain.tracks import calculate_track_payment
from backend.app.domain.tracks.cpi import adjust_balance_for_cpi


def test_prime_floating_track_uses_boi_plus_prime_spread_plus_margin() -> None:
    track = MortgageTrack(
        label="Prime",
        track_type=TrackType.PRIME_FLOATING,
        outstanding_balance=Decimal("300000"),
        current_rate=None,
        remaining_term_months=240,
        bank_margin=Decimal("-0.5"),
    )
    result = calculate_track_payment(track, MarketContext(boi_base_rate=Decimal("4.0")))
    assert result.effective_annual_rate == Decimal("5.0")
    assert float(result.monthly_payment) == pytest.approx(1961.509398, abs=1e-6)
    assert int(result.monthly_payment.quantize(Decimal("1"))) == 1962
    assert result.prepayment_penalty_applies is False


def test_fixed_linked_track_adjusts_only_outstanding_balance_by_cpi() -> None:
    track = MortgageTrack(
        label="Linked fixed",
        track_type=TrackType.FIXED_LINKED,
        outstanding_balance=Decimal("300000"),
        current_rate=Decimal("2.0"),
        remaining_term_months=180,
        original_cpi=Decimal("92.5"),
    )
    result = calculate_track_payment(track, MarketContext(current_cpi=Decimal("115.0")))
    assert float(result.adjusted_balance) == pytest.approx(372972.972973, abs=1e-6)
    assert float(result.monthly_payment) == pytest.approx(2397.005822, abs=1e-6)
    assert int(result.monthly_payment.quantize(Decimal("1"))) == 2397


def test_adjustable_non_linked_preserves_reset_metadata() -> None:
    track = MortgageTrack(
        label="Adjustable",
        track_type=TrackType.ADJUSTABLE_NON_LINKED,
        outstanding_balance=Decimal("200000"),
        current_rate=Decimal("4.2"),
        remaining_term_months=180,
        reset_interval="60m",
    )
    result = calculate_track_payment(track, MarketContext())
    assert result.metadata["calculation_mode"] == "adjustable_non_linked"
    assert result.metadata["reset_interval"] == "60m"


def test_total_monthly_payment_aggregates_breakdown_and_totals() -> None:
    tracks = [
        MortgageTrack(
            label="Fixed",
            track_type=TrackType.FIXED_NON_LINKED,
            outstanding_balance=Decimal("500000"),
            current_rate=Decimal("3.5"),
            remaining_term_months=240,
        ),
        MortgageTrack(
            label="Prime",
            track_type=TrackType.PRIME_FLOATING,
            outstanding_balance=Decimal("300000"),
            current_rate=None,
            remaining_term_months=240,
            bank_margin=Decimal("-0.5"),
        ),
        MortgageTrack(
            label="Linked",
            track_type=TrackType.FIXED_LINKED,
            outstanding_balance=Decimal("200000"),
            current_rate=Decimal("2.0"),
            remaining_term_months=180,
            original_cpi=Decimal("92.5"),
        ),
    ]
    summary = calculate_total_monthly_payment(
        tracks=tracks,
        context=MarketContext(boi_base_rate=Decimal("4.0"), current_cpi=Decimal("115.0")),
    )
    assert len(summary.track_results) == 3
    assert summary.total_outstanding_balance == Decimal("1000000")
    assert summary.total_adjusted_balance > summary.total_outstanding_balance
    assert summary.total_monthly_payment > 0


def test_increasing_cpi_does_not_reduce_adjusted_balance() -> None:
    lower_cpi_balance = adjust_balance_for_cpi(Decimal("300000"), Decimal("92.5"), Decimal("100.0"))
    higher_cpi_balance = adjust_balance_for_cpi(Decimal("300000"), Decimal("92.5"), Decimal("115.0"))
    assert higher_cpi_balance > lower_cpi_balance


def test_track_type_normalization_rejects_unknown_types() -> None:
    with pytest.raises(UnsupportedTrackTypeError):
        TrackType.from_raw("balloon")


def test_linked_track_requires_original_cpi() -> None:
    track = MortgageTrack(
        label="Broken linked",
        track_type=TrackType.FIXED_LINKED,
        outstanding_balance=Decimal("300000"),
        current_rate=Decimal("2.0"),
        remaining_term_months=180,
    )
    with pytest.raises(MissingFieldError):
        calculate_track_payment(track, MarketContext(current_cpi=Decimal("115.0")))


def test_prime_track_requires_boi_rate() -> None:
    track = MortgageTrack(
        label="Prime",
        track_type=TrackType.PRIME_FLOATING,
        outstanding_balance=Decimal("300000"),
        current_rate=None,
        remaining_term_months=240,
        bank_margin=Decimal("-0.5"),
    )
    with pytest.raises(MissingFieldError):
        calculate_track_payment(track, MarketContext())


def test_adjust_balance_rejects_invalid_cpi_values() -> None:
    with pytest.raises(ValidationError):
        adjust_balance_for_cpi(Decimal("300000"), Decimal("0"), Decimal("115.0"))

