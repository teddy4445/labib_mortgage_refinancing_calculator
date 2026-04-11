from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import httpx

from backend.app.domain.exceptions import MarketDataFetchError, MarketDataParseError
from backend.app.domain.market_data.models import MarketDataSourceDefinition


class BaseMarketDataConnector(ABC):
    connector_version = "phase4-market-data-v1"

    def __init__(
        self,
        *,
        source_definition: MarketDataSourceDefinition,
        endpoint: str | None,
        use_static_fallbacks: bool,
        timeout_seconds: int,
    ) -> None:
        self.source_definition = source_definition
        self.endpoint = endpoint
        self.use_static_fallbacks = use_static_fallbacks
        self.timeout_seconds = timeout_seconds

    async def fetch_payload(self) -> dict[str, Any]:
        if self.endpoint:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.endpoint)
                response.raise_for_status()
                try:
                    payload = response.json()
                except Exception as exc:  # noqa: BLE001
                    raise MarketDataParseError(
                        f"{self.source_definition.source_key} returned a non-JSON payload."
                    ) from exc
                return self.parse_payload(payload)

        if self.use_static_fallbacks:
            return self.parse_payload(self.static_payload())

        raise MarketDataFetchError(
            f"No endpoint configured for {self.source_definition.source_key} and static fallbacks are disabled."
        )

    @staticmethod
    def _coalesce(payload: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in payload and payload[key] is not None:
                return payload[key]
        return None

    @staticmethod
    def _today_iso() -> str:
        return date.today().isoformat()

    @abstractmethod
    def static_payload(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def parse_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
