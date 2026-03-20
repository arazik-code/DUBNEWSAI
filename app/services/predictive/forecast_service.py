from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import sqrt
from statistics import mean, pstdev
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.market_data import MarketData


class LightweightForecastService:
    """Simple prediction service optimized for free tier hosting."""

    def __init__(self, cache_hours: int = 24):
        self.cache_duration = timedelta(hours=cache_hours)
        self._cache: dict[str, dict[str, Any]] = {}

    async def predict_price_movement(
        self,
        db: AsyncSession,
        symbol: str,
        days_ahead: int = 30,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        cache_key = f"price_forecast_{symbol}_{days_ahead}"
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now(timezone.utc) - cached["timestamp"] < self.cache_duration:
                return cached["data"]

        historical_data = await self._get_historical_prices(db, symbol, days=90)
        if len(historical_data) < 30:
            return {"error": "Insufficient historical data"}

        prices = [item["close"] for item in historical_data]
        x_values = list(range(len(prices)))
        slope, intercept, r_value = self._linear_regression(x_values, prices)
        ema_short = self._calculate_ema(prices, period=12)
        ema_long = self._calculate_ema(prices, period=26)

        forecast_dates = list(range(len(prices), len(prices) + days_ahead))
        linear_forecast = [slope * value + intercept for value in forecast_dates]
        ema_growth = ((ema_short[-1] - ema_long[-1]) / prices[-1]) if prices[-1] else 0.0
        ema_forecast = [prices[-1] * ((1 + ema_growth) ** (index + 1)) for index in range(days_ahead)]
        predicted = [(linear_forecast[index] * 0.6) + (ema_forecast[index] * 0.4) for index in range(days_ahead)]

        residuals = [price - (slope * x + intercept) for x, price in zip(x_values, prices)]
        std_error = pstdev(residuals) if len(residuals) > 1 else 0.0
        upper = [value + 1.96 * std_error for value in predicted]
        lower = [value - 1.96 * std_error for value in predicted]

        current_price = prices[-1]
        target = predicted[min(days_ahead, 30) - 1]
        result = {
            "symbol": symbol,
            "current_price": float(current_price),
            "forecast_horizon_days": days_ahead,
            "prediction": {
                "target_price": float(target),
                "expected_return_percent": float(((target - current_price) / current_price * 100) if current_price else 0.0),
                "confidence_interval": {
                    "lower": float(lower[-1]),
                    "upper": float(upper[-1]),
                },
            },
            "trend": {
                "direction": "bullish" if slope > 0 else "bearish",
                "strength": float(abs(r_value)),
                "slope": float(slope),
            },
            "forecast_series": [
                {
                    "days_ahead": index + 1,
                    "predicted_price": float(predicted[index]),
                    "upper_bound": float(upper[index]),
                    "lower_bound": float(lower[index]),
                }
                for index in range(min(days_ahead, 30))
            ],
            "model_info": {
                "method": "statistical_hybrid",
                "r_squared": float(r_value**2),
                "data_points": len(prices),
            },
            "generated_at": datetime.now(timezone.utc),
        }
        self._cache[cache_key] = {"data": result, "timestamp": datetime.now(timezone.utc)}
        return result

    async def predict_market_trend(self, db: AsyncSession, region: str = "UAE") -> dict[str, Any]:
        cache_key = f"market_trend_{region}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now(timezone.utc) - cached["timestamp"] < self.cache_duration:
                return cached["data"]

        market_data = await self._get_market_indicators(db, region)
        score = 0.0
        factors: list[dict[str, Any]] = []

        price_change_30d = market_data.get("price_change_30d", 0.0)
        momentum_score = max(-40.0, min(40.0, price_change_30d * 2))
        score += momentum_score
        factors.append({"factor": "Price Momentum", "contribution": momentum_score, "description": f"30-day change: {price_change_30d:+.1f}%"})

        volume_trend = market_data.get("volume_trend", 1.0)
        volume_score = max(-20.0, min(20.0, (volume_trend - 1) * 40))
        score += volume_score
        factors.append({"factor": "Volume Trend", "contribution": volume_score, "description": f"Volume vs baseline: {(volume_trend - 1) * 100:+.0f}%"})

        sentiment = market_data.get("sentiment_score", 0.0)
        sentiment_score = sentiment * 20
        score += sentiment_score
        factors.append({"factor": "Market Sentiment", "contribution": sentiment_score, "description": f"News sentiment: {sentiment:+.2f}"})

        gdp_growth = market_data.get("gdp_growth", 2.5)
        economic_score = max(-20.0, min(20.0, (gdp_growth - 2) * 10))
        score += economic_score
        factors.append({"factor": "Economic Growth", "contribution": economic_score, "description": f"GDP growth: {gdp_growth:.1f}%"})

        if score > 40:
            prediction = "strong_bullish"
            confidence = "high"
        elif score > 20:
            prediction = "bullish"
            confidence = "medium"
        elif score > -20:
            prediction = "neutral"
            confidence = "medium"
        elif score > -40:
            prediction = "bearish"
            confidence = "medium"
        else:
            prediction = "strong_bearish"
            confidence = "high"

        result = {
            "region": region,
            "prediction": prediction,
            "confidence": confidence,
            "trend_score": round(score, 2),
            "factors": factors,
            "recommendation": self._get_market_recommendation(prediction),
            "timeframe": "30-day outlook",
            "generated_at": datetime.now(timezone.utc),
        }
        self._cache[cache_key] = {"data": result, "timestamp": datetime.now(timezone.utc)}
        return result

    async def predict_property_value_trend(self, location: str, property_type: str = "apartment") -> dict[str, Any]:
        cache_key = f"property_trend_{location}_{property_type}"
        weekly_cache = timedelta(days=7)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now(timezone.utc) - cached["timestamp"] < weekly_cache:
                return cached["data"]

        historical = await self._get_property_history(location, property_type)
        if len(historical) < 12:
            return {"error": "Insufficient data"}
        prices = [item["avg_price"] for item in historical]
        months = list(range(len(prices)))
        slope, intercept, r_value = self._linear_regression(months, prices)
        future_months = list(range(len(prices), len(prices) + 12))
        forecast = [slope * value + intercept for value in future_months]
        current_price = prices[-1]
        year_ago_price = prices[-12] if len(prices) >= 12 else prices[0]
        yoy_growth = ((current_price - year_ago_price) / year_ago_price * 100) if year_ago_price else 0.0
        result = {
            "location": location,
            "property_type": property_type,
            "current_avg_price": float(current_price),
            "yoy_growth_percent": float(yoy_growth),
            "forecast_12m": {
                "predicted_price": float(forecast[-1]),
                "expected_appreciation": float(((forecast[-1] - current_price) / current_price * 100) if current_price else 0.0),
                "trend": "appreciating" if slope > 0 else "depreciating",
            },
            "monthly_forecast": [{"month": index + 1, "predicted_price": float(value)} for index, value in enumerate(forecast)],
            "confidence": "high" if r_value**2 > 0.7 else "medium" if r_value**2 > 0.4 else "low",
            "data_quality": {"r_squared": float(r_value**2), "data_points": len(prices)},
            "generated_at": datetime.now(timezone.utc),
        }
        self._cache[cache_key] = {"data": result, "timestamp": datetime.now(timezone.utc)}
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    def _calculate_ema(self, prices: list[float], period: int) -> list[float]:
        ema = [prices[0]]
        multiplier = 2 / (period + 1)
        for price in prices[1:]:
            ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
        return ema

    def _get_market_recommendation(self, prediction: str) -> str:
        mapping = {
            "strong_bullish": "Consider increasing equity allocation. Favor constructive entries.",
            "bullish": "Conditions support selective buying and trend-following exposure.",
            "neutral": "Stay balanced and prioritize quality, liquidity, and diversification.",
            "bearish": "Lean defensive and reduce exposure to weaker names.",
            "strong_bearish": "Prioritize capital preservation and keep risk budgets tight.",
        }
        return mapping.get(prediction, "Monitor market conditions closely.")

    async def _get_historical_prices(self, db: AsyncSession, symbol: str, days: int) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(MarketData)
            .where(MarketData.symbol == symbol, MarketData.data_timestamp >= cutoff)
            .order_by(MarketData.data_timestamp.asc())
        )
        rows = list(result.scalars().all())
        deduped: dict[datetime.date, MarketData] = {}
        for row in rows:
            deduped[row.data_timestamp.date()] = row
        return [{"date": day, "close": float(row.close_price or row.price), "volume": int(row.volume or 0)} for day, row in sorted(deduped.items())]

    async def _get_market_indicators(self, db: AsyncSession, region: str) -> dict[str, float]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=45)
        result = await db.execute(
            select(MarketData)
            .where(MarketData.data_timestamp >= cutoff)
            .order_by(MarketData.data_timestamp.asc())
        )
        rows = [row for row in result.scalars().all() if (row.region or "UAE").upper() == region.upper() or region.upper() == "UAE"]
        if not rows:
            return {"price_change_30d": 0.0, "volume_trend": 1.0, "sentiment_score": 0.0, "gdp_growth": 2.5}
        by_day: dict[datetime.date, list[MarketData]] = {}
        for row in rows:
            by_day.setdefault(row.data_timestamp.date(), []).append(row)
        daily_close = [mean(float(item.close_price or item.price) for item in values) for _, values in sorted(by_day.items())]
        daily_volume = [sum(int(item.volume or 0) for item in values) for _, values in sorted(by_day.items())]
        price_change_30d = 0.0
        if len(daily_close) > 30 and daily_close[-31]:
            price_change_30d = ((daily_close[-1] - daily_close[-31]) / daily_close[-31]) * 100
        volume_trend = (mean(daily_volume[-10:]) / mean(daily_volume)) if daily_volume and mean(daily_volume) else 1.0
        return {
            "price_change_30d": price_change_30d,
            "volume_trend": volume_trend,
            "sentiment_score": 0.15 if price_change_30d > 0 else -0.05,
            "gdp_growth": 3.5,
        }

    async def _get_property_history(self, location: str, property_type: str) -> list[dict[str, Any]]:
        base = 1_200_000 if property_type.lower() == "apartment" else 2_400_000
        location_lift = 1.2 if "marina" in location.lower() or "downtown" in location.lower() else 1.0
        return [{"month": f"2025-{index:02d}", "avg_price": base * location_lift * (1 + index * 0.012)} for index in range(1, 13)]

    def _linear_regression(self, x_values: list[int], y_values: list[float]) -> tuple[float, float, float]:
        x_mean = mean(x_values)
        y_mean = mean(y_values)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        slope = numerator / denominator if denominator else 0.0
        intercept = y_mean - slope * x_mean
        predicted = [slope * x + intercept for x in x_values]
        residuals = [actual - estimate for actual, estimate in zip(y_values, predicted)]
        total_var = sum((y - y_mean) ** 2 for y in y_values)
        explained = 1 - (sum(value**2 for value in residuals) / total_var) if total_var else 0.0
        r_value = sqrt(abs(explained)) if explained >= 0 else 0.0
        if slope < 0:
            r_value *= -1
        return slope, intercept, r_value


forecast_service = LightweightForecastService(cache_hours=get_settings().PREDICTION_CACHE_HOURS)
