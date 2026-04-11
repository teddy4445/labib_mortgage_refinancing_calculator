from __future__ import annotations

from typing import Any

from backend.app.domain.exceptions import MarketDataParseError
from backend.app.infrastructure.market_data.connectors.base import BaseMarketDataConnector


class MortgageRateBucketsConnector(BaseMarketDataConnector):
    def static_payload(self) -> dict[str, Any]:
        return {
            "effectiveDate": self._today_iso(),
            "buckets": [
                {"bucketCode": "up_to_5_years", "monthsMin": 1, "monthsMax": 60, "annualRatePercent": 4.1},
                {"bucketCode": "five_to_ten_years", "monthsMin": 61, "monthsMax": 120, "annualRatePercent": 4.3},
                {"bucketCode": "ten_to_fifteen_years", "monthsMin": 121, "monthsMax": 180, "annualRatePercent": 4.5},
                {"bucketCode": "fifteen_to_twenty_years", "monthsMin": 181, "monthsMax": 240, "annualRatePercent": 4.7},
                {"bucketCode": "twenty_to_twenty_five_years", "monthsMin": 241, "monthsMax": 300, "annualRatePercent": 4.9},
                {"bucketCode": "twenty_five_to_thirty_years", "monthsMin": 301, "monthsMax": 360, "annualRatePercent": 5.1},
            ],
        }

    def parse_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        effective_date = self._coalesce(payload, "effective_date", "effectiveDate", "date")
        raw_buckets = self._coalesce(payload, "buckets", "records")
        if effective_date is None or not isinstance(raw_buckets, list):
            raise MarketDataParseError("Mortgage-rate bucket payload must include effective date and bucket list.")

        buckets = []
        for bucket in raw_buckets:
            bucket_code = self._coalesce(bucket, "bucket_code", "bucketCode")
            min_months = self._coalesce(bucket, "remaining_months_min", "monthsMin", "minMonths")
            max_months = self._coalesce(bucket, "remaining_months_max", "monthsMax", "maxMonths")
            annual_rate_percent = self._coalesce(bucket, "annual_rate_percent", "annualRatePercent", "ratePercent")
            if bucket_code is None or min_months is None or max_months is None or annual_rate_percent is None:
                raise MarketDataParseError("Each mortgage-rate bucket must include code, min/max months, and rate.")
            buckets.append(
                {
                    "bucket_code": bucket_code,
                    "remaining_months_min": min_months,
                    "remaining_months_max": max_months,
                    "annual_rate_percent": annual_rate_percent,
                    "track_family": self._coalesce(bucket, "track_family", "trackFamily") or "general",
                }
            )

        return {"effective_date": effective_date, "buckets": buckets}
