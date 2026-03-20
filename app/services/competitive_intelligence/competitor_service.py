from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.competitive_intelligence import (
    Competitor,
    CompetitorNewsMention,
    CompetitorPriceChange,
    CompetitorProduct,
    CompetitorSWOT,
)
from app.models.market_data import MarketData
from app.models.news import NewsArticle


class CompetitorService:
    """Comprehensive competitive intelligence service."""

    async def list_competitors(self, db: AsyncSession) -> list[Competitor]:
        result = await db.execute(
            select(Competitor)
            .options(selectinload(Competitor.products), selectinload(Competitor.news_mentions))
            .where(Competitor.is_active.is_(True))
            .order_by(Competitor.market_share_percent.desc().nullslast(), Competitor.name.asc())
        )
        return list(result.scalars().unique().all())

    async def create_competitor(self, db: AsyncSession, **payload: Any) -> Competitor:
        competitor = Competitor(**payload)
        db.add(competitor)
        await db.flush()
        await self._seed_competitor_market_context(db, competitor)
        await db.commit()
        await db.refresh(competitor)
        return competitor

    async def get_competitor(self, db: AsyncSession, competitor_id: int) -> Competitor | None:
        result = await db.execute(
            select(Competitor)
            .options(
                selectinload(Competitor.products),
                selectinload(Competitor.news_mentions),
                selectinload(Competitor.swot_analyses),
                selectinload(Competitor.price_changes),
            )
            .where(Competitor.id == competitor_id)
        )
        return result.scalar_one_or_none()

    async def analyze_competitor(self, db: AsyncSession, competitor_id: int) -> dict[str, Any]:
        competitor = await self.get_competitor(db, competitor_id)
        if competitor is None:
            raise ValueError("Competitor not found")

        analysis = {
            "competitor": self._serialize_competitor(competitor),
            "swot_analysis": await self._generate_swot(db, competitor),
            "news_intelligence": await self._analyze_news_mentions(db, competitor),
            "market_positioning": await self._analyze_market_position(db, competitor),
            "product_comparison": await self._compare_products(db, competitor),
            "pricing_analysis": await self._analyze_pricing(db, competitor),
            "performance_trends": await self._analyze_performance_trends(db, competitor),
            "threat_assessment": await self._assess_threat_level(db, competitor),
            "strategic_insights": await self._generate_strategic_insights(db, competitor),
        }
        competitor.last_analyzed = datetime.now(timezone.utc)
        await db.commit()
        return analysis

    async def get_swot(self, db: AsyncSession, competitor_id: int) -> dict[str, Any]:
        competitor = await self.get_competitor(db, competitor_id)
        if competitor is None:
            raise ValueError("Competitor not found")
        return await self._generate_swot(db, competitor)

    async def get_news(self, db: AsyncSession, competitor_id: int) -> dict[str, Any]:
        competitor = await self.get_competitor(db, competitor_id)
        if competitor is None:
            raise ValueError("Competitor not found")
        return await self._analyze_news_mentions(db, competitor)

    async def _generate_swot(self, db: AsyncSession, competitor: Competitor) -> dict[str, Any]:
        result = await db.execute(
            select(CompetitorSWOT)
            .where(
                CompetitorSWOT.competitor_id == competitor.id,
                CompetitorSWOT.analysis_date >= datetime.now(timezone.utc) - timedelta(days=30),
            )
            .order_by(CompetitorSWOT.analysis_date.desc())
            .limit(1)
        )
        swot = result.scalar_one_or_none()
        if swot is not None:
            return {
                "strengths": swot.strengths or [],
                "weaknesses": swot.weaknesses or [],
                "opportunities": swot.opportunities or [],
                "threats": swot.threats or [],
                "competitive_position": swot.competitive_position,
                "threat_level": swot.threat_level,
                "analysis_date": swot.analysis_date,
            }

        swot_data = await self._auto_generate_swot(db, competitor)
        record = CompetitorSWOT(
            competitor_id=competitor.id,
            strengths=swot_data["strengths"],
            weaknesses=swot_data["weaknesses"],
            opportunities=swot_data["opportunities"],
            threats=swot_data["threats"],
            competitive_position=swot_data["competitive_position"],
            threat_level=swot_data["threat_level"],
            analysis_date=datetime.now(timezone.utc),
            data_sources=["market_data", "news_articles", "competitor_profile"],
        )
        db.add(record)
        await db.commit()
        return swot_data

    async def _auto_generate_swot(self, db: AsyncSession, competitor: Competitor) -> dict[str, Any]:
        strengths: list[dict[str, str]] = []
        weaknesses: list[dict[str, str]] = []
        opportunities: list[dict[str, str]] = []
        threats: list[dict[str, str]] = []

        if competitor.market_cap:
            if competitor.market_cap > 10_000_000_000:
                strengths.append({"category": "Financial", "description": f"Strong market capitalization around {competitor.market_cap:,.0f}", "impact": "high"})
            elif competitor.market_cap < 1_000_000_000:
                weaknesses.append({"category": "Financial", "description": "Limited financial resources versus sector leaders", "impact": "medium"})

        if competitor.revenue_growth_rate:
            if competitor.revenue_growth_rate > 20:
                strengths.append({"category": "Growth", "description": f"Rapid revenue growth at {competitor.revenue_growth_rate:.1f}%", "impact": "high"})
                threats.append({"category": "Competition", "description": "Fast-growing competitor may capture share aggressively", "impact": "high"})
            elif competitor.revenue_growth_rate < 5:
                weaknesses.append({"category": "Growth", "description": "Growth is slowing versus expansion peers", "impact": "medium"})

        if competitor.market_share_percent:
            if competitor.market_share_percent > 25:
                strengths.append({"category": "Market Position", "description": f"Large market share at {competitor.market_share_percent:.1f}%", "impact": "high"})
                threats.append({"category": "Dominance", "description": "Scale allows aggressive price or marketing moves", "impact": "critical"})
            elif competitor.market_share_percent < 5:
                opportunities.append({"category": "Market Share", "description": "Still a niche player with limited penetration", "impact": "medium"})

        news = await self._analyze_news_mentions(db, competitor)
        avg_sentiment = float(news.get("average_sentiment", 0.0))
        if avg_sentiment > 0.25:
            strengths.append({"category": "Brand", "description": "Positive media narrative supports brand momentum", "impact": "medium"})
        elif avg_sentiment < -0.25:
            weaknesses.append({"category": "Reputation", "description": "Negative coverage is weakening perception", "impact": "high"})
            opportunities.append({"category": "Differentiation", "description": "Reputation softness creates positioning space", "impact": "high"})

        result = await db.execute(
            select(CompetitorProduct).where(CompetitorProduct.competitor_id == competitor.id)
        )
        products = list(result.scalars().all())
        if len(products) > 5:
            strengths.append({"category": "Product Portfolio", "description": f"Broad offering set with {len(products)} products", "impact": "medium"})
        elif len(products) == 0:
            weaknesses.append({"category": "Product Portfolio", "description": "No structured product coverage has been cataloged yet", "impact": "low"})

        strength_score = len([item for item in strengths if item["impact"] == "high"]) * 2 + len(strengths)
        weakness_score = len([item for item in weaknesses if item["impact"] == "high"]) * 2 + len(weaknesses)
        if strength_score > weakness_score * 1.5:
            position = "leader"
            threat_level = "high"
        elif strength_score > weakness_score:
            position = "challenger"
            threat_level = "medium"
        elif weakness_score > strength_score * 1.5:
            position = "follower"
            threat_level = "low"
        else:
            position = "niche"
            threat_level = "medium"

        return {
            "strengths": strengths[:5],
            "weaknesses": weaknesses[:5],
            "opportunities": opportunities[:5],
            "threats": threats[:5],
            "competitive_position": position,
            "threat_level": threat_level,
        }

    async def _analyze_news_mentions(self, db: AsyncSession, competitor: Competitor) -> dict[str, Any]:
        result = await db.execute(
            select(CompetitorNewsMention)
            .where(
                CompetitorNewsMention.competitor_id == competitor.id,
                CompetitorNewsMention.published_at >= datetime.now(timezone.utc) - timedelta(days=90),
            )
            .order_by(CompetitorNewsMention.published_at.desc())
        )
        mentions = list(result.scalars().all())
        if not mentions:
            return {"total_mentions": 0, "coverage_trend": "unknown", "sentiment": "neutral", "average_sentiment": 0.0, "top_stories": []}

        sentiments = [item.sentiment_score for item in mentions if item.sentiment_score is not None]
        avg_sentiment = mean(sentiments) if sentiments else 0.0
        types = Counter(item.mention_type for item in mentions if item.mention_type)
        recent_30 = [item for item in mentions if item.published_at and item.published_at >= datetime.now(timezone.utc) - timedelta(days=30)]
        older_30 = [item for item in mentions if item.published_at and datetime.now(timezone.utc) - timedelta(days=60) <= item.published_at < datetime.now(timezone.utc) - timedelta(days=30)]
        trend = "stable"
        if older_30:
            trend = "increasing" if len(recent_30) > len(older_30) else "decreasing"

        top = sorted(mentions, key=lambda item: item.importance_score or 0.0, reverse=True)[:5]
        return {
            "total_mentions": len(mentions),
            "average_sentiment": round(avg_sentiment, 3),
            "sentiment_label": "positive" if avg_sentiment > 0.2 else "negative" if avg_sentiment < -0.2 else "neutral",
            "coverage_trend": trend,
            "mention_breakdown": dict(types.most_common(5)),
            "top_stories": [
                {
                    "title": item.article_title,
                    "source": item.source,
                    "published_at": item.published_at,
                    "sentiment": item.sentiment_score,
                    "type": item.mention_type,
                }
                for item in top
            ],
        }

    async def _analyze_market_position(self, db: AsyncSession, competitor: Competitor) -> dict[str, Any]:
        result = await db.execute(
            select(Competitor).where(Competitor.sector == competitor.sector, Competitor.is_active.is_(True))
        )
        peers = list(result.scalars().all())
        market_caps = sorted([(item.id, item.market_cap or 0.0) for item in peers], key=lambda item: item[1], reverse=True)
        market_shares = sorted([(item.id, item.market_share_percent or 0.0) for item in peers], key=lambda item: item[1], reverse=True)
        cap_rank = next((index + 1 for index, (item_id, _) in enumerate(market_caps) if item_id == competitor.id), None)
        share_rank = next((index + 1 for index, (item_id, _) in enumerate(market_shares) if item_id == competitor.id), None)

        total_share = sum(value for _, value in market_shares)
        hhi = 0.0
        if total_share:
            hhi = sum(((value / total_share) * 100) ** 2 for _, value in market_shares)
        structure = "competitive"
        if hhi > 2500:
            structure = "highly concentrated"
        elif hhi > 1500:
            structure = "moderately concentrated"

        return {
            "sector": competitor.sector,
            "total_competitors": len(peers),
            "market_cap_rank": cap_rank,
            "market_share_rank": share_rank,
            "market_share_percent": competitor.market_share_percent,
            "market_concentration_hhi": round(hhi, 2),
            "market_structure": structure,
            "competitive_intensity": "high" if len(peers) > 10 else "medium" if len(peers) > 5 else "low",
        }

    async def _compare_products(self, db: AsyncSession, competitor: Competitor) -> dict[str, Any]:
        result = await db.execute(
            select(CompetitorProduct).where(CompetitorProduct.competitor_id == competitor.id)
        )
        products = list(result.scalars().all())
        prices = [item.price for item in products if item.price is not None]
        return {
            "product_count": len(products),
            "products": [
                {
                    "name": item.product_name,
                    "category": item.category,
                    "price": item.price,
                    "pricing_model": item.pricing_model,
                    "key_features_count": len(item.key_features or []),
                    "market_reception": item.market_reception,
                    "estimated_users": item.estimated_users,
                    "our_advantage": item.weaknesses,
                    "their_advantage": item.strengths,
                }
                for item in products[:5]
            ],
            "avg_price": round(mean(prices), 2) if prices else None,
            "pricing_strategy": self._determine_pricing_strategy(prices),
        }

    async def _analyze_pricing(self, db: AsyncSession, competitor: Competitor) -> dict[str, Any]:
        result = await db.execute(
            select(CompetitorProduct).where(CompetitorProduct.competitor_id == competitor.id)
        )
        products = list(result.scalars().all())
        prices = [item.price for item in products if item.price is not None]
        if not prices:
            return {"strategy": "unknown"}
        return {
            "average_price": round(mean(prices), 2),
            "price_range": (round(min(prices), 2), round(max(prices), 2)),
            "pricing_strategy": self._determine_pricing_strategy(prices),
            "product_count": len(products),
            "pricing_models": sorted({item.pricing_model for item in products if item.pricing_model}),
        }

    async def _analyze_performance_trends(self, db: AsyncSession, competitor: Competitor) -> dict[str, Any]:
        if not competitor.ticker_symbol:
            return {"is_public": False}

        result = await db.execute(
            select(CompetitorPriceChange)
            .where(
                CompetitorPriceChange.competitor_id == competitor.id,
                CompetitorPriceChange.date >= datetime.now(timezone.utc) - timedelta(days=90),
            )
            .order_by(CompetitorPriceChange.date.asc())
        )
        price_history = list(result.scalars().all())
        if len(price_history) < 2:
            return {"is_public": True, "data_available": False}

        prices = [item.close_price or 0.0 for item in price_history]
        returns = self._pct_changes(prices)
        current_price = prices[-1]
        price_30 = prices[-30] if len(prices) >= 30 else prices[0]
        price_90 = prices[0]
        return {
            "is_public": True,
            "current_price": current_price,
            "change_30d": round(((current_price - price_30) / price_30 * 100) if price_30 else 0.0, 2),
            "change_90d": round(((current_price - price_90) / price_90 * 100) if price_90 else 0.0, 2),
            "volatility": round((pstdev(returns) * 100) if len(returns) > 1 else 0.0, 2),
            "trend": "upward" if current_price > price_30 else "downward",
            "momentum": "strong" if price_30 and abs((current_price - price_30) / price_30) > 0.1 else "weak",
        }

    async def _assess_threat_level(self, db: AsyncSession, competitor: Competitor) -> dict[str, Any]:
        threat_factors: list[dict[str, str]] = []
        threat_score = 0
        if competitor.market_share_percent:
            if competitor.market_share_percent > 25:
                threat_factors.append({"factor": "Market Dominance", "severity": "critical", "description": f"{competitor.market_share_percent:.1f}% market share"})
                threat_score += 30
            elif competitor.market_share_percent > 10:
                threat_factors.append({"factor": "Significant Market Share", "severity": "high", "description": f"{competitor.market_share_percent:.1f}% market share"})
                threat_score += 20
        if competitor.revenue_growth_rate and competitor.revenue_growth_rate > 20:
            threat_factors.append({"factor": "Rapid Growth", "severity": "high", "description": f"{competitor.revenue_growth_rate:.1f}% revenue growth"})
            threat_score += 25
        if competitor.market_cap and competitor.market_cap > 10_000_000_000:
            threat_factors.append({"factor": "Financial Resources", "severity": "high", "description": "Large resource base enables aggressive competition"})
            threat_score += 20

        result = await db.execute(
            select(func.count(CompetitorProduct.id)).where(
                CompetitorProduct.competitor_id == competitor.id,
                CompetitorProduct.launch_date >= datetime.now(timezone.utc) - timedelta(days=180),
            )
        )
        recent_launches = int(result.scalar() or 0)
        if recent_launches >= 3:
            threat_factors.append({"factor": "Product Innovation", "severity": "medium", "description": f"{recent_launches} launches in the last 6 months"})
            threat_score += 15

        threat_level = "low"
        if threat_score >= 70:
            threat_level = "critical"
        elif threat_score >= 50:
            threat_level = "high"
        elif threat_score >= 30:
            threat_level = "medium"

        return {
            "threat_level": threat_level,
            "threat_score": threat_score,
            "threat_factors": threat_factors,
            "recommended_actions": self._get_threat_mitigation_actions(threat_level, threat_factors),
        }

    async def _generate_strategic_insights(self, db: AsyncSession, competitor: Competitor) -> list[dict[str, str]]:
        insights: list[dict[str, str]] = []
        swot = await self._generate_swot(db, competitor)
        news = await self._analyze_news_mentions(db, competitor)
        if swot["weaknesses"]:
            top = swot["weaknesses"][0]
            insights.append({
                "type": "opportunity",
                "priority": "high",
                "title": "Exploitable weakness identified",
                "description": f"Weakness in {top['category']}: {top['description']}",
                "recommendation": f"Position our strengths in {top['category']} to capture share.",
                "timeframe": "immediate",
            })
        if competitor.revenue_growth_rate and competitor.revenue_growth_rate > 15:
            insights.append({
                "type": "threat",
                "priority": "high",
                "title": "Competitor gaining momentum",
                "description": f"{competitor.name} is growing at {competitor.revenue_growth_rate:.1f}%.",
                "recommendation": "Accelerate product and go-to-market responses.",
                "timeframe": "urgent",
            })
        if float(news.get("average_sentiment", 0.0)) < -0.3:
            insights.append({
                "type": "opportunity",
                "priority": "medium",
                "title": "Competitor facing reputation drag",
                "description": "Negative media coverage creates a positioning window.",
                "recommendation": "Push reliability and trust themes in near-term campaigns.",
                "timeframe": "short-term",
            })
        if competitor.market_share_percent and competitor.market_share_percent < 5:
            insights.append({
                "type": "assessment",
                "priority": "low",
                "title": "Limited current threat",
                "description": f"Small market share at {competitor.market_share_percent:.1f}%.",
                "recommendation": "Monitor quarterly but avoid overreacting strategically.",
                "timeframe": "ongoing",
            })
        return insights

    async def _seed_competitor_market_context(self, db: AsyncSession, competitor: Competitor) -> None:
        if competitor.ticker_symbol:
            result = await db.execute(
                select(MarketData).where(MarketData.symbol == competitor.ticker_symbol).order_by(MarketData.data_timestamp.desc()).limit(60)
            )
            rows = list(result.scalars().all())
            for row in rows:
                db.add(
                    CompetitorPriceChange(
                        competitor_id=competitor.id,
                        date=row.data_timestamp,
                        open_price=row.open_price,
                        close_price=row.close_price or row.price,
                        high_price=row.high_price,
                        low_price=row.low_price,
                        volume=row.volume,
                        daily_change_percent=row.change_percent,
                        daily_change_amount=row.change,
                    )
                )

        terms = [competitor.name.lower()]
        if competitor.ticker_symbol:
            terms.append(competitor.ticker_symbol.lower().replace(".du", "").replace(".ad", ""))
        result = await db.execute(
            select(NewsArticle)
            .where(NewsArticle.is_published.is_(True))
            .order_by(NewsArticle.published_at.desc())
            .limit(300)
        )
        articles = list(result.scalars().all())
        for article in articles:
            text = " ".join([article.title, article.description or "", article.content or ""]).lower()
            if any(term and term in text for term in terms):
                db.add(
                    CompetitorNewsMention(
                        competitor_id=competitor.id,
                        article_title=article.title,
                        article_url=article.url,
                        source=article.source_name or article.source.value,
                        published_at=article.published_at,
                        excerpt=article.description,
                        full_content=article.content,
                        mention_type=self._classify_mention_type(text),
                        sentiment_score=(article.sentiment_score / 100 if abs(article.sentiment_score) > 1 else article.sentiment_score),
                        importance_score=float(article.relevance_score or article.quality_score or 50),
                        keywords=article.keywords or [],
                        entities_mentioned=(article.entities or {}).get("organizations", []),
                    )
                )

    def _determine_pricing_strategy(self, prices: list[float]) -> str:
        if not prices:
            return "unknown"
        avg_price = mean(prices)
        std_dev = pstdev(prices) if len(prices) > 1 else 0.0
        if avg_price and std_dev > avg_price * 0.5:
            return "differentiation"
        if avg_price < 50:
            return "penetration"
        if avg_price > 500:
            return "premium"
        return "competitive"

    def _get_threat_mitigation_actions(self, threat_level: str, factors: list[dict[str, str]]) -> list[str]:
        actions: list[str] = []
        if threat_level in {"critical", "high"}:
            actions.extend([
                "Run monthly competitor reviews.",
                "Accelerate roadmap delivery on differentiating features.",
                "Defend priority accounts with tailored messaging.",
            ])
        elif threat_level == "medium":
            actions.extend([
                "Monitor competitor activity weekly.",
                "Strengthen retention and customer proof points.",
            ])
        else:
            actions.append("Maintain quarterly competitive review cadence.")
        for factor in factors:
            if factor["factor"] == "Rapid Growth":
                actions.append("Deconstruct growth drivers and answer with targeted offers.")
            if factor["factor"] == "Product Innovation":
                actions.append("Shorten feature release cycles in exposed categories.")
        return list(dict.fromkeys(actions))

    def _classify_mention_type(self, text: str) -> str:
        if any(term in text for term in {"launch", "announced", "introduce"}):
            return "product_launch"
        if any(term in text for term in {"acquisition", "acquire", "buyout"}):
            return "acquisition"
        if any(term in text for term in {"funding", "raise", "investment"}):
            return "funding"
        if any(term in text for term in {"fine", "lawsuit", "controversy", "probe"}):
            return "scandal"
        return "general"

    def _pct_changes(self, values: list[float]) -> list[float]:
        changes: list[float] = []
        for index in range(1, len(values)):
            previous = values[index - 1]
            current = values[index]
            if previous:
                changes.append((current - previous) / previous)
        return changes

    def _serialize_competitor(self, competitor: Competitor) -> dict[str, Any]:
        return {
            "id": competitor.id,
            "name": competitor.name,
            "industry": competitor.industry,
            "sector": competitor.sector,
            "ticker_symbol": competitor.ticker_symbol,
            "market_cap": competitor.market_cap,
            "revenue_annual": competitor.revenue_annual,
            "revenue_growth_rate": competitor.revenue_growth_rate,
            "market_share_percent": competitor.market_share_percent,
            "employee_count": competitor.employee_count,
        }


competitor_service = CompetitorService()
