from __future__ import annotations

from itertools import combinations

from backend.app.domain.exceptions import InvalidScenarioInputError
from backend.app.domain.models import MortgageTrack


def generate_partial_track_subsets(
    tracks: list[MortgageTrack],
    *,
    max_scenarios: int = 64,
) -> tuple[list[tuple[MortgageTrack, ...]], dict[str, str | int]]:
    track_count = len(tracks)
    if track_count < 2:
        raise InvalidScenarioInputError("At least two tracks are required for partial refinance generation.")

    exact_total = (2**track_count) - 2
    if exact_total <= max_scenarios:
        subsets = [
            combo
            for size in range(1, track_count)
            for combo in combinations(tracks, size)
        ]
        return subsets, {"strategy": "exact", "generated": len(subsets), "total_possible": exact_total}

    sorted_tracks = sorted(tracks, key=lambda track: track.outstanding_balance, reverse=True)
    generated: list[tuple[MortgageTrack, ...]] = []
    seen_keys: set[tuple[str, ...]] = set()

    for size in range(1, min(3, track_count)):
        for combo in combinations(sorted_tracks, size):
            key = tuple(sorted(track.label for track in combo))
            if key in seen_keys:
                continue
            generated.append(combo)
            seen_keys.add(key)
            if len(generated) >= max_scenarios:
                return generated, {
                    "strategy": "pruned_balance_priority",
                    "generated": len(generated),
                    "total_possible": exact_total,
                }

    return generated, {
        "strategy": "pruned_balance_priority",
        "generated": len(generated),
        "total_possible": exact_total,
    }
