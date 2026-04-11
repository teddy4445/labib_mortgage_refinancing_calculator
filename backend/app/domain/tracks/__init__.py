from __future__ import annotations

from backend.app.domain.models import MarketContext, MortgageTrack, TrackCalculationResult, TrackType
from backend.app.domain.tracks.cpi import calculate_adjustable_linked, calculate_fixed_linked
from backend.app.domain.tracks.fixed import calculate_adjustable_non_linked, calculate_fixed_non_linked
from backend.app.domain.tracks.prime import calculate_prime_floating


def calculate_track_payment(track: MortgageTrack, context: MarketContext) -> TrackCalculationResult:
    if track.track_type == TrackType.FIXED_NON_LINKED:
        return calculate_fixed_non_linked(track, context)
    if track.track_type == TrackType.FIXED_LINKED:
        return calculate_fixed_linked(track, context)
    if track.track_type == TrackType.PRIME_FLOATING:
        return calculate_prime_floating(track, context)
    if track.track_type == TrackType.ADJUSTABLE_NON_LINKED:
        return calculate_adjustable_non_linked(track, context)
    return calculate_adjustable_linked(track, context)

