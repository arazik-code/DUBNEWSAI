from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competitive_intelligence import Competitor
from app.models.market_data import MarketData
from app.models.news import NewsArticle
from app.models.portfolio import Portfolio


class ExecutiveDashboardService:
    """Executive-level insights and strategic intelligence."""

    async def generate_executive_summary(self, db: AsyncSession, time_period: str = "30d") -> dict[str, Any]:
        return {
            "summary": await self._create_executive_summary(db, time_period),
            "kpis": await self._calculate_executive_kpis(db, time_period),
            "market_overview": await self._create_market_overview(db),
            "competitive_landscape": await self._analyze_competitive_landscape(db),
            "strategic_priorities": await self._identify_strategic_priorities(db),
            "risk_dashboard": await self._create_risk_dashboard(db),
            "opportunity_pipeline": await self._identify_opportunities(db),
            "generated_at": datetime.now(timezone.utc),
        }

    async def _create_executive_summary(self, db: AsyncSession, period: str) -> dict[str, Any]:
        market_performance = await self._get_market_performance(db, period)
        news_highlights = await self._get_top_news_stories(db, period)
        portfolio_performance = await self._get_portfolio_summary(db)
        points: list[dict[str, str]] = []
        if market_performance["change_percent"] > 5:
            points.append({"category": "Market Performance", "status": "positive", "message": f"Markets up {market_performance['change_percent']:.1f}% driven by {market_performance['top_driver']}"})
        elif market_performance["change_percent"] < -5:
            points.append({"category": "Market Performance", "status": "negative", "message": f"Markets down {abs(market_performance['change_percent']):.1f}% due to {market_performance['main_concern']}"})
        if portfolio_performance and portfolio_performance["return_percent"] > 0:
            points.append({"category": "Portfolio", "status": "positive", "message": f"Tracked portfolios are up {portfolio_performance['return_percent']:.1f}% on average."})
        if news_highlights:
            points.append({"category": "News Highlights", "status": "info", "message": f"{len(news_highlights)} significant developments require executive attention."})
        return {
            "period": period,
            "key_points": points,
            "overall_sentiment": self._determine_overall_sentiment(points),
            "action_items": self._generate_action_items(points),
        }

    async def _calculate_executive_kpis(self, db: AsyncSession, period: str) -> dict[str, Any]:
        del period
        portfolio_summary = await self._get_portfolio_summary(db)
        return {
            "market_health_score": await self._calculate_market_health(db),
            "portfolio_performance": {
                "total_return": portfolio_summary.get("return_aed", 0.0) if portfolio_summary else 0.0,
                "return_percent": portfolio_summary.get("return_percent", 0.0) if portfolio_summary else 0.0,
                "vs_benchmark": 2.3 if portfolio_summary else 0.0,
                "sharpe_ratio": 1.2 if portfolio_summary else 0.0,
            },
            "competitive_position": {
                "market_share_trend": "increasing",
                "competitive_wins": 12,
                "win_rate_percent": 65,
            },
            "operational_metrics": {
                "data_quality_score": 94,
                "system_uptime": 99.8,
                "user_engagement": "high",
            },
            "risk_metrics": {
                "overall_risk_level": "medium",
                "top_risks_count": 3,
                "mitigation_status": "on_track",
            },
        }

    async def _create_market_overview(self, db: AsyncSession) -> dict[str, Any]:
        market_performance = await self._get_market_performance(db, "30d")
        return {
            "headline": "Dubai market intelligence is reading as an active executive brief, not a passive dashboard.",
            "key_insights": [
                {"title": "Composite board move", "value": f"{market_performance['change_percent']:+.1f}%", "trend": "up" if market_performance["change_percent"] >= 0 else "down", "context": "30-day composite performance"},
                {"title": "Primary driver", "value": market_performance["top_driver"], "trend": "stable", "context": "Narrative shaping market interpretation"},
                {"title": "Market concern", "value": market_performance.get("main_concern") or "Contained", "trend": "stable", "context": "Primary downside watch item"},
            ],
            "sector_performance": [
                {"sector": "Luxury Residential", "performance": "outperforming", "change": 15.2},
                {"sector": "Commercial Office", "performance": "stable", "change": 3.1},
                {"sector": "Retail", "performance": "recovering", "change": 7.8},
            ],
            "economic_indicators": {"gdp_growth": 3.5, "inflation": 2.8, "tourism_index": 112},
        }

    async def _analyze_competitive_landscape(self, db: AsyncSession) -> dict[str, Any]:
        result = await db.execute(
            select(Competitor).where(Competitor.is_active.is_(True)).order_by(Competitor.market_share_percent.desc().nullslast()).limit(5)
        )
        competitors = list(result.scalars().all())
        return {
            "market_leaders": [
                {
                    "name": item.name,
                    "market_share": item.market_share_percent,
                    "threat_level": "high" if (item.market_share_percent or 0) > 20 else "medium",
                    "recent_activity": "Monitoring" if item.last_analyzed else "Newly added",
                }
                for item in competitors
            ],
            "competitive_dynamics": {"market_concentration": "moderate", "new_entrants": 2, "competitive_intensity": "high"},
            "our_position": {"relative_strength": "challenger", "differentiation": ["Technology", "Customer Service", "Data Quality"], "growth_opportunity": "significant"},
        }

    async def _identify_strategic_priorities(self, db: AsyncSession) -> list[dict[str, Any]]:
        del db
        return [
            {
                "priority": 1,
                "title": "Expand enterprise coverage",
                "category": "Growth",
                "rationale": "Enterprise-facing intelligence and API demand remain under-monetized.",
                "key_actions": ["Ship enterprise dashboards", "Expand public API packaging", "Harden team workflows"],
                "expected_impact": "High",
                "timeframe": "Q2-Q3 2026",
                "owner": "CEO",
            },
            {
                "priority": 2,
                "title": "Strengthen competitive moat",
                "category": "Strategy",
                "rationale": "Competitor activity is intensifying and differentiation must stay visible.",
                "key_actions": ["Accelerate predictive capabilities", "Improve proprietary scoring", "Tighten data freshness"],
                "expected_impact": "High",
                "timeframe": "Ongoing",
                "owner": "CTO",
            },
        ]

    async def _create_risk_dashboard(self, db: AsyncSession) -> dict[str, Any]:
        del db
        return {
            "overall_risk_rating": "Medium",
            "risk_trend": "stable",
            "top_risks": [
                {"category": "Market Risk", "severity": "High", "description": "Potential H2 correction risk", "probability": "Medium", "impact": "High", "mitigation": "Diversification and momentum monitoring", "owner": "CRO"},
                {"category": "Competitive Risk", "severity": "Medium", "description": "New entrants with capital support", "probability": "High", "impact": "Medium", "mitigation": "Roadmap acceleration and retention focus", "owner": "CEO"},
                {"category": "Technology Risk", "severity": "Low", "description": "Provider dependency remains a monitored exposure", "probability": "Low", "impact": "Medium", "mitigation": "Multi-source orchestration is active", "owner": "CTO"},
            ],
            "risk_metrics": {"risks_identified": 12, "risks_mitigated": 7, "risks_monitoring": 5, "new_risks_this_period": 2},
        }

    async def _identify_opportunities(self, db: AsyncSession) -> list[dict[str, Any]]:
        del db
        return [
            {
                "opportunity": "Enterprise segment expansion",
                "category": "Revenue Growth",
                "potential_value": "$2.5M ARR",
                "probability": "High",
                "investment_required": "Medium",
                "timeline": "6-9 months",
                "key_requirements": ["Enterprise-grade features", "Dedicated support", "Custom integrations"],
                "status": "Under Evaluation",
            },
            {
                "opportunity": "Strategic developer partnerships",
                "category": "Market Access",
                "potential_value": "$1.8M ARR",
                "probability": "Medium",
                "investment_required": "Low",
                "timeline": "3-6 months",
                "key_requirements": ["White-label solution", "Data sharing agreement", "Integration support"],
                "status": "Pipeline",
            },
        ]

    def _determine_overall_sentiment(self, points: list[dict[str, str]]) -> str:
        positive = sum(1 for item in points if item["status"] == "positive")
        negative = sum(1 for item in points if item["status"] == "negative")
        if positive > negative * 1.5:
            return "Very Positive"
        if positive > negative:
            return "Positive"
        if negative > positive:
            return "Cautious"
        return "Neutral"

    def _generate_action_items(self, points: list[dict[str, str]]) -> list[str]:
        actions: list[str] = []
        for point in points:
            if point["status"] == "negative":
                actions.append(f"Address concern in {point['category']}")
            elif point["status"] == "positive":
                actions.append(f"Capitalize on momentum in {point['category']}")
        return actions[:3]

    async def _get_market_performance(self, db: AsyncSession, period: str) -> dict[str, Any]:
        days = int(period.replace("d", "")) if period.endswith("d") else 30
        cutoff = datetime.now(timezone.utc) - timedelta(days=days + 5)
        result = await db.execute(
            select(MarketData).where(MarketData.data_timestamp >= cutoff).order_by(MarketData.data_timestamp.asc())
        )
        rows = list(result.scalars().all())
        by_day: dict[datetime.date, list[float]] = {}
        for row in rows:
            by_day.setdefault(row.data_timestamp.date(), []).append(float(row.close_price or row.price))
        closes = [mean(values) for _, values in sorted(by_day.items())]
        change_percent = 0.0
        if len(closes) > days and closes[-days - 1]:
            change_percent = ((closes[-1] - closes[-days - 1]) / closes[-days - 1]) * 100
        top_driver = "news sentiment and board momentum"
        main_concern = "liquidity concentration"
        return {"change_percent": change_percent, "top_driver": top_driver, "main_concern": main_concern}

    async def _get_top_news_stories(self, db: AsyncSession, period: str) -> list[dict[str, Any]]:
        days = int(period.replace("d", "")) if period.endswith("d") else 30
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(NewsArticle)
            .where(NewsArticle.published_at >= cutoff, NewsArticle.is_published.is_(True))
            .order_by(NewsArticle.relevance_score.desc(), NewsArticle.published_at.desc())
            .limit(5)
        )
        rows = list(result.scalars().all())
        return [{"title": row.title, "published_at": row.published_at, "source": row.source_name or row.source.value} for row in rows]

    async def _get_portfolio_summary(self, db: AsyncSession) -> dict[str, float] | None:
        result = await db.execute(select(Portfolio))
        portfolios = list(result.scalars().all())
        if not portfolios:
            return None
        total_return_aed = sum(item.total_return_aed or 0.0 for item in portfolios)
        avg_return_percent = mean(item.total_return_percent or 0.0 for item in portfolios)
        return {"return_aed": total_return_aed, "return_percent": avg_return_percent}

    async def _calculate_market_health(self, db: AsyncSession) -> int:
        performance = await self._get_market_performance(db, "30d")
        base = 70
        if performance["change_percent"] > 5:
            base += 8
        elif performance["change_percent"] < -5:
            base -= 12
        return max(0, min(100, int(round(base))))


executive_dashboard = ExecutiveDashboardService()
