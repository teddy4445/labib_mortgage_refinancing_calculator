from __future__ import annotations

from backend.app.domain.exceptions import MarketDataBucketLookupError
from backend.app.domain.market_data.models import MortgageRateBucketRecord
from backend.app.domain.market_data.selectors import lookup_mortgage_bucket_by_remaining_months


def select_regulation_116_market_rate(
    *,
    records: list[MortgageRateBucketRecord],
    remaining_months: int,
    track_family: str = "general",
) -> MortgageRateBucketRecord:
    bucket = lookup_mortgage_bucket_by_remaining_months(remaining_months)
    matching = [
        record
        for record in records
        if record.bucket_code == bucket.bucket_code and record.track_family == track_family
    ]
    if not matching:
        raise MarketDataBucketLookupError(
            f"No market-rate bucket record found for remaining_months={remaining_months}, track_family={track_family}"
        )
    return matching[0]
