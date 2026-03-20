from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_data import EconomicIndicator, MarketData
from app.models.news import NewsArticle
from app.models.portfolio import InvestmentRecommendation
from app.utils.symbols import display_symbol, normalize_symbol, symbol_metadata


class InvestmentScoringService:
    """Heuristic investment scoring engine powered by live platform data."""

    async def score_investment(
        self,
        db: AsyncSession,
        *,
        symbol: str,
        user_risk_profile: str = "moderate",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        normalized_symbol = normalize_symbol(symbol)
        fundamental_data = await self._get_fundamental_data(db, normalized_symbol)
        technical_data = await self._get_technical_data(db, normalized_symbol)
        sentiment_data = await self._get_sentiment_data(db, normalized_symbol)
        macro_data = await self._get_macro_context(db)

        scores = {
            "fundamental_score": self._score_fundamentals(fundamental_data),
            "technical_score": self._score_technicals(technical_data),
            "sentiment_score": self._score_sentiment(sentiment_data),
            "macro_score": self._score_macro_environment(macro_data),
            "valuation_score": self._score_valuation(fundamental_data, technical_data),
        }
        weights = self._get_weights_for_risk_profile(user_risk_profile)
        overall_score = sum(scores[key] * weights[key] for key in scores)
        recommendation = self._generate_recommendation(overall_score, scores, fundamental_data, technical_data, sentiment_data)

        payload = {
            "symbol": display_symbol(normalized_symbol),
            "overall_score": round(overall_score, 2),
            "component_scores": {key: round(value, 2) for key, value in scores.items()},
            "recommendation": recommendation["action"],
            "confidence": recommendation["confidence"],
            "rationale": recommendation["rationale"],
            "key_factors": recommendation["key_factors"],
            "risks": recommendation["risks"],
            "target_price": recommendation["target_price"],
            "stop_loss": recommendation["stop_loss"],
            "time_horizon": recommendation["time_horizon"],
            "generated_at": datetime.now(timezone.utc),
        }

        if user_id is not None:
            await self._persist_recommendation(
                db,
                user_id=user_id,
                symbol=normalized_symbol,
                technical_data=technical_data,
                payload=payload,
            )
        return payload

    def _score_fundamentals(self, data: dict[str, Any]) -> float:
        score = 50.0
        pe_ratio = data.get("pe_ratio")
        if pe_ratio:
            if 8 <= pe_ratio <= 22:
                score += 15
            elif 5 <= pe_ratio < 8 or 22 < pe_ratio <= 32:
                score += 8

        margin_quality = data.get("margin_quality", 0.0)
        if margin_quality > 12:
            score += 15
        elif margin_quality > 7:
            score += 10
        elif margin_quality > 3:
            score += 5

        dividend_yield = data.get("dividend_yield", 0.0)
        if 2 <= dividend_yield <= 8:
            score += 10
        elif dividend_yield > 0:
            score += 5

        balance_strength = data.get("balance_strength", 0.0)
        score += max(0.0, min(15.0, balance_strength))
        return min(100.0, max(0.0, score))

    def _score_technicals(self, data: dict[str, Any]) -> float:
        score = 50.0
        rsi = data.get("rsi", 50.0)
        if 40 <= rsi <= 60:
            score += 15
        elif 30 <= rsi < 40:
            score += 20
        elif rsi < 30:
            score += 10
        elif 60 < rsi <= 70:
            score += 5

        if data.get("macd_signal") == "buy":
            score += 15
        elif data.get("macd_signal") == "hold":
            score += 5

        current_price = data.get("current_price")
        ma_20 = data.get("ma_20")
        ma_50 = data.get("ma_50")
        if current_price and ma_20 and ma_50:
            if current_price > ma_20 > ma_50:
                score += 20
            elif current_price > ma_20:
                score += 10
        return min(100.0, max(0.0, score))

    def _score_sentiment(self, data: dict[str, Any]) -> float:
        score = 50.0
        score += data.get("news_sentiment", 0.0) * 25
        analyst_consensus = data.get("analyst_consensus", "hold")
        if analyst_consensus == "strong_buy":
            score += 15
        elif analyst_consensus == "buy":
            score += 10
        elif analyst_consensus == "sell":
            score -= 10
        elif analyst_consensus == "strong_sell":
            score -= 15
        return min(100.0, max(0.0, score))

    def _score_macro_environment(self, data: dict[str, Any]) -> float:
        score = 50.0
        gdp_growth = data.get("gdp_growth", 0.0)
        inflation = data.get("inflation", 2.5)
        rates_trend = data.get("interest_rates_trend", "stable")

        if gdp_growth > 3:
            score += 15
        elif gdp_growth > 2:
            score += 10
        elif gdp_growth < 0:
            score -= 15

        if 1 <= inflation <= 3:
            score += 10
        elif inflation > 5:
            score -= 15

        if rates_trend == "falling":
            score += 15
        elif rates_trend == "rising":
            score -= 10
        return min(100.0, max(0.0, score))

    def _score_valuation(self, fundamental: dict[str, Any], technical: dict[str, Any]) -> float:
        score = 50.0
        current_price = technical.get("current_price", 0.0)
        fair_value = fundamental.get("fair_value", current_price)
        if fair_value and current_price:
            discount = ((fair_value - current_price) / fair_value) * 100
            if discount > 20:
                score += 25
            elif discount > 10:
                score += 15
            elif -10 <= discount <= 10:
                score += 5
            elif discount < -20:
                score -= 20
        return min(100.0, max(0.0, score))

    def _get_weights_for_risk_profile(self, profile: str) -> dict[str, float]:
        profiles = {
            "conservative": {
                "fundamental_score": 0.35,
                "technical_score": 0.15,
                "sentiment_score": 0.15,
                "macro_score": 0.20,
                "valuation_score": 0.15,
            },
            "moderate": {
                "fundamental_score": 0.30,
                "technical_score": 0.20,
                "sentiment_score": 0.20,
                "macro_score": 0.15,
                "valuation_score": 0.15,
            },
            "aggressive": {
                "fundamental_score": 0.20,
                "technical_score": 0.30,
                "sentiment_score": 0.25,
                "macro_score": 0.10,
                "valuation_score": 0.15,
            },
        }
        return profiles.get(profile, profiles["moderate"])

    def _generate_recommendation(
        self,
        overall_score: float,
        component_scores: dict[str, float],
        fundamental: dict[str, Any],
        technical: dict[str, Any],
        sentiment: dict[str, Any],
    ) -> dict[str, Any]:
        if overall_score >= 75:
            action = "Strong Buy"
            confidence = "High"
        elif overall_score >= 60:
            action = "Buy"
            confidence = "Medium"
        elif overall_score >= 45:
            action = "Hold"
            confidence = "Medium"
        elif overall_score >= 30:
            action = "Sell"
            confidence = "Medium"
        else:
            action = "Strong Sell"
            confidence = "High"

        rationale_parts: list[str] = []
        key_factors: list[str] = []
        risks: list[str] = []
        sorted_scores = sorted(component_scores.items(), key=lambda item: item[1], reverse=True)
        for component, score in sorted_scores[:2]:
            if score > 70:
                label = component.replace("_score", "").replace("_", " ").title()
                rationale_parts.append(f"strong {label.lower()}")
                key_factors.append(f"{label} is screening well ({score:.0f}/100)")
        for component, score in sorted_scores[-2:]:
            if score < 40:
                label = component.replace("_score", "").replace("_", " ").title()
                risks.append(f"{label} is weak ({score:.0f}/100)")

        if sentiment.get("news_sentiment", 0) < -0.2:
            risks.append("Recent news flow is leaning negative.")
        if technical.get("rsi", 50) > 72:
            risks.append("Momentum is extended and may need to cool.")

        current_price = technical.get("current_price", 100.0)
        fair_value = fundamental.get("fair_value", current_price or 100.0)
        target_price = current_price + (fair_value - current_price) * 0.8 if current_price else fair_value
        stop_loss = current_price * 0.92 if current_price else 0.0
        time_horizon = "3-6 months" if confidence == "High" else "6-12 months"

        return {
            "action": action,
            "confidence": confidence,
            "rationale": f"{action} based on " + " and ".join(rationale_parts) if rationale_parts else action,
            "key_factors": key_factors,
            "risks": risks,
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "time_horizon": time_horizon,
        }

    async def _get_fundamental_data(self, db: AsyncSession, symbol: str) -> dict[str, Any]:
        result = await db.execute(
            select(MarketData).where(MarketData.symbol == symbol).order_by(MarketData.data_timestamp.desc()).limit(60)
        )
        rows = list(result.scalars().all())
        latest = rows[0] if rows else None
        prices = [float(row.price) for row in rows if row.price]
        balance_strength = 15.0 if latest and latest.confidence_level == "high" else 8.0
        return {
            "pe_ratio": latest.pe_ratio if latest else None,
            "dividend_yield": float(latest.dividend_yield or 0.0) if latest else 0.0,
            "fair_value": float(mean(prices[-20:])) if prices else 0.0,
            "margin_quality": max(0.0, min(15.0, (latest.data_quality_score or 50.0) / 5)) if latest else 0.0,
            "balance_strength": balance_strength,
        }

    async def _get_technical_data(self, db: AsyncSession, symbol: str) -> dict[str, Any]:
        result = await db.execute(
            select(MarketData).where(MarketData.symbol == symbol).order_by(MarketData.data_timestamp.asc()).limit(120)
        )
        rows = list(result.scalars().all())
        closes = [float(row.price) for row in rows if row.price]
        volumes = [float(row.volume or 0.0) for row in rows]
        if not closes:
            return {}
        rsi = self._compute_rsi(closes, 14)
        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)
        macd = ema_12[-1] - ema_26[-1] if ema_12 and ema_26 else 0.0
        macd_signal = self._ema([a - b for a, b in zip(ema_12, ema_26)], 9)
        signal_value = macd_signal[-1] if macd_signal else 0.0
        ma_20 = mean(closes[-20:]) if len(closes) >= 20 else mean(closes)
        ma_50 = mean(closes[-50:]) if len(closes) >= 50 else mean(closes)
        return {
            "current_price": closes[-1],
            "rsi": rsi[-1] if rsi else 50.0,
            "ma_20": ma_20,
            "ma_50": ma_50,
            "macd_signal": "buy" if macd > signal_value else "hold" if abs(macd - signal_value) < 0.01 else "sell",
            "volume_trend": (mean(volumes[-10:]) / mean(volumes)) if volumes and mean(volumes) else 1.0,
        }

    async def _get_sentiment_data(self, db: AsyncSession, symbol: str) -> dict[str, Any]:
        from_date = datetime.now(timezone.utc) - timedelta(days=30)
        result = await db.execute(
            select(NewsArticle)
            .where(
                and_(
                    NewsArticle.published_at >= from_date,
                    NewsArticle.is_published.is_(True),
                )
            )
            .order_by(NewsArticle.published_at.desc())
        )
        articles = list(result.scalars().all())
        scores: list[float] = []
        symbol_lower = symbol.lower().replace(".du", "").replace(".ad", "")
        for article in articles:
            text = " ".join([article.title, article.description or "", article.content or ""]).lower()
            if symbol_lower in text:
                raw = float(article.sentiment_score or 0.0)
                scores.append(raw / 100 if abs(raw) > 1 else raw)
        avg_sentiment = mean(scores) if scores else 0.0
        analyst_consensus = "buy" if avg_sentiment > 0.15 else "sell" if avg_sentiment < -0.15 else "hold"
        return {"news_sentiment": avg_sentiment, "analyst_consensus": analyst_consensus}

    async def _get_macro_context(self, db: AsyncSession) -> dict[str, Any]:
        result = await db.execute(select(EconomicIndicator).order_by(EconomicIndicator.timestamp.desc()).limit(20))
        indicators = list(result.scalars().all())
        inflation = next((item.value for item in indicators if "inflation" in item.indicator_name.lower()), 2.8)
        gdp = next((item.value for item in indicators if "gdp" in item.indicator_name.lower()), 2.5)
        rates_trend = "stable"
        if inflation and inflation > 4:
            rates_trend = "rising"
        elif inflation and inflation < 2:
            rates_trend = "falling"
        return {"gdp_growth": gdp, "inflation": inflation, "interest_rates_trend": rates_trend}

    async def _persist_recommendation(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        symbol: str,
        technical_data: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        recommendation = InvestmentRecommendation(
            user_id=user_id,
            symbol=symbol,
            asset_name=(symbol_metadata(symbol).name if symbol_metadata(symbol) else symbol),
            recommendation_type=payload["recommendation"],
            confidence_score=85.0 if payload["confidence"] == "High" else 65.0,
            investment_score=payload["overall_score"],
            rationale=payload["rationale"],
            key_factors=payload["key_factors"],
            risks=payload["risks"],
            target_price=payload["target_price"],
            stop_loss_price=payload["stop_loss"],
            time_horizon_days=180 if payload["time_horizon"] == "3-6 months" else 365,
            recommendation_date=payload["generated_at"],
            price_at_recommendation=technical_data.get("current_price"),
            current_price=technical_data.get("current_price"),
            generated_by="hybrid",
            model_version="phase2-v1",
        )
        db.add(recommendation)
        await db.commit()

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

    def _ema(self, values: list[float], span: int) -> list[float]:
        if not values:
            return []
        multiplier = 2 / (span + 1)
        results = [values[0]]
        for value in values[1:]:
            results.append((value - results[-1]) * multiplier + results[-1])
        return results


investment_scoring = InvestmentScoringService()
