from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.circuit_breaker import provider_health
from app.core.providers import ProviderType, provider_registry
from app.integrations.free_data_sources import (
    FreeDataAggregator,
    NormalizedCurrencyRate,
    NormalizedEconomicIndicator,
    NormalizedMarketQuote,
)
from app.models.market_data import MarketType, StockExchange, WatchlistSymbol


@dataclass(slots=True)
class MarketSymbolSpec:
    symbol: str
    name: str
    market_type: MarketType
    exchange: StockExchange | None
    priority: int = 0
    is_active: bool = True
    is_real_estate_company: bool = False
    segment: str = "core"


UAE_CORE_SYMBOLS: list[MarketSymbolSpec] = [
    MarketSymbolSpec("EMAAR", "Emaar Properties", MarketType.STOCK, StockExchange.DFM, priority=100, is_real_estate_company=True, segment="uae"),
    MarketSymbolSpec("DAMAC", "DAMAC Properties", MarketType.STOCK, StockExchange.DFM, priority=95, is_real_estate_company=True, segment="uae"),
    MarketSymbolSpec("DEYAAR", "Deyaar Development", MarketType.STOCK, StockExchange.DFM, priority=92, is_real_estate_company=True, segment="uae"),
    MarketSymbolSpec("UPP", "Union Properties", MarketType.STOCK, StockExchange.DFM, priority=88, is_real_estate_company=True, segment="uae"),
    MarketSymbolSpec("AMLAK", "Amlak Finance", MarketType.STOCK, StockExchange.DFM, priority=85, is_real_estate_company=True, segment="uae"),
    MarketSymbolSpec("ALDAR", "Aldar Properties", MarketType.STOCK, StockExchange.ADX, priority=94, is_real_estate_company=True, segment="uae"),
    MarketSymbolSpec("ESHRAQ", "Eshraq Investments", MarketType.STOCK, StockExchange.ADX, priority=82, is_real_estate_company=True, segment="uae"),
    MarketSymbolSpec("RAKPROP", "RAK Properties", MarketType.STOCK, StockExchange.ADX, priority=80, is_real_estate_company=True, segment="uae"),
]

GLOBAL_REALESTATE_SYMBOLS: list[MarketSymbolSpec] = [
    MarketSymbolSpec("AMT", "American Tower", MarketType.STOCK, StockExchange.NYSE, priority=70, segment="global_real_estate"),
    MarketSymbolSpec("PLD", "Prologis", MarketType.STOCK, StockExchange.NYSE, priority=68, segment="global_real_estate"),
    MarketSymbolSpec("CCI", "Crown Castle", MarketType.STOCK, StockExchange.NYSE, priority=66, segment="global_real_estate"),
    MarketSymbolSpec("SPG", "Simon Property Group", MarketType.STOCK, StockExchange.NYSE, priority=64, segment="global_real_estate"),
    MarketSymbolSpec("O", "Realty Income", MarketType.STOCK, StockExchange.NYSE, priority=62, segment="global_real_estate"),
    MarketSymbolSpec("LEN", "Lennar", MarketType.STOCK, StockExchange.NYSE, priority=60, segment="global_real_estate"),
    MarketSymbolSpec("DHI", "D.R. Horton", MarketType.STOCK, StockExchange.NYSE, priority=58, segment="global_real_estate"),
    MarketSymbolSpec("NVR", "NVR", MarketType.STOCK, StockExchange.NYSE, priority=56, segment="global_real_estate"),
]

INDEX_SYMBOLS: list[MarketSymbolSpec] = [
    MarketSymbolSpec("^DFM", "Dubai Financial Market General Index", MarketType.INDEX, None, priority=100, segment="indices"),
    MarketSymbolSpec("^GSPC", "S&P 500", MarketType.INDEX, None, priority=80, segment="indices"),
    MarketSymbolSpec("^DJI", "Dow Jones Industrial Average", MarketType.INDEX, None, priority=78, segment="indices"),
    MarketSymbolSpec("^IXIC", "NASDAQ Composite", MarketType.INDEX, None, priority=76, segment="indices"),
    MarketSymbolSpec("^FTSE", "FTSE 100", MarketType.INDEX, None, priority=72, segment="indices"),
]

COMMODITY_SYMBOLS: list[MarketSymbolSpec] = [
    MarketSymbolSpec("GC=F", "Gold Futures", MarketType.COMMODITY, None, priority=70, segment="commodities"),
    MarketSymbolSpec("SI=F", "Silver Futures", MarketType.COMMODITY, None, priority=68, segment="commodities"),
    MarketSymbolSpec("CL=F", "Crude Oil Futures", MarketType.COMMODITY, None, priority=74, segment="commodities"),
    MarketSymbolSpec("BZ=F", "Brent Oil Futures", MarketType.COMMODITY, None, priority=76, segment="commodities"),
]


