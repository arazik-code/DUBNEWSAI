import asyncio
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.metrics import market_updates
from app.integrations.alpha_vantage_client import AlphaVantageClient
from app.integrations.free_data_sources import FreeDataAggregator
from app.models.sources import DataProvider
from app.schemas.market_data import CurrencyRateResponse, EconomicIndicatorResponse, MarketDataResponse
from app.models.market_data import CurrencyRate, EconomicIndicator, MarketData, MarketType, StockExchange, WatchlistSymbol
from app.services.aggregation.market_aggregator import (
    COMMODITY_SYMBOLS,
    GLOBAL_REALESTATE_SYMBOLS,
    INDEX_SYMBOLS,
    UAE_CORE_SYMBOLS,
    MarketSymbolSpec,
    market_aggregator,
)


class MarketService:
    MAX_DATABASE_VOLUME = 2_147_483_647
    MARKET_REFRESH_COOLDOWN = timedelta(minutes=3)
    SNAPSHOT_FRESHNESS_WINDOW = timedelta(hours=8)
    _market_refresh_lock: asyncio.Lock = asyncio.Lock()
    _last_market_refresh_attempt: datetime | None = None

    @staticmethod
    def _sanitize_float(value: Any, default: float | None = None) -> float | None:
        if value is None:
            return default
        try:
            parsed = float(value)
        except Exception:
            return default
        if not math.isfinite(parsed):
            return default
        return parsed

    @classmethod
    def _serialize_market_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        sanitized = dict(payload)
        sanitized["price"] = cls._sanitize_float(sanitized.get("price"), 0.0) or 0.0
        sanitized["open_price"] = cls._sanitize_float(sanitized.get("open_price"))
        sanitized["high_price"] = cls._sanitize_float(sanitized.get("high_price"))
        sanitized["low_price"] = cls._sanitize_float(sanitized.get("low_price"))
        sanitized["previous_close"] = cls._sanitize_float(sanitized.get("previous_close"))
        sanitized["change"] = cls._sanitize_float(sanitized.get("change"), 0.0) or 0.0
        sanitized["change_percent"] = cls._sanitize_float(sanitized.get("change_percent"), 0.0) or 0.0
        sanitized["market_cap"] = cls._sanitize_float(sanitized.get("market_cap"))
        sanitized["data_quality_score"] = cls._sanitize_float(sanitized.get("data_quality_score"))
        sanitized["volume"] = cls._sanitize_volume(sanitized.get("volume"))
        return sanitized

    @classmethod
    def _serialize_market_row(cls, row: MarketData) -> dict[str, Any]:
        return cls._serialize_market_payload(
            MarketDataResponse.model_validate(row).model_dump(mode="json")
        )

    @classmethod
    def _serialize_currency_rate(cls, row: CurrencyRate) -> dict[str, Any]:
        payload = CurrencyRateResponse.model_validate(row).model_dump(mode="json")
        payload["rate"] = cls._sanitize_float(payload.get("rate"), 0.0) or 0.0
        return payload

    @classmethod
    def _serialize_economic_indicator(cls, row: EconomicIndicator) -> dict[str, Any]:
        payload = EconomicIndicatorResponse.model_validate(row).model_dump(mode="json")
        payload["value"] = cls._sanitize_float(payload.get("value"), 0.0) or 0.0
        return payload

    @classmethod
    def _sanitize_market_rows(cls, rows: list[Any]) -> list[dict[str, Any]]:
        sanitized_rows: list[dict[str, Any]] = []
        for row in rows:
            if isinstance(row, MarketData):
                sanitized_rows.append(cls._serialize_market_row(row))
            elif isinstance(row, dict):
                sanitized_rows.append(cls._serialize_market_payload(row))
        return sanitized_rows

    @classmethod
    def _sanitize_weather_payload(cls, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if payload is None:
            return None
        sanitized = dict(payload)
        sanitized["latitude"] = cls._sanitize_float(sanitized.get("latitude"), 0.0) or 0.0
        sanitized["longitude"] = cls._sanitize_float(sanitized.get("longitude"), 0.0) or 0.0
        sanitized["temperature_c"] = cls._sanitize_float(sanitized.get("temperature_c"), 0.0) or 0.0
        sanitized["apparent_temperature_c"] = cls._sanitize_float(sanitized.get("apparent_temperature_c"))
        sanitized["wind_speed_kph"] = cls._sanitize_float(sanitized.get("wind_speed_kph"))
        return sanitized

    @classmethod
    def _sanitize_market_overview_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        sanitized = dict(payload)
        for key in ("stocks", "indices", "global_real_estate", "commodities", "real_estate_companies"):
            sanitized[key] = cls._sanitize_market_rows(list(sanitized.get(key) or []))
        sanitized["currencies"] = [
            {
                **dict(item),
                "rate": cls._sanitize_float(dict(item).get("rate"), 0.0) or 0.0,
            }
            for item in list(sanitized.get("currencies") or [])
            if isinstance(item, dict)
        ]
        sanitized["economic_indicators"] = [
            {
                **dict(item),
                "value": cls._sanitize_float(dict(item).get("value"), 0.0) or 0.0,
            }
            for item in list(sanitized.get("economic_indicators") or [])
            if isinstance(item, dict)
        ]
        sanitized["provider_utilization"] = [
            {
                **dict(item),
                "type": str(dict(item).get("type") or "unknown"),
                "circuit_state": str(dict(item).get("circuit_state") or "closed"),
                "total_calls": cls._coerce_int(dict(item).get("total_calls")),
                "successful_calls": cls._coerce_int(dict(item).get("successful_calls")),
                "failed_calls": cls._coerce_int(dict(item).get("failed_calls")),
            }
            for item in list(sanitized.get("provider_utilization") or [])
            if isinstance(item, dict)
        ]
        provider_mix = sanitized.get("provider_mix")
        if isinstance(provider_mix, dict):
            sanitized["provider_mix"] = {
                **provider_mix,
                "active_count": cls._coerce_int(provider_mix.get("active_count")),
                "dormant_count": cls._coerce_int(provider_mix.get("dormant_count")),
                "top_contributors": [str(item) for item in list(provider_mix.get("top_contributors") or []) if item],
                "dormant_providers": [str(item) for item in list(provider_mix.get("dormant_providers") or []) if item],
            }
        sanitized["weather"] = cls._sanitize_weather_payload(sanitized.get("weather"))
        return sanitized

    @staticmethod
    def _coerce_int(value: Any, default: int = 0) -> int:
        try:
            return int(value or default)
        except Exception:
            return default

    @classmethod
    def _sanitize_volume(cls, value: int | None) -> int:
        if value is None:
            return 0
        return max(0, min(int(value), cls.MAX_DATABASE_VOLUME))

    @staticmethod
    async def _invalidate_market_cache(symbol: str | None = None) -> None:
        await cache.delete_pattern("market_latest:*")
        await cache.delete(cache.MARKET_REAL_ESTATE)
        await cache.delete(cache.MARKET_OVERVIEW)
        await cache.delete(cache.MARKET_WEATHER)
        if symbol:
            await cache.delete(cache.MARKET_SYMBOL.format(symbol=symbol.upper()))

    @classmethod
    def _watchlist_to_market_snapshot(cls, watchlist: WatchlistSymbol) -> dict:
        return cls._serialize_market_payload({
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
        })

    @classmethod
    def _market_row_to_snapshot(cls, row: MarketData) -> dict:
        payload = cls._serialize_market_row(row)
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
    def _canonical_symbol_specs() -> list[MarketSymbolSpec]:
        return [
            *UAE_CORE_SYMBOLS,
            *GLOBAL_REALESTATE_SYMBOLS,
            *INDEX_SYMBOLS,
            *COMMODITY_SYMBOLS,
        ]

    @classmethod
    async def ensure_canonical_watchlist(cls, db: AsyncSession) -> None:
        specs = cls._canonical_symbol_specs()
        symbols = [spec.symbol.upper() for spec in specs]
        existing_result = await db.execute(
            select(WatchlistSymbol).where(WatchlistSymbol.symbol.in_(symbols))
        )
        existing = {row.symbol.upper(): row for row in existing_result.scalars().all()}

        changed = False
        for spec in specs:
            symbol = spec.symbol.upper()
            row = existing.get(symbol)
            if row is None:
                db.add(
                    WatchlistSymbol(
                        symbol=symbol,
                        name=spec.name,
                        market_type=spec.market_type,
                        exchange=spec.exchange,
                        is_active=spec.is_active,
                        priority=spec.priority,
                        is_real_estate_company=spec.is_real_estate_company,
                    )
                )
                changed = True
                continue

            updates = {
                "name": spec.name,
                "market_type": spec.market_type,
                "exchange": spec.exchange,
                "is_active": spec.is_active,
                "priority": spec.priority,
                "is_real_estate_company": spec.is_real_estate_company,
            }
            for field_name, value in updates.items():
                if getattr(row, field_name) != value:
                    setattr(row, field_name, value)
                    changed = True

        if changed:
            await db.commit()
            await cls._invalidate_market_cache()

    @staticmethod
    def _count_live_rows(rows: list[dict[str, Any]]) -> int:
        return sum(1 for row in rows if row.get("is_live_data", True) is not False)

    @staticmethod
    def _latest_timestamp(rows: list[dict[str, Any]]) -> datetime | None:
        timestamps: list[datetime] = []
        for row in rows:
            value = row.get("data_timestamp")
            if isinstance(value, datetime):
                timestamps.append(value if value.tzinfo else value.replace(tzinfo=timezone.utc))
                continue
            if isinstance(value, str):
                try:
                    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except Exception:
                    continue
                timestamps.append(parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc))
        return max(timestamps) if timestamps else None

    @classmethod
    async def _run_market_refresh(cls) -> None:
        from app.tasks.aggregation_tasks import _aggregate_full_market_data

        await _aggregate_full_market_data()

    @classmethod
    async def ensure_market_surface_ready(cls, db: AsyncSession, *, force: bool = False) -> None:
        await cls.ensure_canonical_watchlist(db)

        now = datetime.now(timezone.utc)
        core_rows = await cls.get_latest_market_data_for_symbols(
            db,
            [item.symbol for item in UAE_CORE_SYMBOLS],
            limit=len(UAE_CORE_SYMBOLS),
            include_watchlist_fallback=True,
        )
        global_rows = await cls.get_latest_market_data_for_symbols(
            db,
            [item.symbol for item in GLOBAL_REALESTATE_SYMBOLS],
            limit=8,
            include_watchlist_fallback=True,
        )
        index_rows = await cls.get_latest_market_data(db, MarketType.INDEX, limit=4)
        currencies = await cls.get_latest_currency_rates(db, limit=4)
        indicators = await cls.get_latest_economic_indicators(db, limit=4)

        latest_core_timestamp = cls._latest_timestamp(core_rows if isinstance(core_rows, list) else [])
        core_is_stale = latest_core_timestamp is None or (now - latest_core_timestamp) > cls.SNAPSHOT_FRESHNESS_WINDOW
        needs_refresh = force or core_is_stale or cls._count_live_rows(core_rows if isinstance(core_rows, list) else []) < 4 or len(global_rows) < 3 or len(index_rows) < 1 or len(currencies) < 2 or len(indicators) < 3

        if not needs_refresh:
            return

        async with cls._market_refresh_lock:
            cooldown_active = (
                not force
                and cls._last_market_refresh_attempt is not None
                and (now - cls._last_market_refresh_attempt) < cls.MARKET_REFRESH_COOLDOWN
            )
            if cooldown_active:
                return

            cls._last_market_refresh_attempt = now
            try:
                await cls._run_market_refresh()
            except Exception as exc:
                logger.warning("Inline market refresh did not complete: {}", str(exc))

    @classmethod
    def _build_board_health(
        cls,
        *,
        board: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        live_rows = cls._count_live_rows(rows)
        fallback_rows = max(0, len(rows) - live_rows)
        last_updated = cls._latest_timestamp(rows)
        if len(rows) == 0:
            status = "empty"
        elif live_rows == len(rows):
            status = "live"
        elif live_rows > 0:
            status = "mixed"
        else:
            status = "fallback"
        providers = sorted({str(row.get("primary_provider")) for row in rows if row.get("primary_provider")})
        return {
            "board": board,
            "status": status,
            "total_rows": len(rows),
            "live_rows": live_rows,
            "fallback_rows": fallback_rows,
            "last_updated": last_updated,
            "providers": providers,
        }

    @staticmethod
    async def _get_provider_utilization(db: AsyncSession, limit: int = 8) -> list[dict[str, Any]]:
        result = await db.execute(
            select(DataProvider)
            .where(DataProvider.is_enabled.is_(True))
            .order_by(desc(DataProvider.successful_calls), desc(DataProvider.total_calls), DataProvider.name.asc())
            .limit(limit)
        )
        providers = result.scalars().all()
        return [
            {
                "provider": provider.name,
                "type": provider.type or "unknown",
                "health": "healthy" if provider.is_healthy else "degraded",
                "circuit_state": provider.circuit_state or "closed",
                "total_calls": MarketService._coerce_int(provider.total_calls),
                "successful_calls": MarketService._coerce_int(provider.successful_calls),
                "failed_calls": MarketService._coerce_int(provider.failed_calls),
                "last_success_at": provider.last_success_at,
                "last_failure_at": provider.last_failure_at,
            }
            for provider in providers
        ]

    @staticmethod
    async def _safe_collection(
        label: str,
        fetcher: Any,
        default: Any,
    ) -> Any:
        try:
            return await fetcher()
        except Exception as exc:
            logger.warning("Market overview partial failure in {}: {}", label, str(exc))
            return default

    @staticmethod
    def _build_market_highlights(
        *,
        stocks: list[dict[str, Any]],
        indices: list[dict[str, Any]],
        currencies: list[dict[str, Any]],
        indicators: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        highlights: list[dict[str, str]] = []

        movers = [row for row in stocks if row.get("is_live_data", True)]
        if movers:
            top_mover = max(movers, key=lambda row: abs(float(row.get("change_percent") or 0.0)))
            highlights.append(
                {
                    "title": "Top UAE mover",
                    "value": f"{top_mover['symbol']} {float(top_mover.get('change_percent') or 0.0):+.2f}%",
                    "context": f"{top_mover['name']} is leading the local board move right now.",
                }
            )

        live_indices = [row for row in indices if row.get("is_live_data", True)]
        if live_indices:
            lead_index = max(live_indices, key=lambda row: abs(float(row.get("change_percent") or 0.0)))
            highlights.append(
                {
                    "title": "Index pressure",
                    "value": f"{lead_index['symbol']} {float(lead_index.get('change_percent') or 0.0):+.2f}%",
                    "context": f"{lead_index['name']} is setting the benchmark tone for the board.",
                }
            )

        if currencies:
            primary_pair = currencies[0]
            highlights.append(
                {
                    "title": "FX anchor",
                    "value": f"{primary_pair['from_currency']}/{primary_pair['to_currency']} {float(primary_pair.get('rate') or 0.0):.4f}",
                    "context": "Currency context is available for the active market read.",
                }
            )

        if indicators:
            primary_indicator = indicators[0]
            highlights.append(
                {
                    "title": "Macro pulse",
                    "value": primary_indicator["indicator_name"],
                    "context": f"Latest macro context comes from {primary_indicator.get('source') or 'the active feed stack'}.",
                }
            )

        return highlights[:4]

    @staticmethod
    def _build_market_brief(
        *,
        stocks: list[dict[str, Any]],
        indices: list[dict[str, Any]],
        currencies: list[dict[str, Any]],
        indicators: list[dict[str, Any]],
        board_health: list[dict[str, Any]],
    ) -> dict[str, Any]:
        live_uae_rows = [row for row in stocks if row.get("is_live_data", True)]
        lead_symbol = max(
            live_uae_rows,
            key=lambda row: abs(float(row.get("change_percent") or 0.0)),
        ) if live_uae_rows else None
        live_indices = [row for row in indices if row.get("is_live_data", True)]
        lead_index = max(
            live_indices,
            key=lambda row: abs(float(row.get("change_percent") or 0.0)),
        ) if live_indices else None
        primary_currency = currencies[0] if currencies else None
        primary_indicator = indicators[0] if indicators else None
        degraded_boards = [board for board in board_health if board.get("status") in {"fallback", "empty"}]

        headline_parts = []
        if lead_symbol:
            headline_parts.append(
                f"{lead_symbol['symbol']} is the lead local mover at {float(lead_symbol.get('change_percent') or 0.0):+.2f}%"
            )
        if lead_index:
            headline_parts.append(f"{lead_index['symbol']} is setting the benchmark tone")
        if not headline_parts:
            headline_parts.append("DUBNEWSAI is holding a mixed but actionable market read")

        focus_areas: list[str] = []
        if primary_currency:
            focus_areas.append(
                f"FX anchor: {primary_currency['from_currency']}/{primary_currency['to_currency']} at {float(primary_currency.get('rate') or 0.0):.4f}"
            )
        if primary_indicator:
            focus_areas.append(f"Macro pulse: {primary_indicator['indicator_name']}")
        if degraded_boards:
            focus_areas.append(
                f"Coverage watch: {', '.join(board['board'] for board in degraded_boards[:2])}"
            )
        if not focus_areas:
            focus_areas.append("Coverage is available across local boards, FX, and macro context.")

        confidence = "high"
        if degraded_boards:
            confidence = "medium" if any(board.get("live_rows", 0) > 0 for board in degraded_boards) else "low"

        narrative = " ".join(
            part
            for part in [
                f"The current market read blends {len(stocks)} UAE rows, {len(indices)} indices, {len(currencies)} FX pairs, and {len(indicators)} macro signals.",
                " ".join(focus_areas[:2]),
                "Fallback rows remain visible where provider coverage is partial so the board never collapses into empty space."
                if degraded_boards else "Live and fallback coverage are balanced so the board remains decision-ready even while some sources rotate.",
            ]
            if part
        )

        return {
            "headline": ". ".join(headline_parts) + ".",
            "narrative": narrative.strip(),
            "focus_areas": focus_areas[:4],
            "confidence": confidence,
        }

    @staticmethod
    def _build_coverage_alerts(
        board_health: list[dict[str, Any]],
        boards: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for board in board_health:
            board_name = str(board.get("board") or "Board")
            rows = boards.get(board_name, [])
            affected_symbols = [str(row.get("symbol")) for row in rows if row.get("is_live_data", True) is False][:5]
            status = str(board.get("status") or "unknown")
            if status == "live":
                continue
            if status == "empty":
                severity = "high"
                message = f"{board_name} has no verified rows in the active snapshot."
                action = "Force a refresh cycle and widen the provider rotation for this board."
            elif status == "fallback":
                severity = "medium"
                message = f"{board_name} is currently leaning on verified reference rows instead of fresh live quotes."
                action = "Keep the board visible, but prioritize alternate providers for the missing symbols."
            else:
                severity = "low"
                message = f"{board_name} is live, but part of the board is still being backfilled from the fallback layer."
                action = "Monitor the affected symbols and preserve current live rows while the next sync completes."
            alerts.append(
                {
                    "board": board_name,
                    "severity": severity,
                    "message": message,
                    "action": action,
                    "affected_symbols": affected_symbols,
                }
            )
        return alerts[:6]

    @staticmethod
    def _build_provider_mix(provider_utilization: list[dict[str, Any]]) -> dict[str, Any]:
        active = [
            item["provider"]
            for item in provider_utilization
            if int(item.get("successful_calls") or 0) > 0 or int(item.get("total_calls") or 0) > 0
        ]
        dormant = [
            item["provider"]
            for item in provider_utilization
            if int(item.get("successful_calls") or 0) == 0 and int(item.get("total_calls") or 0) == 0
        ]
        ranked = sorted(
            provider_utilization,
            key=lambda item: (int(item.get("successful_calls") or 0), int(item.get("total_calls") or 0)),
            reverse=True,
        )
        return {
            "active_count": len(active),
            "dormant_count": len(dormant),
            "top_contributors": [item["provider"] for item in ranked[:5] if item.get("provider")],
            "dormant_providers": dormant[:6],
        }

    @classmethod
    async def get_priority_market_board(cls, db: AsyncSession, limit: int = 24) -> list[dict[str, Any]]:
        await cls.ensure_market_surface_ready(db)
        board_specs = [*UAE_CORE_SYMBOLS, *GLOBAL_REALESTATE_SYMBOLS]
        board_rows = await cls.get_latest_market_data_for_symbols(
            db,
            [item.symbol for item in board_specs],
            limit=len(board_specs),
            include_watchlist_fallback=True,
        )
        ordered_symbols = {spec.symbol.upper(): index for index, spec in enumerate(board_specs)}
        rows = list(board_rows)
        rows.sort(key=lambda row: ordered_symbols.get(str(row.get("symbol", "")).upper(), len(ordered_symbols)))
        return rows[:limit]

    @classmethod
    async def get_market_overview_payload(cls, db: AsyncSession) -> dict[str, Any]:
        cached_overview = await cache.get(cache.MARKET_OVERVIEW)
        if cached_overview is not None:
            try:
                return cls._sanitize_market_overview_payload(dict(cached_overview))
            except Exception:
                await cache.delete(cache.MARKET_OVERVIEW)

        try:
            await cls.ensure_market_surface_ready(db)
        except Exception as exc:
            logger.warning("Market surface refresh preparation failed: {}", str(exc))

        stocks = await cls._safe_collection(
            "uae_board",
            lambda: cls.get_latest_market_data_for_symbols(
                db,
                [item.symbol for item in UAE_CORE_SYMBOLS],
                limit=20,
                include_watchlist_fallback=True,
            ),
            [],
        )
        indices = await cls._safe_collection(
            "indices",
            lambda: cls.get_latest_market_data(db, MarketType.INDEX, limit=10),
            [],
        )
        global_real_estate = await cls._safe_collection(
            "global_real_estate",
            lambda: cls.get_latest_market_data_for_symbols(
                db,
                [item.symbol for item in GLOBAL_REALESTATE_SYMBOLS],
                limit=16,
                include_watchlist_fallback=True,
            ),
            [],
        )
        commodities = await cls._safe_collection(
            "commodities",
            lambda: cls.get_latest_market_data_for_symbols(
                db,
                [item.symbol for item in COMMODITY_SYMBOLS],
                limit=6,
                include_watchlist_fallback=True,
            ),
            [],
        )
        real_estate = await cls._safe_collection("real_estate_companies", lambda: cls.get_real_estate_companies(db), [])
        currencies = await cls._safe_collection(
            "currencies",
            lambda: cls.get_latest_currency_rates(db, limit=10),
            [],
        )
        economic_indicator_rows = await cls._safe_collection(
            "economic_indicators",
            lambda: cls.get_latest_economic_indicators(db, limit=12),
            [],
        )
        weather = await cls._safe_collection("weather", cls.get_market_weather, None)
        provider_utilization = await cls._safe_collection(
            "provider_utilization",
            lambda: cls._get_provider_utilization(db),
            [],
        )

        stocks_rows = list(stocks)
        index_rows = list(indices)
        global_rows = list(global_real_estate)
        commodity_rows = list(commodities)
        real_estate_rows = list(real_estate)
        currencies = [cls._serialize_currency_rate(item) if isinstance(item, CurrencyRate) else dict(item) for item in currencies]
        economic_indicators = [
            cls._serialize_economic_indicator(item) if isinstance(item, EconomicIndicator) else dict(item)
            for item in economic_indicator_rows
        ]

        total_symbols = len(stocks_rows) + len(global_rows) + len(index_rows) + len(commodity_rows)
        live_symbols = (
            cls._count_live_rows(stocks_rows)
            + cls._count_live_rows(global_rows)
            + cls._count_live_rows(index_rows)
            + cls._count_live_rows(commodity_rows)
        )
        board_health = [
            cls._build_board_health(board="UAE market board", rows=stocks_rows),
            cls._build_board_health(board="Global real-estate board", rows=global_rows),
            cls._build_board_health(board="Indices", rows=index_rows),
            cls._build_board_health(board="Commodities", rows=commodity_rows),
        ]
        provider_mix = cls._build_provider_mix(provider_utilization)

        payload = {
            "stocks": stocks_rows,
            "indices": index_rows,
            "global_real_estate": global_rows,
            "commodities": commodity_rows,
            "currencies": currencies,
            "economic_indicators": economic_indicators,
            "real_estate_companies": real_estate_rows,
            "weather": weather,
            "market_status": market_aggregator._get_market_status(),
            "board_health": board_health,
            "coverage_snapshot": {
                "tracked_symbols": total_symbols,
                "live_symbols": live_symbols,
                "fallback_symbols": max(0, total_symbols - live_symbols),
                "fx_pairs": len(currencies),
                "macro_indicators": len(economic_indicators),
                "provider_count": len(provider_utilization),
            },
            "provider_utilization": provider_utilization,
            "provider_mix": provider_mix,
            "intelligence_highlights": cls._build_market_highlights(
                stocks=stocks_rows,
                indices=index_rows,
                currencies=currencies,
                indicators=economic_indicators,
            ),
            "market_brief": cls._build_market_brief(
                stocks=stocks_rows,
                indices=index_rows,
                currencies=currencies,
                indicators=economic_indicators,
                board_health=board_health,
            ),
            "coverage_alerts": cls._build_coverage_alerts(
                board_health,
                {
                    "UAE market board": stocks_rows,
                    "Global real-estate board": global_rows,
                    "Indices": index_rows,
                    "Commodities": commodity_rows,
                },
            ),
        }
        payload = cls._sanitize_market_overview_payload(payload)
        await cache.set(cache.MARKET_OVERVIEW, payload, ttl=60)
        return payload

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
                volume=MarketService._sanitize_volume(int(float(quote_data.get("06. volume", 0) or 0))),
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
        price = MarketService._sanitize_float(price, 0.0) or 0.0
        open_price = MarketService._sanitize_float(open_price)
        high_price = MarketService._sanitize_float(high_price)
        low_price = MarketService._sanitize_float(low_price)
        previous_close = MarketService._sanitize_float(previous_close)
        market_cap = MarketService._sanitize_float(market_cap)
        change = MarketService._sanitize_float(change, 0.0) or 0.0
        change_percent = MarketService._sanitize_float(change_percent, 0.0) or 0.0
        data_quality_score = MarketService._sanitize_float(data_quality_score)
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
            volume=MarketService._sanitize_volume(volume),
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
        rate = MarketService._sanitize_float(rate, 0.0) or 0.0
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
        value = MarketService._sanitize_float(value, 0.0) or 0.0
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
            return MarketService._sanitize_market_rows(list(cached_market))

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
        serialized = [MarketService._serialize_market_row(row) for row in rows]
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
            return MarketService._sanitize_market_rows(list(cached_companies))

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
        serialized = [MarketService._serialize_market_row(company) for company in companies]
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
        return serialized

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
            return MarketService._sanitize_market_rows(list(cached_market))

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

        serialized = [MarketService._serialize_market_row(row) for row in rows]
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
            return MarketService._serialize_market_payload(dict(cached_symbol))

        result = await db.execute(
            select(MarketData)
            .where(MarketData.symbol == symbol.upper(), MarketData.price > 0)
            .order_by(MarketData.data_timestamp.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        if latest is not None:
            payload = MarketService._serialize_market_row(latest)
            await cache.cache_market_symbol(
                symbol,
                payload,
                ttl=60,
            )
            return payload

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
            return MarketService._sanitize_weather_payload(dict(cached_weather))

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
        payload = MarketService._sanitize_weather_payload(payload)
        await cache.set(cache.MARKET_WEATHER, payload, ttl=900)
        return payload
