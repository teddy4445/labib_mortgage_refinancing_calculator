from __future__ import annotations

from typing import Any

from backend.app.domain.exceptions import MarketDataParseError
from backend.app.infrastructure.market_data.connectors.base import BaseMarketDataConnector


class CpiSeriesConnector(BaseMarketDataConnector):
    def static_payload(self) -> dict[str, Any]:
        return {
            "records": [
                {"period": "2026-01", "indexValue": 115.2, "releaseDate": "2026-02-15"},
                {"period": "2026-02", "indexValue": 115.5, "releaseDate": "2026-03-15"},
                {"period": "2026-03", "indexValue": 115.8, "releaseDate": "2026-04-15"},
            ]
        }

    def parse_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_records = self._coalesce(payload, "records", "series")
        if not isinstance(raw_records, list):
            raise MarketDataParseError("CPI payload must include a records list.")

        records = []
        for record in raw_records:
            period = self._coalesce(record, "period", "month")
            index_value = self._coalesce(record, "index_value", "indexValue", "value")
            release_date = self._coalesce(record, "release_date", "releaseDate", "date")
            if period is None or index_value is None or release_date is None:
                raise MarketDataParseError("Each CPI record must include period, index value, and release date.")
            records.append({"period": period, "index_value": index_value, "release_date": release_date})
        return {"records": records}