class MarketAggregator:
    def __init__(self) -> None:
        self.registry = provider_registry

    async def aggregate_full_market_data(
        self,
        *,
        watchlist_symbols: list[WatchlistSymbol] | None = None,
    ) -> dict[str, object]:
        watchlist_symbols = watchlist_symbols or []
        aggregator = FreeDataAggregator()
        try:
            uae_specs = self._merge_specs(watchlist_symbols, UAE_CORE_SYMBOLS)
            all_specs = self._merge_specs(
                [],
                [
                    *uae_specs,
                    *GLOBAL_REALESTATE_SYMBOLS,
                    *INDEX_SYMBOLS,
                    *COMMODITY_SYMBOLS,
                ],
            )
            tasks = {
                "quotes": aggregator.fetch_market_quotes(all_specs),
                "currencies": self._fetch_currency_rates(aggregator),
                "economic_indicators": self._fetch_economic_indicators(aggregator),
            }

            results = await self._gather(tasks)
            segmented_quotes = self._segment_quotes(results["quotes"], all_specs)
            provider_stats = self._build_provider_stats(results)

            return {
                "uae_stocks": segmented_quotes["uae_stocks"],
                "global_real_estate": segmented_quotes["global_real_estate"],
                "indices": segmented_quotes["indices"],
                "commodities": segmented_quotes["commodities"],
                "currencies": results["currencies"],
                "economic_indicators": results["economic_indicators"],
                "provider_stats": provider_stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "market_status": self._get_market_status(),
            }
        finally:
            await aggregator.close()

    async def _gather(self, tasks: dict[str, object]) -> dict[str, object]:
        names = list(tasks.keys())
        values = list(tasks.values())
        results = await asyncio.gather(*values, return_exceptions=True)
        output: dict[str, object] = {}
        for name, result in zip(names, results):
            output[name] = [] if isinstance(result, Exception) else result
        return output

    async def _fetch_currency_rates(self, aggregator: FreeDataAggregator) -> list[NormalizedCurrencyRate]:
        providers = self.registry.get_providers_by_type(ProviderType.MARKET)
        for provider in providers:
            await provider_health.warmup(provider.name)
        return await aggregator.fetch_currency_rates()

    async def _fetch_economic_indicators(self, aggregator: FreeDataAggregator) -> list[NormalizedEconomicIndicator]:
        indicators = await aggregator.fetch_world_bank_indicators()
        indicators.extend(await aggregator.fetch_fred_indicators())
        try:
            trading_economics = await aggregator.fetch_trading_economics_indicators()
        except Exception:
            trading_economics = []

        for item in trading_economics:
            value = item.get("value")
            if value is None:
                continue
            indicators.append(
                NormalizedEconomicIndicator(
                    indicator_name=item["category"],
                    indicator_code=item.get("ticker") or item["category"].lower().replace(" ", "_"),
                    value=float(value),
                    unit=item.get("unit"),
                    period=item.get("date"),
                    timestamp=datetime.now(timezone.utc),
                    source="Trading Economics",
                    description=item["category"],
                )
            )
        return indicators

    @staticmethod
    def _merge_specs(
        watchlist_symbols: list[WatchlistSymbol],
        defaults: list[MarketSymbolSpec],
    ) -> list[MarketSymbolSpec]:
        merged: dict[str, MarketSymbolSpec] = {item.symbol.upper(): item for item in defaults}
        for item in watchlist_symbols:
            merged[item.symbol.upper()] = MarketSymbolSpec(
                symbol=item.symbol.upper(),
                name=item.name,
                market_type=item.market_type,
                exchange=item.exchange,
                priority=item.priority,
                is_real_estate_company=item.is_real_estate_company,
                segment="uae",
            )
        return sorted(merged.values(), key=lambda item: (-item.priority, item.symbol))

    @staticmethod
    def _segment_quotes(
        quotes: list[NormalizedMarketQuote],
        specs: list[MarketSymbolSpec],
    ) -> dict[str, list[NormalizedMarketQuote]]:
        segment_by_symbol = {spec.symbol.upper(): spec.segment for spec in specs}
        buckets: dict[str, list[NormalizedMarketQuote]] = {
            "uae_stocks": [],
            "global_real_estate": [],
            "indices": [],
            "commodities": [],
        }
        for quote in quotes:
            segment = segment_by_symbol.get(quote.symbol.upper())
            if segment == "uae":
                buckets["uae_stocks"].append(quote)
            elif segment == "global_real_estate":
                buckets["global_real_estate"].append(quote)
            elif segment == "indices":
                buckets["indices"].append(quote)
            elif segment == "commodities":
                buckets["commodities"].append(quote)
        return buckets

    @staticmethod
    def _build_provider_stats(results: dict[str, object]) -> dict[str, dict[str, object]]:
        provider_counts: dict[str, int] = {}
        for quote in results.get("quotes", []):
            provider_counts[quote.provider] = provider_counts.get(quote.provider, 0) + 1

        for rate in results.get("currencies", []):
            provider_counts[rate.source] = provider_counts.get(rate.source, 0) + 1

        for indicator in results.get("economic_indicators", []):
            provider_key = indicator.source.lower().replace(":", "_").replace(" ", "_")
            provider_counts[provider_key] = provider_counts.get(provider_key, 0) + 1

        stats: dict[str, dict[str, object]] = {}
        for provider_name, count in sorted(provider_counts.items()):
            state = provider_health.snapshot(provider_name)
            stats[provider_name] = {
                "count": count,
                "state": state.state,
                "reliability": state.reliability,
                "last_error": state.last_error,
            }
        return stats

    @staticmethod
    def _get_market_status() -> dict[str, str]:
        now = datetime.now(timezone.utc)
        weekday = now.weekday()
        hour = now.hour
        uae_open = weekday <= 3 and 6 <= hour < 10
        us_open = weekday <= 4 and 14 <= hour < 21
        return {
            "uae_markets": "open" if uae_open else "closed",
            "us_markets": "open" if us_open else "closed",
            "timestamp": now.isoformat(),
        }


market_aggregator = MarketAggregator()
