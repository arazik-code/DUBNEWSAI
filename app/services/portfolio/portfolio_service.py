from __future__ import annotations

from datetime import datetime, timezone
from math import sqrt
from statistics import mean, pstdev
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.market_data import MarketData
from app.models.portfolio import (
    Portfolio,
    PortfolioHolding,
    PortfolioPerformance,
    PortfolioTransaction,
    PortfolioType,
    TransactionType,
    Watchlist,
    WatchlistItem,
)
from app.services.intelligence.market_intelligence_service import MarketIntelligenceService
from app.services.market_service import MarketService
from app.utils.symbols import normalize_symbol, symbol_metadata


class PortfolioService:
    """Comprehensive portfolio management service."""

    async def _load_portfolio(self, db: AsyncSession, *, portfolio_id: int) -> Portfolio:
        result = await db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.holdings), selectinload(Portfolio.transactions))
            .where(Portfolio.id == portfolio_id)
        )
        return result.scalar_one()

    async def _load_watchlist(self, db: AsyncSession, *, watchlist_id: int) -> Watchlist:
        result = await db.execute(
            select(Watchlist)
            .options(selectinload(Watchlist.items))
            .where(Watchlist.id == watchlist_id)
        )
        return result.scalar_one()

    async def get_asset_catalog(self, db: AsyncSession) -> list[dict[str, Any]]:
        symbols = list(MarketIntelligenceService.SECTOR_MAP.keys())
        snapshots = await MarketService.get_latest_market_data_for_symbols(
            db,
            symbols,
            include_watchlist_fallback=True,
            limit=len(symbols),
        )
        catalog: list[dict[str, Any]] = []
        for item in snapshots:
            metadata = symbol_metadata(item["symbol"])
            catalog.append(
                {
                    "symbol": metadata.display if metadata else item["symbol"],
                    "canonical_symbol": normalize_symbol(item["symbol"]),
                    "name": metadata.name if metadata else item["name"],
                    "sector": MarketIntelligenceService.SECTOR_MAP.get(normalize_symbol(item["symbol"]), item.get("asset_class") or "Other"),
                    "price": float(item.get("price", 0.0)),
                    "change_percent": float(item.get("change_percent", 0.0)),
                    "exchange": metadata.exchange if metadata else item.get("exchange"),
                    "currency": item.get("currency", "AED"),
                }
            )
        return sorted(catalog, key=lambda entry: (entry["sector"], entry["name"]))

    async def create_portfolio(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        name: str,
        description: str | None = None,
        portfolio_type: PortfolioType = PortfolioType.MIXED,
        base_currency: str = "AED",
    ) -> Portfolio:
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description,
            portfolio_type=portfolio_type,
            base_currency=base_currency,
            last_updated=datetime.now(timezone.utc),
        )
        db.add(portfolio)
        await db.commit()
        return await self._load_portfolio(db, portfolio_id=portfolio.id)

    async def list_portfolios(self, db: AsyncSession, *, user_id: int) -> list[Portfolio]:
        result = await db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.holdings))
            .where(Portfolio.user_id == user_id)
            .order_by(Portfolio.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def get_portfolio(self, db: AsyncSession, *, portfolio_id: int, user_id: int) -> Portfolio | None:
        result = await db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.holdings), selectinload(Portfolio.transactions))
            .where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add_transaction(
        self,
        db: AsyncSession,
        *,
        portfolio_id: int,
        transaction_type: TransactionType,
        symbol: str,
        quantity: float,
        price: float,
        transaction_date: datetime,
        fees: float = 0.0,
        notes: str | None = None,
    ) -> dict[str, Any]:
        normalized_symbol = normalize_symbol(symbol)
        total_amount = quantity * price + fees
        transaction = PortfolioTransaction(
            portfolio_id=portfolio_id,
            transaction_type=transaction_type,
            symbol=normalized_symbol,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            fees=fees,
            transaction_date=transaction_date,
            notes=notes,
        )
        db.add(transaction)

        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.symbol == normalized_symbol,
            )
        )
        holding = result.scalar_one_or_none()

        if transaction_type == TransactionType.BUY:
            if holding:
                previous_cost = holding.quantity * holding.average_cost
                holding.quantity += quantity
                holding.average_cost = (previous_cost + total_amount) / holding.quantity if holding.quantity else price
            else:
                holding = PortfolioHolding(
                    portfolio_id=portfolio_id,
                    symbol=normalized_symbol,
                    asset_type="stock",
                    asset_name=(symbol_metadata(normalized_symbol).name if symbol_metadata(normalized_symbol) else normalized_symbol),
                    quantity=quantity,
                    average_cost=price,
                    purchase_date=transaction_date,
                )
                db.add(holding)
                await db.flush()
        elif transaction_type == TransactionType.SELL and holding:
            cost_basis = quantity * holding.average_cost
            proceeds = quantity * price - fees
            realized_gain = proceeds - cost_basis
            holding.realized_gain_loss = (holding.realized_gain_loss or 0.0) + realized_gain
            holding.quantity -= quantity
            if holding.quantity <= 0:
                await db.delete(holding)
                holding = None
        elif transaction_type == TransactionType.DIVIDEND and holding:
            holding.total_dividends = (holding.total_dividends or 0.0) + total_amount

        if holding is not None:
            await db.flush()
            transaction.holding_id = holding.id

        await db.commit()
        await self.update_portfolio_values(db, portfolio_id=portfolio_id)
        return {"transaction": transaction, "holding": holding, "message": "Transaction added successfully"}

    async def create_watchlist(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        name: str,
        description: str | None = None,
        alert_on_change: bool = False,
        change_threshold_percent: float = 5.0,
    ) -> Watchlist:
        watchlist = Watchlist(
            user_id=user_id,
            name=name,
            description=description,
            alert_on_change=alert_on_change,
            change_threshold_percent=change_threshold_percent,
        )
        db.add(watchlist)
        await db.commit()
        return await self._load_watchlist(db, watchlist_id=watchlist.id)

    async def list_watchlists(self, db: AsyncSession, *, user_id: int) -> list[Watchlist]:
        result = await db.execute(
            select(Watchlist)
            .options(selectinload(Watchlist.items))
            .where(Watchlist.user_id == user_id)
            .order_by(Watchlist.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def add_watchlist_item(
        self,
        db: AsyncSession,
        *,
        watchlist_id: int,
        symbol: str,
        asset_type: str | None = None,
        asset_name: str | None = None,
        target_buy_price: float | None = None,
        target_sell_price: float | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> WatchlistItem:
        normalized_symbol = normalize_symbol(symbol)
        current_prices = await self._get_current_prices(db, [normalized_symbol])
        current_price = current_prices.get(normalized_symbol)
        item = WatchlistItem(
            watchlist_id=watchlist_id,
            symbol=normalized_symbol,
            asset_type=asset_type,
            asset_name=asset_name or (symbol_metadata(normalized_symbol).name if symbol_metadata(normalized_symbol) else normalized_symbol),
            target_buy_price=target_buy_price,
            target_sell_price=target_sell_price,
            notes=notes,
            tags=tags or [],
            added_price=current_price,
            current_price=current_price,
            price_change_percent=0.0,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def update_portfolio_values(self, db: AsyncSession, *, portfolio_id: int) -> dict[str, float]:
        portfolio_result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
        portfolio = portfolio_result.scalar_one()
        holdings_result = await db.execute(select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id))
        holdings = list(holdings_result.scalars().all())

        symbols = [holding.symbol for holding in holdings]
        current_prices = await self._get_current_prices(db, symbols)

        total_value = 0.0
        total_cost = 0.0
        for holding in holdings:
            current_price = current_prices.get(holding.symbol, holding.current_price or holding.average_cost)
            holding.current_price = current_price
            holding.current_value = holding.quantity * current_price
            cost_basis = holding.quantity * holding.average_cost
            holding.unrealized_gain_loss = holding.current_value - cost_basis
            holding.unrealized_gain_loss_percent = ((holding.unrealized_gain_loss / cost_basis) * 100) if cost_basis else 0.0
            total_value += holding.current_value
            total_cost += cost_basis

        previous_total = portfolio.total_value_aed or 0.0
        portfolio.total_value_aed = total_value
        portfolio.total_cost_aed = total_cost
        portfolio.total_return_aed = total_value - total_cost
        portfolio.total_return_percent = ((portfolio.total_return_aed / total_cost) * 100) if total_cost else 0.0
        portfolio.last_updated = datetime.now(timezone.utc)
        await db.commit()
        await self._create_performance_snapshot(db, portfolio=portfolio, previous_total=previous_total)
        return {
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_return": round(total_value - total_cost, 2),
            "total_return_percent": round(portfolio.total_return_percent, 2),
        }

    async def get_portfolio_analytics(self, db: AsyncSession, *, portfolio_id: int) -> dict[str, Any]:
        portfolio_result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
        portfolio = portfolio_result.scalar_one()
        holdings_result = await db.execute(select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id))
        holdings = list(holdings_result.scalars().all())

        return {
            "overview": {
                "total_value": portfolio.total_value_aed,
                "total_cost": portfolio.total_cost_aed,
                "total_return": portfolio.total_return_aed,
                "total_return_percent": portfolio.total_return_percent,
                "holdings_count": len(holdings),
            },
            "allocation": self._calculate_allocation(holdings),
            "performance": await self._calculate_performance(db, portfolio_id=portfolio_id),
            "risk_metrics": self._calculate_risk_metrics(holdings),
            "top_performers": self._get_top_performers(holdings),
            "bottom_performers": self._get_bottom_performers(holdings),
            "dividend_income": self._calculate_dividend_income(holdings),
        }

    def _calculate_allocation(self, holdings: list[PortfolioHolding]) -> dict[str, Any]:
        total_value = sum((holding.current_value or 0.0) for holding in holdings)
        if total_value <= 0:
            return {"by_asset": {}, "by_sector": {}, "concentration": {"herfindahl_index": 0.0, "top_5_concentration": 0.0, "diversification_score": 0.0}}

        by_asset: dict[str, dict[str, float]] = {}
        sector_map = MarketIntelligenceService.SECTOR_MAP
        by_sector: dict[str, float] = {}
        for holding in holdings:
            current_value = holding.current_value or 0.0
            percent = (current_value / total_value) * 100
            by_asset[holding.symbol] = {
                "value": round(current_value, 2),
                "percent": round(percent, 2),
                "quantity": round(holding.quantity, 4),
            }
            sector = sector_map.get(holding.symbol, holding.asset_type or "Other")
            by_sector[sector] = by_sector.get(sector, 0.0) + percent

        return {
            "by_asset": by_asset,
            "by_sector": {key: round(value, 2) for key, value in sorted(by_sector.items(), key=lambda item: item[1], reverse=True)},
            "concentration": self._calculate_concentration(by_asset),
        }

    async def _calculate_performance(self, db: AsyncSession, *, portfolio_id: int) -> dict[str, Any]:
        result = await db.execute(
            select(PortfolioPerformance)
            .where(PortfolioPerformance.portfolio_id == portfolio_id)
            .order_by(PortfolioPerformance.snapshot_date.asc())
            .limit(365)
        )
        snapshots = list(result.scalars().all())
        if len(snapshots) < 2:
            return {}

        values = [snapshot.total_value for snapshot in snapshots if snapshot.total_value is not None]
        returns = self._pct_changes(values)
        if not returns:
            return {}

        return {
            "daily_avg_return": round(mean(returns) * 100, 2),
            "daily_volatility": round((pstdev(returns) if len(returns) > 1 else 0.0) * 100, 2),
            "sharpe_ratio": round((mean(returns) / pstdev(returns) * sqrt(252)) if len(returns) > 1 and pstdev(returns) > 0 else 0.0, 2),
            "max_drawdown": round(self._calculate_max_drawdown(values), 2),
            "win_rate": round((sum(1 for item in returns if item > 0) / len(returns)) * 100, 2),
            "1_day_return": round(returns[-1] * 100, 2),
            "7_day_return": round(self._window_return(values, 7) * 100, 2),
            "30_day_return": round(self._window_return(values, 30) * 100, 2),
            "90_day_return": round(self._window_return(values, 90) * 100, 2),
        }

    def _calculate_risk_metrics(self, holdings: list[PortfolioHolding]) -> dict[str, Any]:
        weighted_returns: list[float] = []
        total_value = sum((holding.current_value or 0.0) for holding in holdings)
        if total_value <= 0:
            return {}

        for holding in holdings:
            current_value = holding.current_value or 0.0
            gain_percent = holding.unrealized_gain_loss_percent or 0.0
            weight = current_value / total_value if total_value else 0.0
            weighted_returns.append(gain_percent * weight)

        if not weighted_returns:
            return {}
        volatility = pstdev(weighted_returns) if len(weighted_returns) > 1 else 0.0
        ordered = sorted(weighted_returns)
        var_index = max(0, int(round((len(ordered) - 1) * 0.05)))
        value_at_risk = ordered[var_index]
        expected_return = sum(weighted_returns)
        return {
            "portfolio_volatility": round(volatility, 2),
            "value_at_risk_95": round(value_at_risk, 2),
            "expected_return": round(expected_return, 2),
            "risk_grade": self._get_risk_grade(volatility),
        }

    def _get_top_performers(self, holdings: list[PortfolioHolding], count: int = 5) -> list[dict[str, Any]]:
        sorted_holdings = sorted(holdings, key=lambda item: item.unrealized_gain_loss_percent or 0.0, reverse=True)
        return [
            {
                "symbol": holding.symbol,
                "return_percent": round(holding.unrealized_gain_loss_percent or 0.0, 2),
                "return_amount": round(holding.unrealized_gain_loss or 0.0, 2),
                "current_value": round(holding.current_value or 0.0, 2),
            }
            for holding in sorted_holdings[:count]
        ]

    def _get_bottom_performers(self, holdings: list[PortfolioHolding], count: int = 5) -> list[dict[str, Any]]:
        sorted_holdings = sorted(holdings, key=lambda item: item.unrealized_gain_loss_percent or 0.0)
        return [
            {
                "symbol": holding.symbol,
                "return_percent": round(holding.unrealized_gain_loss_percent or 0.0, 2),
                "return_amount": round(holding.unrealized_gain_loss or 0.0, 2),
                "current_value": round(holding.current_value or 0.0, 2),
            }
            for holding in sorted_holdings[:count]
        ]

    def _calculate_dividend_income(self, holdings: list[PortfolioHolding]) -> dict[str, Any]:
        total_dividends = sum(holding.total_dividends or 0.0 for holding in holdings)
        total_value = sum(holding.current_value or 0.0 for holding in holdings)
        dividend_yield = ((total_dividends / total_value) * 100) if total_value else 0.0
        return {
            "total_dividends": round(total_dividends, 2),
            "dividend_yield": round(dividend_yield, 2),
            "annualized_income": round(total_dividends * 4, 2),
        }

    def _calculate_max_drawdown(self, values: list[float]) -> float:
        if not values:
            return 0.0
        peak = values[0]
        max_drawdown = 0.0
        for value in values:
            peak = max(peak, value)
            if peak:
                max_drawdown = min(max_drawdown, (value - peak) / peak)
        return max_drawdown * 100

    def _calculate_concentration(self, allocation: dict[str, dict[str, float]]) -> dict[str, float]:
        if not allocation:
            return {"herfindahl_index": 0.0, "top_5_concentration": 0.0, "diversification_score": 0.0}
        percentages = [item["percent"] / 100 for item in allocation.values()]
        herfindahl = sum(value**2 for value in percentages)
        top_5 = sum(sorted(percentages, reverse=True)[:5]) * 100
        return {
            "herfindahl_index": round(herfindahl, 4),
            "top_5_concentration": round(top_5, 2),
            "diversification_score": round((1 - herfindahl) * 100, 2),
        }

    def _get_risk_grade(self, volatility: float) -> str:
        if volatility < 10:
            return "Low Risk"
        if volatility < 20:
            return "Medium Risk"
        if volatility < 30:
            return "High Risk"
        return "Very High Risk"

    async def _get_current_prices(self, db: AsyncSession, symbols: list[str]) -> dict[str, float]:
        prices: dict[str, float] = {}
        for symbol in symbols:
            normalized_symbol = normalize_symbol(symbol)
            result = await db.execute(
                select(MarketData).where(MarketData.symbol == normalized_symbol).order_by(MarketData.data_timestamp.desc()).limit(1)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                prices[normalized_symbol] = float(row.price)
        return prices

    async def _create_performance_snapshot(
        self,
        db: AsyncSession,
        *,
        portfolio: Portfolio,
        previous_total: float,
    ) -> None:
        today = datetime.now(timezone.utc).date()
        result = await db.execute(
            select(PortfolioPerformance).where(
                PortfolioPerformance.portfolio_id == portfolio.id,
                func.date(PortfolioPerformance.snapshot_date) == today,
            )
        )
        existing = result.scalar_one_or_none()

        holdings_result = await db.execute(
            select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio.id)
        )
        holdings = list(holdings_result.scalars().all())
        allocation = self._calculate_allocation(holdings)
        daily_change = portfolio.total_value_aed - previous_total if previous_total else 0.0
        daily_change_percent = ((daily_change / previous_total) * 100) if previous_total else 0.0

        if existing:
            existing.total_value = portfolio.total_value_aed
            existing.total_cost = portfolio.total_cost_aed
            existing.total_return = portfolio.total_return_aed
            existing.total_return_percent = portfolio.total_return_percent
            existing.daily_change = daily_change
            existing.daily_change_percent = daily_change_percent
            existing.holdings_snapshot = {holding.symbol: holding.current_value or 0.0 for holding in holdings}
            existing.sector_allocation = allocation["by_sector"]
            existing.asset_allocation = allocation["by_asset"]
        else:
            snapshot = PortfolioPerformance(
                portfolio_id=portfolio.id,
                snapshot_date=datetime.now(timezone.utc),
                total_value=portfolio.total_value_aed,
                total_cost=portfolio.total_cost_aed,
                total_return=portfolio.total_return_aed,
                total_return_percent=portfolio.total_return_percent,
                daily_change=daily_change,
                daily_change_percent=daily_change_percent,
                holdings_snapshot={holding.symbol: holding.current_value or 0.0 for holding in holdings},
                sector_allocation=allocation["by_sector"],
                asset_allocation=allocation["by_asset"],
            )
            db.add(snapshot)
        await db.commit()

    def _pct_changes(self, values: list[float]) -> list[float]:
        changes: list[float] = []
        for index in range(1, len(values)):
            previous = values[index - 1]
            current = values[index]
            if previous:
                changes.append((current - previous) / previous)
        return changes

    def _window_return(self, values: list[float], periods: int) -> float:
        if len(values) <= periods or values[-periods - 1] == 0:
            return 0.0
        baseline = values[-periods - 1]
        return (values[-1] - baseline) / baseline


portfolio_service = PortfolioService()
