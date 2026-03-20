from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from math import sqrt
from statistics import mean, pstdev
from typing import Any, Iterable

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_data import EconomicIndicator, MarketData
from app.models.news import NewsArticle


@dataclass(slots=True)
class MarketPoint:
    symbol: str
    name: str
    sector: str
    region: str
    exchange: str | None
    asset_class: str | None
    recorded_on: date
    close: float
    high: float
    low: float
    volume: int
    change_percent: float


class MarketIntelligenceService:
    """Generate additive intelligence views from stored market, macro, and news history."""

    SECTOR_MAP: dict[str, str] = {
        "EMAAR.DU": "Real Estate",
        "DAMAC.DU": "Real Estate",
        "DEYAAR.DU": "Real Estate",
        "UPP.DU": "Real Estate",
        "AMLAK.DU": "Real Estate Finance",
        "ALDAR.AD": "Real Estate",
        "ESHRAQ.AD": "Real Estate",
        "RAKPROP.AD": "Real Estate",
        "DIC.DU": "Diversified",
        "DFM.DU": "Capital Markets",
        "ADCB.AD": "Banking",
        "FAB.AD": "Banking",
        "ADNOC.AD": "Energy",
        "SPG": "Global Real Estate",
        "O": "Global Real Estate",
        "PLD": "Global Real Estate",
        "AMT": "Global Real Estate",
        "CCI": "Global Real Estate",
        "LEN": "Developers",
        "DHI": "Developers",
        "NVR": "Developers",
        "GC=F": "Commodities",
        "SI=F": "Commodities",
        "CL=F": "Commodities",
        "BZ=F": "Commodities",
    }

    async def generate_market_overview(self, db: AsyncSession, region: str = "UAE") -> dict[str, Any]:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=90)

        market_points = await self._fetch_market_points(db, start_date, end_date, region)
        sentiment_points = await self._fetch_news_sentiment(db, start_date, end_date, region)
        economic_indicators = await self._fetch_economic_data(db, region)

        symbol_series = self._build_symbol_series(market_points)
        composite = self._build_composite_series(symbol_series)

        market_health = self._calculate_market_health(composite, sentiment_points)
        momentum = self._calculate_momentum(composite)
        sector_performance = self._analyze_sector_performance(symbol_series)
        volatility = self._calculate_volatility_metrics(composite)
        correlation = self._build_correlation_matrix(symbol_series)
        key_drivers = self._identify_key_drivers(composite, sentiment_points, economic_indicators)
        risks = self._assess_risk_factors(symbol_series, composite, sentiment_points)
        opportunities = self._identify_opportunities(symbol_series, sentiment_points)
        benchmarks = self._build_benchmark_snapshots(market_points)
        executive_summary = self._build_executive_summary(
            market_health=market_health,
            sector_performance=sector_performance,
            risk_factors=risks,
            opportunities=opportunities,
            key_drivers=key_drivers,
        )

        return {
            "market_health_score": market_health,
            "momentum_indicators": momentum,
            "sector_performance": sector_performance,
            "volatility_analysis": volatility,
            "correlation_matrix": correlation,
            "key_drivers": key_drivers,
            "risk_factors": risks,
            "opportunities": opportunities,
            "benchmark_snapshots": benchmarks,
            "executive_summary": executive_summary,
            "timestamp": datetime.now(timezone.utc),
        }

    async def _fetch_market_points(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        region: str,
    ) -> list[MarketPoint]:
        result = await db.execute(
            select(MarketData)
            .where(
                and_(
                    MarketData.data_timestamp >= start_date,
                    MarketData.data_timestamp <= end_date,
                )
            )
            .order_by(MarketData.data_timestamp.asc())
        )
        rows = result.scalars().all()

        normalized_region = region.upper()
        points: list[MarketPoint] = []
        for row in rows:
            row_region = (row.region or "").upper()
            if normalized_region == "UAE" and row_region and row_region not in {"UAE", "GCC"}:
                continue

            points.append(
                MarketPoint(
                    symbol=row.symbol,
                    name=row.name,
                    sector=self.SECTOR_MAP.get(row.symbol, row.asset_class or row.market_type.value.title()),
                    region=row.region or "Unknown",
                    exchange=row.exchange.value.upper() if row.exchange is not None else None,
                    asset_class=row.asset_class,
                    recorded_on=row.data_timestamp.date(),
                    close=float(row.close_price or row.price or 0.0),
                    high=float(row.high_price or row.price or 0.0),
                    low=float(row.low_price or row.price or 0.0),
                    volume=int(row.volume or 0),
                    change_percent=float(row.change_percent or 0.0),
                )
            )

        if points:
            return points

        fallback_result = await db.execute(
            select(MarketData).order_by(MarketData.data_timestamp.desc()).limit(500)
        )
        fallback_rows = fallback_result.scalars().all()
        return [
            MarketPoint(
                symbol=row.symbol,
                name=row.name,
                sector=self.SECTOR_MAP.get(row.symbol, row.asset_class or row.market_type.value.title()),
                region=row.region or "Unknown",
                exchange=row.exchange.value.upper() if row.exchange is not None else None,
                asset_class=row.asset_class,
                recorded_on=row.data_timestamp.date(),
                close=float(row.close_price or row.price or 0.0),
                high=float(row.high_price or row.price or 0.0),
                low=float(row.low_price or row.price or 0.0),
                volume=int(row.volume or 0),
                change_percent=float(row.change_percent or 0.0),
            )
            for row in fallback_rows
        ]

    async def _fetch_news_sentiment(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        region: str,
    ) -> list[dict[str, Any]]:
        result = await db.execute(
            select(NewsArticle)
            .where(
                and_(
                    NewsArticle.published_at >= start_date,
                    NewsArticle.published_at <= end_date,
                    NewsArticle.is_published.is_(True),
                )
            )
            .order_by(NewsArticle.published_at.asc())
        )
        articles = result.scalars().all()
        target_region = region.lower()
        points: list[dict[str, Any]] = []
        for article in articles:
            text = " ".join(
                part for part in [article.title, article.description or "", article.content or ""] if part
            ).lower()
            if target_region == "uae" and not any(token in text for token in {"dubai", "uae", "abu dhabi", "dfm", "adx"}):
                continue

            raw_score = float(article.sentiment_score or 0)
            normalized_score = raw_score / 100 if abs(raw_score) > 1 else raw_score
            points.append(
                {
                    "date": article.published_at.date(),
                    "sentiment_score": max(-1.0, min(1.0, normalized_score)),
                    "symbol": self._extract_symbol_from_text(text),
                    "category": article.category.value,
                }
            )
        return points

    async def _fetch_economic_data(self, db: AsyncSession, region: str) -> dict[str, dict[str, Any]]:
        country = "UAE" if region.upper() == "UAE" else None
        result = await db.execute(
            select(EconomicIndicator).order_by(EconomicIndicator.timestamp.desc()).limit(100)
        )
        rows = result.scalars().all()
        indicators: dict[str, dict[str, Any]] = {}
        seen_codes: set[str] = set()
        for row in rows:
            if country and row.country not in {country, "ARE"}:
                continue
            if row.indicator_code in seen_codes:
                continue
            seen_codes.add(row.indicator_code)
            indicators[row.indicator_name] = {
                "value": float(row.value),
                "trend": self._infer_indicator_trend(float(row.value), row.indicator_name),
                "source": row.source or "unknown",
                "period": row.period,
            }
        return indicators

    def _build_symbol_series(self, points: list[MarketPoint]) -> dict[str, dict[str, Any]]:
        grouped: dict[str, list[MarketPoint]] = defaultdict(list)
        for point in points:
            grouped[point.symbol].append(point)

        series: dict[str, dict[str, Any]] = {}
        for symbol, items in grouped.items():
            daily: dict[date, MarketPoint] = {}
            for item in items:
                existing = daily.get(item.recorded_on)
                if existing is None or item.close:
                    daily[item.recorded_on] = item

            ordered = [daily[key] for key in sorted(daily)]
            if not ordered:
                continue
            latest = ordered[-1]
            series[symbol] = {
                "symbol": symbol,
                "name": latest.name,
                "sector": latest.sector,
                "region": latest.region,
                "exchange": latest.exchange,
                "asset_class": latest.asset_class,
                "points": ordered,
            }
        return series

    def _build_composite_series(self, symbol_series: dict[str, dict[str, Any]]) -> list[dict[str, float | date]]:
        by_date: dict[date, dict[str, list[float]]] = defaultdict(lambda: {"close": [], "volume": [], "high": [], "low": []})
        for payload in symbol_series.values():
            for point in payload["points"]:
                by_date[point.recorded_on]["close"].append(point.close)
                by_date[point.recorded_on]["volume"].append(float(point.volume))
                by_date[point.recorded_on]["high"].append(point.high)
                by_date[point.recorded_on]["low"].append(point.low)

        composite: list[dict[str, float | date]] = []
        for bucket in sorted(by_date):
            values = by_date[bucket]
            composite.append(
                {
                    "date": bucket,
                    "close": mean(values["close"]) if values["close"] else 0.0,
                    "volume": sum(values["volume"]),
                    "high": max(values["high"]) if values["high"] else 0.0,
                    "low": min(values["low"]) if values["low"] else 0.0,
                }
            )
        return composite

    def _calculate_market_health(
        self,
        market_data: list[dict[str, float | date]],
        sentiment_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        closes = [float(item["close"]) for item in market_data]
        volumes = [float(item["volume"]) for item in market_data]
        returns = self._returns(closes)

        momentum_raw = self._safe_return(closes, 30)
        momentum_score = max(0.0, min(100.0, 50 + momentum_raw * 500))

        recent_volume = mean(volumes[-30:]) if volumes else 0.0
        baseline_volume = mean(volumes[-90:]) if volumes else 0.0
        volume_ratio = recent_volume / baseline_volume if baseline_volume else 1.0
        volume_score = max(0.0, min(100.0, volume_ratio * 60))

        avg_sentiment = mean([float(item["sentiment_score"]) for item in sentiment_data]) if sentiment_data else 0.0
        sentiment_score = (avg_sentiment + 1.0) * 50

        annualized_vol = (pstdev(returns) * sqrt(252) * 100) if len(returns) > 1 else 0.0
        volatility_score = max(0.0, min(100.0, 100 - annualized_vol * 1.8))

        breadth_score = 50.0
        if returns:
            breadth_score = (sum(1 for item in returns if item > 0) / len(returns)) * 100

        weighted_components = {
            "momentum": round(momentum_score * 0.30, 2),
            "volume": round(volume_score * 0.20, 2),
            "sentiment": round(sentiment_score * 0.25, 2),
            "volatility": round(volatility_score * 0.15, 2),
            "breadth": round(breadth_score * 0.10, 2),
        }
        total_score = round(sum(weighted_components.values()), 2)
        return {
            "overall_score": total_score,
            "components": weighted_components,
            "grade": self._get_health_grade(total_score),
            "trend": self._get_trend_direction(closes),
        }

    def _calculate_momentum(self, market_data: list[dict[str, float | date]]) -> dict[str, Any]:
        closes = [float(item["close"]) for item in market_data]
        rsi_values = self._compute_rsi(closes, 14)
        rsi_current = rsi_values[-1] if rsi_values else 50.0

        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)
        macd_series = [a - b for a, b in zip(ema_12, ema_26)] if ema_12 and ema_26 else [0.0]
        signal_series = self._ema(macd_series, 9)
        histogram = (macd_series[-1] - signal_series[-1]) if macd_series and signal_series else 0.0

        roc_10 = self._safe_return(closes, 10) * 100
        roc_30 = self._safe_return(closes, 30) * 100

        return {
            "rsi": {
                "current": round(rsi_current, 2),
                "signal": "overbought" if rsi_current > 70 else "oversold" if rsi_current < 30 else "neutral",
                "trend": "bullish" if len(rsi_values) >= 5 and rsi_values[-1] >= rsi_values[-5] else "bearish",
            },
            "macd": {
                "value": round(macd_series[-1] if macd_series else 0.0, 4),
                "signal_line": round(signal_series[-1] if signal_series else 0.0, 4),
                "histogram": round(histogram, 4),
                "signal": "buy" if histogram >= 0 else "sell",
                "strength": round(abs(histogram), 4),
            },
            "rate_of_change": {
                "ten_day": round(roc_10, 2),
                "thirty_day": round(roc_30, 2),
                "acceleration": "positive" if roc_10 >= roc_30 else "negative",
            },
        }

    def _analyze_sector_performance(self, symbol_series: dict[str, dict[str, Any]]) -> dict[str, Any]:
        sector_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for payload in symbol_series.values():
            points: list[MarketPoint] = payload["points"]
            closes = [point.close for point in points]
            returns = self._returns(closes)
            sector_buckets[payload["sector"]].append(
                {
                    "symbol": payload["symbol"],
                    "name": payload["name"],
                    "return_30d": self._safe_return(closes, 30) * 100,
                    "volatility": (pstdev(returns) * sqrt(252) * 100) if len(returns) > 1 else 0.0,
                    "avg_volume": int(mean([point.volume for point in points])) if points else 0,
                }
            )

        sectors: list[dict[str, Any]] = []
        for sector, items in sector_buckets.items():
            volatilities = [float(item["volatility"]) for item in items]
            returns = [float(item["return_30d"]) for item in items]
            sharpe = (mean(returns) / mean(volatilities)) if mean(volatilities) > 0 else 0.0
            top = sorted(items, key=lambda entry: float(entry["return_30d"]), reverse=True)[:3]
            sectors.append(
                {
                    "sector": sector,
                    "return_30d": round(mean(returns), 2),
                    "volatility": round(mean(volatilities), 2),
                    "sharpe_ratio": round(sharpe, 2),
                    "avg_volume": int(mean([int(item["avg_volume"]) for item in items])) if items else 0,
                    "stock_count": len(items),
                    "top_performers": [
                        {
                            "symbol": item["symbol"],
                            "name": item["name"],
                            "return_30d": round(float(item["return_30d"]), 2),
                        }
                        for item in top
                    ],
                }
            )

        ranked = sorted(sectors, key=lambda item: item["return_30d"], reverse=True)
        rankings = {
            "best_performing": ranked[0]["sector"] if ranked else None,
            "worst_performing": ranked[-1]["sector"] if ranked else None,
            "most_volatile": max(sectors, key=lambda item: item["volatility"])["sector"] if sectors else None,
            "least_volatile": min(sectors, key=lambda item: item["volatility"])["sector"] if sectors else None,
        }
        return {"sectors": ranked, "rankings": rankings}

    def _calculate_volatility_metrics(self, market_data: list[dict[str, float | date]]) -> dict[str, float | str]:
        closes = [float(item["close"]) for item in market_data]
        returns = self._returns(closes)
        hist_vol = (pstdev(returns) * sqrt(252) * 100) if len(returns) > 1 else 0.0
        vol_30 = (pstdev(returns[-30:]) * sqrt(252) * 100) if len(returns[-30:]) > 1 else hist_vol
        vol_90 = (pstdev(returns[-90:]) * sqrt(252) * 100) if len(returns[-90:]) > 1 else hist_vol
        regime = "normal"
        if vol_30 > vol_90 * 1.2:
            regime = "high"
        elif vol_30 < vol_90 * 0.8:
            regime = "low"

        negative_returns = [value for value in returns if value < 0]
        downside_dev = (pstdev(negative_returns) * sqrt(252) * 100) if len(negative_returns) > 1 else 0.0
        drawdowns = self._drawdowns(returns)
        max_drawdown = min(drawdowns) * 100 if drawdowns else 0.0
        var_95 = self._quantile(returns, 0.05) * 100 if returns else 0.0
        tail_losses = [value for value in returns if value <= self._quantile(returns, 0.05)] if returns else []
        cvar_95 = (mean(tail_losses) * 100) if tail_losses else 0.0

        return {
            "historical_volatility": round(hist_vol, 2),
            "volatility_30d": round(vol_30, 2),
            "volatility_90d": round(vol_90, 2),
            "regime": regime,
            "downside_deviation": round(downside_dev, 2),
            "max_drawdown": round(max_drawdown, 2),
            "var_95": round(var_95, 2),
            "cvar_95": round(cvar_95, 2),
        }

    def _build_correlation_matrix(self, symbol_series: dict[str, dict[str, Any]]) -> dict[str, Any]:
        eligible = []
        for payload in symbol_series.values():
            closes = [point.close for point in payload["points"]]
            if len(closes) >= 8:
                eligible.append((payload["symbol"], self._returns(closes)))

        eligible = sorted(eligible, key=lambda item: len(item[1]), reverse=True)[:8]
        matrix: dict[str, dict[str, float]] = {}
        correlations: list[dict[str, Any]] = []
        corr_values: list[float] = []
        for symbol_a, returns_a in eligible:
            matrix[symbol_a] = {}
            for symbol_b, returns_b in eligible:
                common_len = min(len(returns_a), len(returns_b))
                if common_len < 3:
                    corr = 0.0
                else:
                    corr = self._pearson(returns_a[-common_len:], returns_b[-common_len:])
                matrix[symbol_a][symbol_b] = round(corr, 4)
                if symbol_a < symbol_b:
                    corr_values.append(corr)
                    if abs(corr) >= 0.7:
                        correlations.append(
                            {
                                "asset_1": symbol_a,
                                "asset_2": symbol_b,
                                "correlation": round(corr, 4),
                            }
                        )
        return {
            "matrix": matrix,
            "high_correlations": sorted(correlations, key=lambda item: abs(item["correlation"]), reverse=True)[:10],
            "average_correlation": round(mean(corr_values), 4) if corr_values else 0.0,
        }

    def _identify_key_drivers(
        self,
        market_data: list[dict[str, float | date]],
        sentiment_data: list[dict[str, Any]],
        economic_data: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        drivers: list[dict[str, Any]] = []
        closes = [float(item["close"]) for item in market_data]
        volumes = [float(item["volume"]) for item in market_data]
        returns = self._returns(closes)

        sentiment_by_date: dict[date, list[float]] = defaultdict(list)
        for point in sentiment_data:
            sentiment_by_date[point["date"]].append(float(point["sentiment_score"]))
        aligned_sentiment = [
            mean(sentiment_by_date[item["date"]]) for item in market_data if item["date"] in sentiment_by_date
        ]
        aligned_returns = [
            returns[index - 1]
            for index, item in enumerate(market_data)
            if index > 0 and item["date"] in sentiment_by_date
        ]
        if aligned_sentiment and aligned_returns and len(aligned_sentiment) == len(aligned_returns):
            corr = self._pearson(aligned_sentiment, aligned_returns)
            drivers.append(
                {
                    "factor": "News Sentiment",
                    "impact": "positive" if corr >= 0 else "negative",
                    "strength": round(abs(corr), 2),
                    "description": f"Editorial tone is showing {abs(corr):.0%} correlation with composite price moves.",
                    "current_value": round(mean(aligned_sentiment), 2),
                    "trend": "improving" if mean(aligned_sentiment[-5:]) >= mean(aligned_sentiment[:5]) else "softening",
                }
            )

        if len(volumes) >= 10:
            recent_volume = mean(volumes[-10:])
            base_volume = mean(volumes[-45:]) if len(volumes) >= 45 else mean(volumes)
            ratio = recent_volume / base_volume if base_volume else 1.0
            drivers.append(
                {
                    "factor": "Trading Volume",
                    "impact": "positive" if ratio >= 1 else "negative",
                    "strength": round(abs(ratio - 1), 2),
                    "description": f"Recent trading volume is {ratio:.2f}x the broader baseline.",
                    "current_value": round(ratio, 2),
                    "trend": "expanding" if ratio >= 1 else "cooling",
                }
            )

        for name, payload in list(economic_data.items())[:3]:
            drivers.append(
                {
                    "factor": name,
                    "impact": payload.get("trend", "stable"),
                    "strength": None,
                    "description": f"{name} is reading {payload['value']} ({payload.get('period') or 'latest'}).",
                    "current_value": payload["value"],
                    "trend": payload.get("trend", "stable"),
                }
            )

        return drivers[:5]

    def _assess_risk_factors(
        self,
        symbol_series: dict[str, dict[str, Any]],
        market_data: list[dict[str, float | date]],
        sentiment_data: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        risks: list[dict[str, str]] = []
        closes = [float(item["close"]) for item in market_data]
        returns = self._returns(closes)
        volatility = (pstdev(returns) * sqrt(252) * 100) if len(returns) > 1 else 0.0
        if volatility > 18:
            risks.append(
                {
                    "category": "Market Volatility",
                    "severity": "high" if volatility > 28 else "medium",
                    "description": f"Annualized volatility is {volatility:.1f}%, which is elevated for the current board mix.",
                    "mitigation": "Favor staggered entries and monitor liquidity concentration before sizing up exposure.",
                }
            )

        recent_sentiment = mean([float(item["sentiment_score"]) for item in sentiment_data[-30:]]) if sentiment_data else 0.0
        if recent_sentiment < -0.15:
            risks.append(
                {
                    "category": "Negative Narrative Drift",
                    "severity": "high" if recent_sentiment < -0.35 else "medium",
                    "description": f"Recent sentiment is running at {recent_sentiment:.2f}, indicating a softer editorial backdrop.",
                    "mitigation": "Watch for follow-through in macro and policy stories before assuming mean reversion.",
                }
            )

        latest_volumes = []
        for payload in symbol_series.values():
            points: list[MarketPoint] = payload["points"]
            latest_volumes.append(points[-1].volume if points else 0)
        total_volume = sum(latest_volumes)
        top_share = sum(sorted(latest_volumes, reverse=True)[:5]) / total_volume if total_volume else 0.0
        if top_share > 0.65:
            risks.append(
                {
                    "category": "Concentration Risk",
                    "severity": "medium",
                    "description": f"The top five names represent {top_share:.0%} of observable turnover in the sampled history.",
                    "mitigation": "Avoid reading the whole board through a handful of high-volume symbols.",
                }
            )

        drawdowns = self._drawdowns(returns)
        if drawdowns and min(drawdowns) < -0.12:
            risks.append(
                {
                    "category": "Drawdown Pressure",
                    "severity": "high" if min(drawdowns) < -0.20 else "medium",
                    "description": f"The composite series has seen a {abs(min(drawdowns)):.1%} peak-to-trough drawdown in the sampled window.",
                    "mitigation": "Keep risk budgets explicit and use catalyst-aware stop levels rather than static optimism.",
                }
            )
        return risks

    def _identify_opportunities(
        self,
        symbol_series: dict[str, dict[str, Any]],
        sentiment_data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        opportunities: list[dict[str, Any]] = []
        sentiment_by_symbol: dict[str, list[float]] = defaultdict(list)
        for point in sentiment_data:
            if point["symbol"]:
                sentiment_by_symbol[point["symbol"]].append(float(point["sentiment_score"]))

        for payload in symbol_series.values():
            symbol = payload["symbol"]
            points: list[MarketPoint] = payload["points"]
            closes = [point.close for point in points]
            if len(closes) < 15:
                continue

            rsi_values = self._compute_rsi(closes, 14)
            current_rsi = rsi_values[-1] if rsi_values else 50.0
            return_10d = self._safe_return(closes, 10)

            if current_rsi < 32:
                opportunities.append(
                    {
                        "type": "Oversold Reversal",
                        "symbol": symbol,
                        "indicator": "RSI",
                        "value": round(current_rsi, 2),
                        "rationale": f"{symbol} is screening as oversold on a 14-period RSI basis.",
                        "confidence": "medium",
                    }
                )

            recent_sentiment = mean(sentiment_by_symbol[symbol][-10:]) if sentiment_by_symbol[symbol] else 0.0
            if recent_sentiment > 0.2 and return_10d < -0.03:
                opportunities.append(
                    {
                        "type": "Sentiment-Price Divergence",
                        "symbol": symbol,
                        "indicator": "News Sentiment",
                        "value": round(recent_sentiment, 2),
                        "rationale": f"{symbol} has constructive coverage despite a negative 10-day price move.",
                        "confidence": "medium",
                    }
                )

            trailing_high = max(closes[-90:]) if len(closes) >= 90 else max(closes)
            recent_volume = mean([point.volume for point in points[-10:]])
            baseline_volume = mean([point.volume for point in points[-45:]]) if len(points) >= 45 else recent_volume
            if trailing_high and closes[-1] >= trailing_high * 0.98 and recent_volume > baseline_volume * 1.15:
                opportunities.append(
                    {
                        "type": "Breakout Candidate",
                        "symbol": symbol,
                        "indicator": "Price + Volume",
                        "value": round((closes[-1] / trailing_high - 1) * 100, 2),
                        "rationale": f"{symbol} is pressing the upper range with improving turnover.",
                        "confidence": "high",
                    }
                )

        ranked = sorted(
            opportunities,
            key=lambda item: {"high": 2, "medium": 1, "low": 0}.get(item["confidence"], 0),
            reverse=True,
        )
        return ranked[:10]

    def _build_benchmark_snapshots(self, points: list[MarketPoint]) -> list[dict[str, Any]]:
        latest_by_symbol: dict[str, MarketPoint] = {}
        for point in points:
            existing = latest_by_symbol.get(point.symbol)
            if existing is None or point.recorded_on >= existing.recorded_on:
                latest_by_symbol[point.symbol] = point

        ranked = sorted(latest_by_symbol.values(), key=lambda item: item.change_percent, reverse=True)
        selections = ranked[:4] + ranked[-4:]
        seen: set[str] = set()
        payload: list[dict[str, Any]] = []
        for item in selections:
            if item.symbol in seen:
                continue
            seen.add(item.symbol)
            payload.append(
                {
                    "symbol": item.symbol,
                    "name": item.name,
                    "price": round(item.close, 2),
                    "change_percent": round(item.change_percent, 2),
                    "region": item.region,
                    "asset_class": item.asset_class,
                    "exchange": item.exchange,
                }
            )
        return payload

    def _build_executive_summary(
        self,
        *,
        market_health: dict[str, Any],
        sector_performance: dict[str, Any],
        risk_factors: list[dict[str, str]],
        opportunities: list[dict[str, Any]],
        key_drivers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        headline = (
            f"{market_health['grade']} market posture with a {market_health['trend']} bias"
            if market_health["overall_score"] >= 60
            else f"{market_health['grade']} market posture with selective caution"
        )
        best_sector = sector_performance["rankings"].get("best_performing") or "mixed leadership"
        lead_driver = key_drivers[0]["factor"] if key_drivers else "provider flow"
        narrative = (
            f"The current board is reading {market_health['trend']} with {best_sector} leading the performance stack. "
            f"The main near-term driver is {lead_driver}, while the risk canvas is defined by "
            f"{risk_factors[0]['category'] if risk_factors else 'normal market noise'}."
        )
        focus_areas = [
            f"Track {best_sector} for continued leadership confirmation.",
            f"Watch {lead_driver} for the next directional signal.",
            (
                f"Review {opportunities[0]['symbol']} as the highest-ranked setup."
                if opportunities and opportunities[0].get("symbol")
                else "Maintain selective scanning for clean setups."
            ),
        ]
        return {"headline": headline, "narrative": narrative, "focus_areas": focus_areas}

    def _extract_symbol_from_text(self, text: str) -> str | None:
        for symbol in self.SECTOR_MAP:
            readable = symbol.lower().replace(".du", "").replace(".ad", "")
            if readable in text or symbol.lower() in text:
                return symbol
        return None

    def _infer_indicator_trend(self, value: float, name: str) -> str:
        upper = name.upper()
        if "GDP" in upper or "PMI" in upper:
            return "positive" if value >= 0 else "negative"
        if "INFLATION" in upper:
            return "elevated" if value > 3 else "stable"
        if "UNEMPLOYMENT" in upper:
            return "negative" if value > 4 else "positive"
        return "stable"

    def _get_health_grade(self, score: float) -> str:
        if score >= 90:
            return "A+"
        if score >= 85:
            return "A"
        if score >= 80:
            return "A-"
        if score >= 75:
            return "B+"
        if score >= 70:
            return "B"
        if score >= 65:
            return "B-"
        if score >= 60:
            return "C+"
        if score >= 55:
            return "C"
        if score >= 50:
            return "C-"
        return "D"

    def _get_trend_direction(self, closes: list[float]) -> str:
        sma_20 = self._simple_average(closes[-20:])
        sma_50 = self._simple_average(closes[-50:])
        previous_sma_20 = self._simple_average(closes[-25:-5]) if len(closes) >= 25 else sma_20
        previous_sma_50 = self._simple_average(closes[-55:-5]) if len(closes) >= 55 else sma_50
        if sma_20 >= sma_50 and previous_sma_20 >= previous_sma_50:
            return "bullish"
        if sma_20 < sma_50 and previous_sma_20 < previous_sma_50:
            return "bearish"
        return "neutral"

    def _simple_average(self, values: Iterable[float]) -> float:
        items = [value for value in values if value is not None]
        return mean(items) if items else 0.0

    def _returns(self, closes: list[float]) -> list[float]:
        returns: list[float] = []
        for index in range(1, len(closes)):
            previous = closes[index - 1]
            current = closes[index]
            if previous:
                returns.append((current - previous) / previous)
        return returns

    def _safe_return(self, closes: list[float], periods: int) -> float:
        if len(closes) <= periods or closes[-periods - 1] == 0:
            return 0.0
        previous = closes[-periods - 1]
        return (closes[-1] - previous) / previous

    def _ema(self, values: list[float], span: int) -> list[float]:
        if not values:
            return []
        multiplier = 2 / (span + 1)
        results = [values[0]]
        for value in values[1:]:
            results.append((value - results[-1]) * multiplier + results[-1])
        return results

    def _compute_rsi(self, closes: list[float], period: int) -> list[float]:
        if len(closes) < 2:
            return []
        deltas = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
        rsi: list[float] = []
        for index in range(period, len(deltas) + 1):
            window = deltas[index - period : index]
            gains = [delta for delta in window if delta > 0]
            losses = [-delta for delta in window if delta < 0]
            avg_gain = mean(gains) if gains else 0.0
            avg_loss = mean(losses) if losses else 0.0
            if avg_loss == 0:
                rsi.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))
        return rsi

    def _quantile(self, values: list[float], quantile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        position = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * quantile))))
        return ordered[position]

    def _drawdowns(self, returns: list[float]) -> list[float]:
        if not returns:
            return []
        value = 1.0
        peak = 1.0
        drawdowns: list[float] = []
        for current_return in returns:
            value *= 1 + current_return
            peak = max(peak, value)
            drawdowns.append((value - peak) / peak)
        return drawdowns

    def _pearson(self, left: list[float], right: list[float]) -> float:
        if len(left) != len(right) or len(left) < 2:
            return 0.0
        left_mean = mean(left)
        right_mean = mean(right)
        numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
        left_denominator = sqrt(sum((a - left_mean) ** 2 for a in left))
        right_denominator = sqrt(sum((b - right_mean) ** 2 for b in right))
        denominator = left_denominator * right_denominator
        return numerator / denominator if denominator else 0.0


market_intelligence = MarketIntelligenceService()
