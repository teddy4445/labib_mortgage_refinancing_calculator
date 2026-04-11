from __future__ import annotations

from typing import Any

from backend.app.domain.exceptions import MarketDataParseError
from backend.app.infrastructure.market_data.connectors.base import BaseMarketDataConnector


class InflationExpectationsConnector(BaseMarketDataConnector):
    def static_payload(self) -> dict[str, Any]:
        return {
            "effectiveDate": self._today_iso(),
            "records": [
                {"horizonMonths": 12, "expectedInflationPercent": 2.6},
                {"horizonMonths": 24, "expectedInflationPercent": 2.4},
                {"horizonMonths": 36, "expectedInflationPercent": 2.3},
            ],
        }

    def parse_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        effective_date = self._coalesce(payload, "effective_date", "effectiveDate", "date")
        raw_records = self._coalesce(payload, "records", "series")
        if effective_date is None or not isinstance(raw_records, list):
            raise MarketDataParseError("Inflation-expectations payload must include effective date and records.")

        records = []
        for record in raw_records:
            horizon_months = self._coalesce(record, "horizon_months", "horizonMonths", "horizon")
            expected_inflation_percent = self._coalesce(
                record,
                "expected_inflation_percent",
                "expectedInflationPercent",
                "value",
            )
            if horizon_months is None or expected_inflation_percent is None:
                raise MarketDataParseError(
                    "Each inflation-expectation record must include horizon months and expected inflation percent."
                )
            records.append(
                {
                    "horizon_months": horizon_months,
                    "expected_inflation_percent": expected_inflation_percent,
                }
            )
        return {"effective_date": effective_date, "records": records}
