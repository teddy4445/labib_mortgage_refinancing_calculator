from __future__ import annotations

from typing import Any

from backend.app.domain.exceptions import MarketDataParseError
from backend.app.infrastructure.market_data.connectors.base import BaseMarketDataConnector


class BoiBaseRateConnector(BaseMarketDataConnector):
    def static_payload(self) -> dict[str, Any]:
        return {
            "effectiveDate": self._today_iso(),
            "ratePercent": 4.5,
        }

    def parse_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        effective_date = self._coalesce(payload, "effective_date", "effectiveDate", "date")
        annual_rate_percent = self._coalesce(payload, "annual_rate_percent", "ratePercent", "rate")
        if effective_date is None or annual_rate_percent is None:
            raise MarketDataParseError("Base-rate payload must include effective date and annual rate percent.")
        return {
            "effective_date": effective_date,
            "annual_rate_percent": annual_rate_percent,
        }
