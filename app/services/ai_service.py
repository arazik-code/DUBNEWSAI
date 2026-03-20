from __future__ import annotations

import asyncio
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_models import get_ai_models
from app.core.cache import cache
from app.models.news import NewsArticle, NewsCategory


class AIService:
    STOPWORDS = {
        "a",
        "about",
        "after",
        "all",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "before",
        "by",
        "for",
        "from",
        "has",
        "have",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "said",
        "says",
        "that",
        "the",
        "their",
        "them",
        "there",
        "these",
        "they",
        "this",
        "to",
        "was",
        "were",
        "will",
        "with",
    }

    LOW_SIGNAL_KEYWORDS = {
        "article",
        "business",
        "coverage",
        "estate",
        "market",
        "news",
        "property",
        "real",
        "story",
        "update",
    }

    @staticmethod
    async def analyze_article(article: NewsArticle) -> dict[str, Any]:
        """Run sentiment, entity, keyword, and relevance analysis for an article."""
        ai_models = get_ai_models()

        text = ". ".join(
            part.strip()
            for part in [article.title, article.description or "", article.content or ""]
            if part and part.strip()
        )

        sentiment_result = await asyncio.to_thread(ai_models.analyze_sentiment, text, True)
        entities = await asyncio.to_thread(ai_models.extract_entities, text)
        extracted_keywords = await asyncio.to_thread(ai_models.extract_keywords, text, 10)
        keywords = AIService._sanitize_keywords(extracted_keywords, text=text)

        relevance_score = AIService._calculate_relevance_score(
            article=article,
            sentiment=sentiment_result,
            entities=entities,
            keywords=keywords,
        )

        return {
            "sentiment": sentiment_result["sentiment"],
            "sentiment_score": sentiment_result["sentiment_score"],
            "confidence": sentiment_result["confidence"],
            "entities": entities,
            "keywords": keywords,
            "relevance_score": relevance_score,
        }

    @classmethod
    def _sanitize_keywords(
        cls,
        keywords: list[str] | None,
        *,
        text: str = "",
        limit: int = 10,
    ) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()

        for keyword in keywords or []:
            normalized = " ".join(re.findall(r"[A-Za-z0-9][A-Za-z0-9&+/-]*", str(keyword).lower())).strip()
            if not normalized:
                continue
            if normalized in cls.STOPWORDS or normalized in cls.LOW_SIGNAL_KEYWORDS:
                continue
            if len(normalized) < 3:
                continue
            if normalized.isdigit():
                continue
            if normalized in seen:
                continue
            cleaned.append(normalized)
            seen.add(normalized)

        if len(cleaned) >= min(4, limit):
            return cleaned[:limit]

        fallback_counts = Counter(
            token
            for token in re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", text.lower())
            if token not in cls.STOPWORDS and token not in cls.LOW_SIGNAL_KEYWORDS
        )
        for token, _ in fallback_counts.most_common(limit):
            if token in seen:
                continue
            cleaned.append(token)
            seen.add(token)
            if len(cleaned) >= limit:
                break
        return cleaned[:limit]

    @staticmethod
    def _calculate_relevance_score(
        article: NewsArticle,
        sentiment: dict[str, Any],
        entities: dict[str, list[str]],
        keywords: list[str],
    ) -> int:
        score = 50

        real_estate_keywords = {
            "property",
            "real estate",
            "housing",
            "apartment",
            "villa",
            "rent",
            "rental",
            "sale",
            "market",
            "dubai",
            "developer",
            "construction",
            "mortgage",
            "off-plan",
        }
        keyword_matches = sum(
            1
            for keyword in keywords
            if any(target in keyword.lower() for target in real_estate_keywords)
        )
        score += min(keyword_matches * 5, 25)

        dubai_mentioned = any("dubai" in location.lower() for location in entities.get("locations", []))
        if dubai_mentioned:
            score += 15

        known_companies = {
            "emaar",
            "damac",
            "aldar",
            "nakheel",
            "sobha",
            "azizi",
            "meraas",
            "dubai properties",
        }
        company_matches = sum(
            1
            for organization in entities.get("organizations", [])
            if any(company in organization.lower() for company in known_companies)
        )
        score += min(company_matches * 10, 20)

        published_at = article.published_at
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        if hours_old < 6:
            score += 10
        elif hours_old < 24:
            score += 5

        if article.category == NewsCategory.REAL_ESTATE:
            score += 10
        elif article.category != NewsCategory.GENERAL:
            score += 5

        if abs(int(sentiment.get("sentiment_score", 0))) > 70:
            score += 10

        return max(0, min(100, score))

    @staticmethod
    async def detect_trends(db: AsyncSession, days: int = 7) -> list[dict[str, int | str]]:
        cached_trends = await cache.get_cached_analytics_trends(days)
        if cached_trends is not None:
            return cached_trends

        from_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(NewsArticle).where(
                and_(
                    NewsArticle.published_at >= from_date,
                    NewsArticle.is_published.is_(True),
                )
            )
        )
        articles = result.scalars().all()

        all_keywords: list[str] = []
        for article in articles:
            if article.keywords:
                all_keywords.extend(
                    AIService._sanitize_keywords(
                        article.keywords,
                        text=" ".join(
                            part
                            for part in [article.title, article.description or "", article.content or ""]
                            if part
                        ),
                        limit=12,
                    )
                )

        keyword_counts = Counter(all_keywords)
        trends = [
            {
                "keyword": keyword,
                "count": count,
                "trend_score": count * 10,
            }
            for keyword, count in keyword_counts.most_common(20)
            if count > 3
        ]
        await cache.cache_analytics_trends(days, trends, ttl=300)
        return trends

    @staticmethod
    async def get_category_distribution(
        db: AsyncSession,
        *,
        days: int = 7,
    ) -> list[dict[str, int | float | str]]:
        from_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(NewsArticle.category, func.count(NewsArticle.id))
            .where(
                and_(
                    NewsArticle.published_at >= from_date,
                    NewsArticle.is_published.is_(True),
                )
            )
            .group_by(NewsArticle.category)
        )
        rows = result.all()
        total = sum(count for _, count in rows) or 1
        return [
            {
                "category": category.value,
                "count": count,
                "share_percent": round((count / total) * 100, 2),
            }
            for category, count in sorted(rows, key=lambda item: item[1], reverse=True)
            if category is not None
        ]

    @staticmethod
    async def get_sentiment_timeline(
        db: AsyncSession,
        *,
        days: int = 7,
    ) -> list[dict[str, int | str]]:
        from_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(
                func.date(NewsArticle.published_at).label("bucket"),
                NewsArticle.sentiment,
                func.count(NewsArticle.id),
            )
            .where(
                and_(
                    NewsArticle.published_at >= from_date,
                    NewsArticle.is_published.is_(True),
                )
            )
            .group_by(func.date(NewsArticle.published_at), NewsArticle.sentiment)
            .order_by(func.date(NewsArticle.published_at).asc())
        )
        grouped: dict[str, dict[str, int]] = {}
        for bucket, sentiment, count in result.all():
            key = str(bucket)
            grouped.setdefault(key, {"positive": 0, "neutral": 0, "negative": 0})
            if sentiment is not None:
                grouped[key][sentiment.value] = count
        return [
            {
                "date": key,
                "positive": values["positive"],
                "neutral": values["neutral"],
                "negative": values["negative"],
                "total": values["positive"] + values["neutral"] + values["negative"],
            }
            for key, values in grouped.items()
        ]

    @staticmethod
    async def get_provider_distribution(
        db: AsyncSession,
        *,
        days: int = 7,
    ) -> list[dict[str, int | float | str]]:
        from_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(NewsArticle.primary_provider, func.count(NewsArticle.id))
            .where(
                and_(
                    NewsArticle.published_at >= from_date,
                    NewsArticle.is_published.is_(True),
                )
            )
            .group_by(NewsArticle.primary_provider)
            .order_by(func.count(NewsArticle.id).desc())
        )
        rows = result.all()
        total = sum(count for _, count in rows) or 1
        return [
            {
                "provider": (provider or "unknown"),
                "count": count,
                "share_percent": round((count / total) * 100, 2),
            }
            for provider, count in rows
        ]

    @staticmethod
    async def get_market_mood(
        db: AsyncSession,
        *,
        days: int = 7,
    ) -> dict[str, Any]:
        distribution = await AIService.get_sentiment_distribution(db, days=days)
        trends = await AIService.detect_trends(db, days=days)
        category_distribution = await AIService.get_category_distribution(db, days=days)

        mood_score = round(
            float(distribution["positive_percent"]) - float(distribution["negative_percent"]),
            2,
        )
        if mood_score >= 20:
            label = "Constructive"
        elif mood_score >= 5:
            label = "Measured optimism"
        elif mood_score <= -20:
            label = "Risk-off"
        elif mood_score <= -5:
            label = "Cautious"
        else:
            label = "Balanced"

        leading_categories = ", ".join(
            item["category"].replace("_", " ").title() for item in category_distribution[:2]
        ) or "general market coverage"
        leading_keywords = ", ".join(item["keyword"] for item in trends[:4]) or "no clear thematic concentration"
        summary = (
            f"{label} market mood with {distribution['positive_percent']}% positive coverage versus "
            f"{distribution['negative_percent']}% negative coverage. The strongest current narrative centers on "
            f"{leading_categories}, with momentum around {leading_keywords}."
        )
        return {
            "score": mood_score,
            "label": label,
            "summary": summary,
            "drivers": {
                "positive_percent": distribution["positive_percent"],
                "negative_percent": distribution["negative_percent"],
                "neutral_percent": distribution["neutral_percent"],
                "leading_categories": category_distribution[:3],
                "leading_keywords": trends[:6],
            },
        }

    @staticmethod
    async def get_sentiment_distribution(
        db: AsyncSession,
        category: NewsCategory | None = None,
        days: int = 7,
    ) -> dict[str, int | float]:
        category_key = category.value if category is not None else None
        cached_distribution = await cache.get_cached_analytics_sentiment(category_key, days)
        if cached_distribution is not None:
            return cached_distribution

        from_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = (
            select(NewsArticle.sentiment, func.count(NewsArticle.id).label("count"))
            .where(
                and_(
                    NewsArticle.published_at >= from_date,
                    NewsArticle.is_published.is_(True),
                )
            )
            .group_by(NewsArticle.sentiment)
        )

        if category is not None:
            query = query.where(NewsArticle.category == category)

        result = await db.execute(query)
        rows = result.all()

        distribution: dict[str, int | float] = {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "total": 0,
            "positive_percent": 0.0,
            "neutral_percent": 0.0,
            "negative_percent": 0.0,
        }

        for sentiment, count in rows:
            if sentiment is None:
                continue
            distribution[sentiment.value] = count
            distribution["total"] += count

        total = int(distribution["total"])
        if total > 0:
            for key in ("positive", "neutral", "negative"):
                distribution[f"{key}_percent"] = round((int(distribution[key]) / total) * 100, 2)

        await cache.cache_analytics_sentiment(category_key, days, distribution, ttl=300)
        return distribution

    @staticmethod
    async def get_recommendations(
        db: AsyncSession,
        user_preferences: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[NewsArticle]:
        del user_preferences

        result = await db.execute(
            select(NewsArticle)
            .where(NewsArticle.is_published.is_(True))
            .order_by(NewsArticle.relevance_score.desc(), NewsArticle.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_symbol_sentiment(
        db: AsyncSession,
        *,
        symbol: str,
        days: int = 30,
    ) -> dict[str, Any]:
        from_date = datetime.now(timezone.utc) - timedelta(days=days)
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
        symbol_lower = symbol.lower().replace(".du", "").replace(".ad", "")
        scores: list[float] = []
        article_count = 0
        for article in result.scalars().all():
            text = " ".join(part for part in [article.title, article.description or "", article.content or ""] if part).lower()
            if symbol_lower not in text:
                continue
            raw_score = float(article.sentiment_score or 0.0)
            scores.append(raw_score / 100 if abs(raw_score) > 1 else raw_score)
            article_count += 1
        average = mean(scores) if scores else 0.0
        return {
            "symbol": symbol,
            "days": days,
            "article_count": article_count,
            "average_sentiment": round(average, 3),
            "label": "positive" if average > 0.15 else "negative" if average < -0.15 else "neutral",
        }

    @staticmethod
    async def get_overall_sentiment(
        db: AsyncSession,
        *,
        days: int = 30,
    ) -> dict[str, Any]:
        distribution = await AIService.get_sentiment_distribution(db, days=days)
        mood = await AIService.get_market_mood(db, days=days)
        return {
            "days": days,
            "distribution": distribution,
            "mood": mood,
            "average_sentiment": round((distribution["positive_percent"] - distribution["negative_percent"]) / 100, 3),
        }
