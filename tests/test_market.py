import asyncio
from datetime import datetime, timezone

from app.integrations.free_data_sources import FreeDataAggregator, NormalizedCurrencyRate
from app.database import AsyncSessionLocal
from app.models.market_data import CurrencyRate, MarketData, MarketType, StockExchange, WatchlistSymbol
from app.services.market_service import MarketService


async def seed_market_records() -> None:
    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                WatchlistSymbol(
                    symbol="EMAAR",
                    name="Emaar Properties",
                    market_type=MarketType.STOCK,
                    exchange=StockExchange.DFM,
                    is_real_estate_company=True,
                    priority=10,
                ),
                WatchlistSymbol(
                    symbol="DFM",
                    name="Dubai Financial Market General Index",
                    market_type=MarketType.INDEX,
                    exchange=StockExchange.DFM,
                    priority=10,
                ),
                MarketData(
                    symbol="EMAAR",
                    name="Emaar Properties",
                    market_type=MarketType.STOCK,
                    exchange=StockExchange.DFM,
                    price=8.75,
                    previous_close=8.5,
                    change=0.25,
                    change_percent=2.94,
                    volume=1500000,
                    market_cap=15000000000,
                    data_timestamp=datetime.now(timezone.utc),
                ),
                MarketData(
                    symbol="DFM",
                    name="Dubai Financial Market General Index",
                    market_type=MarketType.INDEX,
                    exchange=StockExchange.DFM,
                    price=4200.5,
                    previous_close=4185.0,
                    change=15.5,
                    change_percent=0.37,
                    volume=0,
                    market_cap=None,
                    data_timestamp=datetime.now(timezone.utc),
                ),
                CurrencyRate(
                    from_currency="USD",
                    to_currency="AED",
                    rate=3.6725,
                    timestamp=datetime.now(timezone.utc),
                ),
            ]
        )
        await db.commit()


class FakeAlphaVantageClient:
    async def get_quote(self, symbol: str) -> dict:
        return {
            "05. price": "9.10",
            "02. open": "8.90",
            "03. high": "9.20",
            "04. low": "8.80",
            "08. previous close": "8.70",
            "06. volume": "2200000",
            "09. change": "0.40",
            "10. change percent": "4.60%",
        }

    async def get_currency_exchange_rate(self, from_currency: str, to_currency: str) -> dict:
        return {
            "5. Exchange Rate": "3.6725",
        }


def test_market_overview_and_symbol_endpoints(client, monkeypatch):
    asyncio.run(seed_market_records())

    async def fake_ensure_market_surface_ready(cls, db, force: bool = False):
        return None

    async def fake_market_weather():
        return None

    monkeypatch.setattr(MarketService, "ensure_market_surface_ready", classmethod(fake_ensure_market_surface_ready))
    monkeypatch.setattr(MarketService, "get_market_weather", staticmethod(fake_market_weather))

    overview_response = client.get("/api/v1/market/overview")
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    assert any(item["symbol"] == "EMAAR" for item in overview_payload["stocks"])
    assert len(overview_payload["indices"]) == 1
    assert len(overview_payload["currencies"]) == 1
    assert len(overview_payload["real_estate_companies"]) == 1
    assert overview_payload["real_estate_companies"][0]["symbol"] == "EMAAR"
    assert "market_brief" in overview_payload
    assert "coverage_alerts" in overview_payload
    assert "provider_mix" in overview_payload
    assert overview_payload["coverage_snapshot"]["tracked_symbols"] >= 1

    symbol_response = client.get("/api/v1/market/symbol/EMAAR")
    assert symbol_response.status_code == 200
    assert symbol_response.json()["name"] == "Emaar Properties"

    real_estate_response = client.get("/api/v1/market/real-estate-companies")
    assert real_estate_response.status_code == 200
    assert real_estate_response.json()[0]["symbol"] == "EMAAR"


def test_market_service_updates_quote_and_currency_rate():
    async def run_assertions() -> None:
        async with AsyncSessionLocal() as db:
            db.add(
                WatchlistSymbol(
                    symbol="EMAAR",
                    name="Emaar Properties",
                    market_type=MarketType.STOCK,
                    exchange=StockExchange.DFM,
                    is_real_estate_company=True,
                    priority=10,
                )
            )
            await db.commit()

            client = FakeAlphaVantageClient()
            quote = await MarketService.update_stock_quote(db, "EMAAR", client)
            rate = await MarketService.update_currency_rate(db, "USD", "AED", client)

            assert quote is not None
            assert quote.price == 9.10
            assert quote.change_percent == 4.6
            assert rate is not None
            assert rate.rate == 3.6725

    asyncio.run(run_assertions())


def test_market_overview_sanitizes_nullable_provider_metrics():
    payload = MarketService._sanitize_market_overview_payload(
        {
            "stocks": [],
            "indices": [],
            "global_real_estate": [],
            "commodities": [],
            "currencies": [],
            "economic_indicators": [],
            "real_estate_companies": [],
            "provider_utilization": [
                {
                    "provider": "newsapi",
                    "type": None,
                    "health": "healthy",
                    "circuit_state": None,
                    "total_calls": None,
                    "successful_calls": None,
                    "failed_calls": None,
                }
            ],
            "provider_mix": {
                "active_count": None,
                "dormant_count": None,
                "top_contributors": ["newsapi"],
                "dormant_providers": [None, "gnews"],
            },
        }
    )

    provider = payload["provider_utilization"][0]
    assert provider["type"] == "unknown"
    assert provider["circuit_state"] == "closed"
    assert provider["total_calls"] == 0
    assert payload["provider_mix"]["active_count"] == 0
    assert payload["provider_mix"]["dormant_providers"] == ["gnews"]


def test_currency_rate_merge_uses_consensus_and_supporting_sources():
    merged = FreeDataAggregator._merge_currency_rates_for_pair(
        [
            NormalizedCurrencyRate(
                from_currency="AED",
                to_currency="USD",
                rate=0.2722,
                timestamp=datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc),
                source="frankfurter",
            ),
            NormalizedCurrencyRate(
                from_currency="AED",
                to_currency="USD",
                rate=0.2723,
                timestamp=datetime(2026, 4, 13, 12, 5, tzinfo=timezone.utc),
                source="exchange_rate_api",
            ),
            NormalizedCurrencyRate(
                from_currency="AED",
                to_currency="USD",
                rate=0.2721,
                timestamp=datetime(2026, 4, 13, 12, 10, tzinfo=timezone.utc),
                source="currencyapi",
            ),
        ]
    )

    assert round(merged.rate, 4) == 0.2722
    assert merged.source == "frankfurter"
    assert merged.supporting_sources == ["exchange_rate_api", "currencyapi"]
