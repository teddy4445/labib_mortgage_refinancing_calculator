from __future__ import annotations

from backend.app.services.market_data_service import MarketDataRefreshBatchResult, MarketDataRefreshResult, MarketDataService


class DataGatheringManager:
    def __init__(self, market_data_service: MarketDataService) -> None:
        self._market_data_service = market_data_service

    async def refresh_source(self, source_key: str) -> MarketDataRefreshResult:
        return await self._market_data_service.refresh_source(source_key)

    async def refresh_all_market_data(self) -> MarketDataRefreshBatchResult:
        return await self._market_data_service.refresh_all_market_data()

    async def run_daily_refresh(self) -> dict[str, str]:
        batch_result = await self.refresh_all_market_data()
        return {result.source_key: result.status for result in batch_result.results}
