from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.metrics import market_updates
from app.integrations.alpha_vantage_client import AlphaVantageClient
from app.integrations.free_data_sources import FreeDataAggregator
from app.schemas.market_data import MarketDataResponse
from app.models.market_data import CurrencyRate, EconomicIndicator, MarketData, MarketType, StockExchange, WatchlistSymbol


class MarketService:
    @staticmethod
    async def _invalidate_market_cache(symbol: str | None = None) -> None:
        await cache.delete_pattern("market_latest:*")
        await cache.delete(cache.MARKET_REAL_ESTATE)
        await cache.delete(cache.MARKET_OVERVIEW)
        await cache.delete(cache.MARKET_WEATHER)
        if symbol:
            await cache.delete(cache.MARKET_SYMBOL.format(symbol=symbol.upper()))

    @staticmethod
    def _watchlist_to_market_snapshot(watchlist: WatchlistSymbol) -> dict:
        return {
            "id": watchlist.id,
            "symbol": watchlist.symbol,
            "name": watchlist.name,
            "market_type": watchlist.market_type,
            "exchange": watchlist.exchange,
            "price": 0.0,
            "change": 0.0,
            "change_percent": 0.0,
            "volume": 0,
            "market_cap": None,
            "currency": "AED",
            "data_timestamp": datetime.now(timezone.utc),
            "is_live_data": False,
            "data_source": "watchlist_fallback",
        }

    @staticmethod
    def _market_row_to_snapshot(row: MarketData) -> dict:
        payload = MarketDataResponse.model_validate(row).model_dump(mode="json")
        payload["is_live_data"] = False
        payload["data_source"] = "historical_snapshot"
        return payload

    @staticmethod
    async def _get_latest_known_snapshots(
        db: AsyncSession,
        symbols: list[str],
    ) -> dict[str, dict]:
        normalized_symbols = [symbol.upper() for symbol in symbols if symbol]
        if not normalized_symbols:
            return {}
        subquery = (
            select(
                MarketData.symbol,
                func.max(MarketData.data_timestamp).label("max_timestamp"),
            )
            .where(MarketData.symbol.in_(normalized_symbols), MarketData.price > 0)
            .group_by(MarketData.symbol)
            .subquery()
        )
        query = select(MarketData).join(
            subquery,
            and_(
                MarketData.symbol == subquery.c.symbol,
                MarketData.data_timestamp == subquery.c.max_timestamp,
            ),
        )
        result = await db.execute(query)
        rows = result.scalars().all()
        return {row.symbol.upper(): MarketService._market_row_to_snapshot(row) for row in rows}

    @staticmethod
    async def _get_watchlist_fallback(
        db: AsyncSession,
        market_type: MarketType | None = None,
        limit: int = 50,
        real_estate_only: bool = False,
    ) -> list[dict]:
        query = (
            select(WatchlistSymbol)
            .where(WatchlistSymbol.is_active.is_(True))
            .order_by(WatchlistSymbol.priority.desc(), WatchlistSymbol.symbol.asc())
        )
        if market_type is not None:
            query = query.where(WatchlistSymbol.market_type == market_type)
        if real_estate_only:
            query = query.where(WatchlistSymbol.is_real_estate_company.is_(True))

        result = await db.execute(query.limit(limit))
        return [MarketService._watchlist_to_market_snapshot(item) for item in result.scalars().all()]

    @staticmethod
    async def update_stock_quote(
        db: AsyncSession,
        symbol: str,
        client: AlphaVantageClient,
    ) -> MarketData | None:
        try:
            quote_data = await client.get_quote(symbol)
            if not quote_data:
                return None

            watchlist_result = await db.execute(
                select(WatchlistSymbol).where(WatchlistSymbol.symbol == symbol.upper())
            )
            watchlist = watchlist_result.scalar_one_or_none()
            if watchlist is None:
                logger.warning("Symbol {} not found in watchlist", symbol)
                return None

            price = float(quote_data.get("05. price", 0) or 0)
            if price <= 0:
                return None

            market_data = MarketData(
                symbol=watchlist.symbol,
                name=watchlist.name,
                market_type=watchlist.market_type,
                exchange=watchlist.exchange,
                price=price,
                open_price=float(quote_data.get("02. open", 0) or 0),
                high_price=float(quote_data.get("03. high", 0) or 0),
                low_price=float(quote_data.get("04. low", 0) or 0),
                close_price=float(quote_data.get("08. previous close", 0) or 0),
                previous_close=float(quote_data.get("08. previous close", 0) or 0),
                volume=int(float(quote_data.get("06. volume", 0) or 0)),
                market_cap=None,
                change=float(quote_data.get("09. change", 0) or 0),
                change_percent=float(str(quote_data.get("10. change percent", "0")).replace("%", "") or 0),
                data_timestamp=datetime.now(timezone.utc),
            )
            db.add(market_data)
            await db.commit()
            await db.refresh(market_data)
            await MarketService._invalidate_market_cache(symbol)
            market_updates.inc()
            logger.info("Updated market quote for {}", symbol)
            return market_data
        except Exception as exc:
            logger.error("Error updating market quote for {}: {}", symbol, str(exc))
            return None

    @staticmethod
    async def update_currency_rate(
        db: AsyncSession,
        from_currency: str,
        to_currency: str,
        client: AlphaVantageClient,
    ) -> CurrencyRate | None:
        try:
            rate_data = await client.get_currency_exchange_rate(from_currency, to_currency)
            if not rate_data:
                return None

            currency_rate = CurrencyRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=float(rate_data.get("5. Exchange Rate", 0) or 0),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(currency_rate)
            await db.commit()
            await db.refresh(currency_rate)
            logger.info("Updated currency rate {}/{}", from_currency, to_currency)
            return currency_rate
        except Exception as exc:
            logger.error("Error updating currency rate {}/{}: {}", from_currency, to_currency, str(exc))
            return None

    @staticmethod
    async def store_market_snapshot(
        db: AsyncSession,
        *,
        symbol: str,
        name: str,
        market_type: MarketType,
        exchange: StockExchange | None,
        price: float,
        open_price: float | None,
        high_price: float | None,
        low_price: float | None,
        previous_close: float | None,
        volume: int,
        market_cap: float | None,
        change: float,
        change_percent: float,
        currency: str = "AED",
        primary_provider: str | None = None,
        data_quality_score: float | None = None,
        confidence_level: str | None = None,
        asset_class: str | None = None,
        region: str | None = None,
    ) -> MarketData:
        market_data = MarketData(
            symbol=symbol.upper(),
            name=name,
            market_type=market_type,
            exchange=exchange,
            price=price,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=price,
            previous_close=previous_close,
            volume=volume,
            market_cap=market_cap,
            change=change,
            change_percent=change_percent,
            currency=currency,
            primary_provider=primary_provider,
            data_quality_score=data_quality_score,
            confidence_level=confidence_level,
            asset_class=asset_class or market_type.value,
            region=region,
            data_timestamp=datetime.now(timezone.utc),
        )
        db.add(market_data)
        await db.commit()
        await db.refresh(market_data)
        await MarketService._invalidate_market_cache(symbol)
        market_updates.inc()
        return market_data

    @staticmethod
    async def store_currency_rate_snapshot(
        db: AsyncSession,
        *,
        from_currency: str,
        to_currency: str,
        rate: float,
        timestamp: datetime,
    ) -> CurrencyRate:
        currency_rate = CurrencyRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            timestamp=timestamp,
        )
        db.add(currency_rate)
        await db.commit()
        await db.refresh(currency_rate)
        await cache.delete(cache.MARKET_OVERVIEW)
        return currency_rate

    @staticmethod
    async def store_economic_indicator(
        db: AsyncSession,
        *,
        indicator_name: str,
        indicator_code: str,
        value: float,
        unit: str | None,
        period: str | None,
        timestamp: datetime,
        source: str,
        description: str | None,
        country: str = "UAE",
    ) -> EconomicIndicator:
        indicator = EconomicIndicator(
            indicator_name=indicator_name,
            indicator_code=indicator_code,
            value=value,
            unit=unit,
            country=country,
            period=period,
            timestamp=timestamp,
            source=source,
            description=description,
        )
        db.add(indicator)
        await db.commit()
        await db.refresh(indicator)
        await cache.delete(cache.MARKET_OVERVIEW)
        return indicator

    @staticmethod
    async def get_latest_market_data(
        db: AsyncSession,
        market_type: MarketType | None = None,
        limit: int = 50,
    ) -> list[MarketData] | list[dict]:
        cache_suffix = market_type.value if market_type is not None else "all"
        cache_key = f"market_latest:{cache_suffix}:{limit}"
        cached_market = await cache.get(cache_key)
        if cached_market is not None:
            return cached_market

        subquery = (
            select(
                MarketData.symbol,
                func.max(MarketData.data_timestamp).label("max_timestamp"),
            )
            .where(MarketData.price > 0)
            .group_by(MarketData.symbol)
            .subquery()
        )

        query = select(MarketData).join(
            subquery,
            and_(
                MarketData.symbol == subquery.c.symbol,
                MarketData.data_timestamp == subquery.c.max_timestamp,
            ),
        )

        if market_type is not None:
            query = query.where(MarketData.market_type == market_type)

        query = query.order_by(desc(MarketData.data_timestamp)).limit(limit)
        result = await db.execute(query)
        rows = list(result.scalars().all())
        serialized = [MarketDataResponse.model_validate(row).model_dump(mode="json") for row in rows]
        if len(serialized) < limit:
            fallback_rows = await MarketService._get_watchlist_fallback(db, market_type=market_type, limit=limit)
            known_snapshots = await MarketService._get_latest_known_snapshots(
                db,
                [fallback["symbol"] for fallback in fallback_rows],
            )
            existing_symbols = {item["symbol"] for item in serialized}
            for fallback in fallback_rows:
                if fallback["symbol"] in existing_symbols:
                    continue
                serialized.append(known_snapshots.get(fallback["symbol"], fallback))
                existing_symbols.add(fallback["symbol"])
                if len(serialized) >= limit:
                    break
        await cache.set(cache_key, serialized, ttl=60)
        return serialized

    @staticmethod
    async def get_real_estate_companies(db: AsyncSession) -> list[MarketData] | list[dict]:
        cached_companies = await cache.get_cached_market_real_estate()
        if cached_companies is not None:
            return [MarketDataResponse.model_validate(company) for company in cached_companies]

        watchlist_result = await db.execute(
            select(WatchlistSymbol).where(
                WatchlistSymbol.is_real_estate_company.is_(True),
                WatchlistSymbol.is_active.is_(True),
            )
        )
        watchlist_symbols = watchlist_result.scalars().all()
        if not watchlist_symbols:
            return []

        symbols = [symbol.symbol for symbol in watchlist_symbols]
        subquery = (
            select(
                MarketData.symbol,
                func.max(MarketData.data_timestamp).label("max_timestamp"),
            )
            .where(MarketData.symbol.in_(symbols), MarketData.price > 0)
            .group_by(MarketData.symbol)
            .subquery()
        )
        query = select(MarketData).join(
            subquery,
            and_(
                MarketData.symbol == subquery.c.symbol,
                MarketData.data_timestamp == subquery.c.max_timestamp,
            ),
        ).order_by(MarketData.symbol.asc())
        result = await db.execute(query)
        companies = list(result.scalars().all())
        serialized = [MarketDataResponse.model_validate(company).model_dump(mode="json") for company in companies]
        if len(serialized) < len(symbols):
            known_snapshots = await MarketService._get_latest_known_snapshots(db, symbols)
            fallback_companies = await MarketService._get_watchlist_fallback(
                db,
                market_type=MarketType.STOCK,
                real_estate_only=True,
                limit=len(symbols),
            )
            existing_symbols = {item["symbol"] for item in serialized}
            for fallback in fallback_companies:
                if fallback["symbol"] in existing_symbols:
                    continue
                serialized.append(known_snapshots.get(fallback["symbol"], fallback))
                existing_symbols.add(fallback["symbol"])
        await cache.cache_market_real_estate(serialized, ttl=120)
        return [MarketDataResponse.model_validate(company) for company in serialized]

    @staticmethod
    async def get_latest_market_data_for_symbols(
        db: AsyncSession,
        symbols: list[str],
        *,
        limit: int | None = None,
        include_watchlist_fallback: bool = False,
    ) -> list[MarketData] | list[dict]:
        normalized_symbols = [symbol.upper() for symbol in symbols if symbol]
        if not normalized_symbols:
            return []

        cache_key = f"market_latest:symbols:{','.join(normalized_symbols)}:{limit or len(normalized_symbols)}:{int(include_watchlist_fallback)}"
        cached_market = await cache.get(cache_key)
        if cached_market is not None:
            return cached_market

        subquery = (
            select(
                MarketData.symbol,
                func.max(MarketData.data_timestamp).label("max_timestamp"),
            )
            .where(MarketData.symbol.in_(normalized_symbols), MarketData.price > 0)
            .group_by(MarketData.symbol)
            .subquery()
        )

        query = select(MarketData).join(
            subquery,
            and_(
                MarketData.symbol == subquery.c.symbol,
                MarketData.data_timestamp == subquery.c.max_timestamp,
            ),
        )
        result = await db.execute(query)
        rows = list(result.scalars().all())
        order_index = {symbol: index for index, symbol in enumerate(normalized_symbols)}
        rows.sort(key=lambda row: (order_index.get(row.symbol, len(order_index)), -row.data_timestamp.timestamp()))

        serialized = [MarketDataResponse.model_validate(row).model_dump(mode="json") for row in rows]
        if include_watchlist_fallback:
            known_snapshots = await MarketService._get_latest_known_snapshots(db, normalized_symbols)
            watchlist_result = await db.execute(
                select(WatchlistSymbol)
                .where(WatchlistSymbol.symbol.in_(normalized_symbols), WatchlistSymbol.is_active.is_(True))
                .order_by(WatchlistSymbol.priority.desc(), WatchlistSymbol.symbol.asc())
            )
            existing_symbols = {item["symbol"] for item in serialized}
            for watchlist in watchlist_result.scalars().all():
                if watchlist.symbol in existing_symbols:
                    continue
                serialized.append(known_snapshots.get(watchlist.symbol, MarketService._watchlist_to_market_snapshot(watchlist)))
                existing_symbols.add(watchlist.symbol)

        if limit is not None:
            serialized = serialized[:limit]

        await cache.set(cache_key, serialized, ttl=60)
        return serialized

    @staticmethod
    async def get_latest_currency_rates(db: AsyncSession, limit: int = 10) -> list[CurrencyRate]:
        subquery = (
            select(
                CurrencyRate.from_currency,
                CurrencyRate.to_currency,
                func.max(CurrencyRate.timestamp).label("max_timestamp"),
            )
            .group_by(CurrencyRate.from_currency, CurrencyRate.to_currency)
            .subquery()
        )
        query = (
            select(CurrencyRate)
            .join(
                subquery,
                and_(
                    CurrencyRate.from_currency == subquery.c.from_currency,
                    CurrencyRate.to_currency == subquery.c.to_currency,
                    CurrencyRate.timestamp == subquery.c.max_timestamp,
                ),
            )
            .order_by(desc(CurrencyRate.timestamp))
            .limit(limit)
        )
        result = await db.execute(query)
        rows = list(result.scalars().all())
        deduped: list[CurrencyRate] = []
        seen_pairs: set[tuple[str, str]] = set()
        for row in rows:
            pair = (row.from_currency, row.to_currency)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            deduped.append(row)
            if len(deduped) >= limit:
                break
        return deduped

    @staticmethod
    async def get_latest_economic_indicators(db: AsyncSession, limit: int = 12) -> list[EconomicIndicator]:
        subquery = (
            select(
                EconomicIndicator.indicator_code,
                func.max(EconomicIndicator.timestamp).label("max_timestamp"),
            )
            .group_by(EconomicIndicator.indicator_code)
            .subquery()
        )
        query = (
            select(EconomicIndicator)
            .join(
                subquery,
                and_(
                    EconomicIndicator.indicator_code == subquery.c.indicator_code,
                    EconomicIndicator.timestamp == subquery.c.max_timestamp,
                ),
            )
            .order_by(desc(EconomicIndicator.timestamp), EconomicIndicator.indicator_name.asc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_symbol_data(db: AsyncSession, symbol: str) -> MarketData | dict | None:
        cached_symbol = await cache.get_cached_market_symbol(symbol)
        if cached_symbol is not None:
            return cached_symbol

        result = await db.execute(
            select(MarketData)
            .where(MarketData.symbol == symbol.upper(), MarketData.price > 0)
            .order_by(MarketData.data_timestamp.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        if latest is not None:
            await cache.cache_market_symbol(
                symbol,
                MarketDataResponse.model_validate(latest).model_dump(mode="json"),
                ttl=60,
            )
            return latest

        watchlist_result = await db.execute(
            select(WatchlistSymbol)
            .where(WatchlistSymbol.symbol == symbol.upper(), WatchlistSymbol.is_active.is_(True))
            .limit(1)
        )
        watchlist = watchlist_result.scalar_one_or_none()
        if watchlist is None:
            return None

        known_snapshots = await MarketService._get_latest_known_snapshots(db, [symbol.upper()])
        fallback_snapshot = known_snapshots.get(symbol.upper(), MarketService._watchlist_to_market_snapshot(watchlist))
        await cache.cache_market_symbol(symbol, fallback_snapshot, ttl=60)
        return fallback_snapshot

    @staticmethod
    async def get_market_weather() -> dict | None:
        cached_weather = await cache.get(cache.MARKET_WEATHER)
        if cached_weather is not None:
            return cached_weather

        aggregator = FreeDataAggregator()
        try:
            snapshot = await aggregator.fetch_market_weather(location_name="Dubai")
        except Exception as exc:
            logger.warning("Unable to fetch market weather: {}", str(exc))
            return None
        finally:
            await aggregator.close()

        if snapshot is None:
            return None

        payload = {
            "location_name": snapshot.location_name,
            "latitude": snapshot.latitude,
            "longitude": snapshot.longitude,
            "temperature_c": snapshot.temperature_c,
            "apparent_temperature_c": snapshot.apparent_temperature_c,
            "humidity_percent": snapshot.humidity_percent,
            "wind_speed_kph": snapshot.wind_speed_kph,
            "weather_code": snapshot.weather_code,
            "weather_summary": snapshot.weather_summary,
            "observed_at": snapshot.observed_at,
            "source": snapshot.source,
        }
        await cache.set(cache.MARKET_WEATHER, payload, ttl=900)
        return payload
