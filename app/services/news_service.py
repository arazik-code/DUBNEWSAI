import hashlib
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.cache import cache
from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.core.metrics import articles_processed
from app.integrations.article_content_extractor import ArticleContentExtractor
from app.models.news import NewsArticle, NewsCategory, NewsSentiment, NewsSource, NewsTag
from app.schemas.news import NewsArticleCreate, NewsArticleResponse, NewsFilterParams, NewsListResponse
from app.services.ai_service import AIService
from app.utils.helpers import slugify

settings = get_settings()


class NewsService:
    @staticmethod
    def generate_url_hash(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    @staticmethod
    def _content_needs_enrichment(content: str | None, description: str | None = None) -> bool:
        normalized_content = (content or "").strip()
        normalized_description = (description or "").strip()
        if not normalized_content:
            return True
        if "[+" in normalized_content or normalized_content.endswith("..."):
            return True
        if normalized_description and normalized_content == normalized_description:
            return True
        return len(normalized_content) < settings.ARTICLE_MIN_CONTENT_LENGTH

    @staticmethod
    def _extract_keywords(text: str, limit: int = 8) -> list[str]:
        words = re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", text.lower())
        stop_words = {
            "about",
            "after",
            "before",
            "dubai",
            "their",
            "there",
            "these",
            "those",
            "estate",
            "real",
            "market",
            "property",
            "with",
            "from",
            "that",
            "this",
            "have",
            "will",
            "into",
            "would",
            "could",
            "should",
            "them",
            "they",
        }
        counts = Counter(word for word in words if word not in stop_words)
        return [word for word, _ in counts.most_common(limit)]

    @staticmethod
    def _extract_entities(text: str) -> dict[str, list[str]]:
        entity_patterns = {
            "locations": ["dubai", "abu dhabi", "uae", "emirates"],
            "organizations": ["emaar", "damac", "nakheel", "aldar", "dubai land department", "rera"],
        }
        lowered = text.lower()
        entities: dict[str, list[str]] = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "money": [],
            "dates": [],
            "other": [],
        }
        for label, values in entity_patterns.items():
            for value in values:
                if value in lowered:
                    entities[label].append(value.title())
        return entities

    @staticmethod
    def _analyze_sentiment(text: str) -> tuple[NewsSentiment, int]:
        positive_terms = {"growth", "surge", "record", "strong", "increase", "boom", "demand"}
        negative_terms = {"decline", "drop", "risk", "fall", "slowdown", "concern"}
        lowered_words = set(re.findall(r"[a-zA-Z]+", text.lower()))
        positive_score = len(lowered_words & positive_terms)
        negative_score = len(lowered_words & negative_terms)
        score = max(-100, min(100, (positive_score - negative_score) * 20))
        if score > 10:
            return NewsSentiment.POSITIVE, score
        if score < -10:
            return NewsSentiment.NEGATIVE, score
        return NewsSentiment.NEUTRAL, score

    @staticmethod
    def _calculate_relevance_score(text: str, category: NewsCategory, published_at: datetime) -> int:
        boosted_terms = ["dubai", "real estate", "property", "rental", "investment", "development"]
        lowered = text.lower()
        keyword_hits = sum(1 for term in boosted_terms if term in lowered)
        category_bonus = 20 if category == NewsCategory.REAL_ESTATE else 10 if category != NewsCategory.GENERAL else 0
        age_hours = max(0, int((datetime.now(timezone.utc) - published_at).total_seconds() // 3600))
        recency_bonus = max(0, 30 - age_hours)
        return min(100, keyword_hits * 10 + category_bonus + recency_bonus)

    @staticmethod
    async def _attach_tags(db: AsyncSession, article: NewsArticle, tag_names: list[str]) -> None:
        normalized_names = []
        seen: set[str] = set()
        for tag_name in tag_names:
            normalized = tag_name.strip().lower()
            if normalized and normalized not in seen:
                normalized_names.append(normalized)
                seen.add(normalized)

        if not normalized_names:
            return

        result = await db.execute(select(NewsTag).where(NewsTag.name.in_(normalized_names)))
        existing_tags = {tag.name: tag for tag in result.scalars().all()}

        for tag_name in normalized_names:
            tag = existing_tags.get(tag_name)
            if tag is None:
                tag = NewsTag(name=tag_name, slug=slugify(tag_name), count=0)
                db.add(tag)
                await db.flush()
                existing_tags[tag_name] = tag

            article.tags.append(tag)
            tag.count += 1

    @staticmethod
    async def create_article(db: AsyncSession, article_data: NewsArticleCreate) -> NewsArticle | None:
        article_url = str(article_data.url)
        url_hash = NewsService.generate_url_hash(article_url)

        existing_result = await db.execute(
            select(NewsArticle).where(
                or_(NewsArticle.url_hash == url_hash, NewsArticle.url == article_url)
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            logger.debug("Skipping duplicate article for {}", article_url)
            return None

        published_at = article_data.published_at
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        article = NewsArticle(
            title=article_data.title,
            description=article_data.description,
            content=article_data.content,
            url=article_url,
            url_hash=url_hash,
            source=article_data.source,
            source_name=article_data.source_name,
            author=article_data.author,
            category=article_data.category,
            sentiment=NewsSentiment.NEUTRAL,
            sentiment_score=0,
            keywords=None,
            entities=None,
            published_at=published_at,
            relevance_score=0,
            image_url=str(article_data.image_url) if article_data.image_url else None,
            video_url=str(article_data.video_url) if article_data.video_url else None,
            tags=[],
        )

        analysis = await AIService.analyze_article(article)
        article.sentiment = NewsSentiment(analysis["sentiment"])
        article.sentiment_score = analysis["sentiment_score"]
        article.keywords = analysis["keywords"] or None
        article.entities = analysis["entities"] or None
        article.relevance_score = analysis["relevance_score"]

        db.add(article)
        await db.flush()
        await NewsService._attach_tags(db, article, article.keywords or [])
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            logger.debug("Skipping duplicate article for {}", article_url)
            return None
        await db.refresh(article)
        await NewsService.invalidate_article_cache(article.id)
        articles_processed.inc()
        logger.info("Created article {}", article.title)
        return article

    @staticmethod
    async def enrich_article_content(
        db: AsyncSession,
        article: NewsArticle,
        *,
        force: bool = False,
    ) -> NewsArticle:
        if not force and not NewsService._content_needs_enrichment(article.content, article.description):
            return article

        extractor = ArticleContentExtractor()
        try:
            extracted = await extractor.extract(article.url)
        finally:
            await extractor.close()

        if extracted is None:
            return article

        updated = False
        if extracted.content and (
            force
            or NewsService._content_needs_enrichment(article.content, article.description)
            or len(extracted.content) > len((article.content or "").strip())
        ):
            article.content = extracted.content
            updated = True

        if extracted.description and (
            not article.description or len(extracted.description) > len(article.description)
        ):
            article.description = extracted.description
            updated = True

        if extracted.image_url and not article.image_url:
            article.image_url = extracted.image_url
            updated = True

        if not updated:
            return article

        analysis = await AIService.analyze_article(article)
        article.sentiment = NewsSentiment(analysis["sentiment"])
        article.sentiment_score = analysis["sentiment_score"]
        article.keywords = analysis["keywords"] or None
        article.entities = analysis["entities"] or None
        article.relevance_score = analysis["relevance_score"]

        await db.commit()
        await db.refresh(article)
        await NewsService.invalidate_article_cache(article.id)
        return article

    @staticmethod
    async def bulk_create_articles(
        db: AsyncSession,
        articles_data: list[NewsArticleCreate],
    ) -> tuple[int, int]:
        created = 0
        skipped = 0
        for article_data in articles_data:
            result = await NewsService.create_article(db, article_data)
            if result is None:
                skipped += 1
            else:
                created += 1
        logger.info("Bulk article import complete: {} created, {} skipped", created, skipped)
        return created, skipped

    @staticmethod
    async def get_articles(db: AsyncSession, filters: NewsFilterParams) -> NewsListResponse:
        cached_articles = await cache.get_cached_news_list(filters)
        if cached_articles is not None:
            return NewsListResponse.model_validate(cached_articles)

        query = (
            select(NewsArticle)
            .options(selectinload(NewsArticle.tags))
            .where(NewsArticle.is_published.is_(True))
        )

        if filters.category:
            query = query.where(NewsArticle.category == filters.category)
        if filters.source:
            query = query.where(NewsArticle.source == filters.source)
        if filters.sentiment:
            query = query.where(NewsArticle.sentiment == filters.sentiment)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    NewsArticle.title.ilike(search_term),
                    NewsArticle.description.ilike(search_term),
                    NewsArticle.content.ilike(search_term),
                )
            )
        if filters.from_date:
            query = query.where(NewsArticle.published_at >= filters.from_date)
        if filters.to_date:
            query = query.where(NewsArticle.published_at <= filters.to_date)

        total_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(total_query)).scalar_one()

        query = query.order_by(NewsArticle.published_at.desc()).offset(
            (filters.page - 1) * filters.page_size
        ).limit(filters.page_size)

        articles_result = await db.execute(query)
        articles = articles_result.scalars().unique().all()
        response = NewsListResponse(
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            articles=[NewsArticleResponse.model_validate(article) for article in articles],
        )
        ttl = 300
        if filters.from_date and filters.from_date < (datetime.now(timezone.utc) - timedelta(days=1)):
            ttl = 3600
        await cache.cache_news_list(filters, response.model_dump(mode="json"), ttl=ttl)
        return response

    @staticmethod
    async def get_article_by_id(db: AsyncSession, article_id: int) -> NewsArticle | dict:
        cached_article = await cache.get_cached_news_detail(article_id)
        if cached_article is not None:
            result = await db.execute(
                select(NewsArticle)
                .options(selectinload(NewsArticle.tags))
                .where(NewsArticle.id == article_id)
            )
            article = result.scalar_one_or_none()
            if article is not None:
                if NewsService._content_needs_enrichment(article.content, article.description):
                    article = await NewsService.enrich_article_content(db, article)
                article.view_count += 1
                await db.commit()
                await db.refresh(article)
                article_payload = NewsArticleResponse.model_validate(article).model_dump(mode="json")
                await cache.cache_news_detail(article_id, article_payload, ttl=600)
                return article_payload
            return cached_article

        result = await db.execute(
            select(NewsArticle)
            .options(selectinload(NewsArticle.tags))
            .where(NewsArticle.id == article_id)
        )
        article = result.scalar_one_or_none()
        if article is None:
            raise ResourceNotFoundError("Article not found")

        if NewsService._content_needs_enrichment(article.content, article.description):
            article = await NewsService.enrich_article_content(db, article)

        article.view_count += 1
        await db.commit()
        await db.refresh(article)
        await cache.cache_news_detail(
            article_id,
            NewsArticleResponse.model_validate(article).model_dump(mode="json"),
            ttl=600,
        )
        return article

    @staticmethod
    async def get_featured_articles(db: AsyncSession, limit: int = 5) -> list[NewsArticle]:
        if limit == 5:
            cached_featured = await cache.get_cached_featured_news()
            if cached_featured is not None:
                return [NewsArticleResponse.model_validate(article) for article in cached_featured]

        result = await db.execute(
            select(NewsArticle)
            .options(selectinload(NewsArticle.tags))
            .where(NewsArticle.is_featured.is_(True), NewsArticle.is_published.is_(True))
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        )
        articles = list(result.scalars().unique().all())
        if limit == 5:
            await cache.cache_featured_news(
                [NewsArticleResponse.model_validate(article).model_dump(mode="json") for article in articles],
                ttl=300,
            )
        return articles

    @staticmethod
    async def get_trending_articles(db: AsyncSession, limit: int = 10) -> list[NewsArticle]:
        timeframe = "today"
        if limit == 10:
            cached_trending = await cache.get_cached_trending_news(timeframe)
            if cached_trending is not None:
                return [NewsArticleResponse.model_validate(article) for article in cached_trending]

        since = datetime.now(timezone.utc) - timedelta(days=1)
        result = await db.execute(
            select(NewsArticle)
            .options(selectinload(NewsArticle.tags))
            .where(NewsArticle.published_at >= since, NewsArticle.is_published.is_(True))
            .order_by(NewsArticle.view_count.desc(), NewsArticle.published_at.desc())
            .limit(limit)
        )
        articles = list(result.scalars().unique().all())
        if limit == 10:
            await cache.cache_trending_news(
                timeframe,
                [NewsArticleResponse.model_validate(article).model_dump(mode="json") for article in articles],
                ttl=300,
            )
        return articles

    @staticmethod
    async def categorize_article(article_data: dict) -> NewsCategory:
        title_lower = article_data.get("title", "").lower()
        description_lower = article_data.get("description", "").lower()
        text = f"{title_lower} {description_lower}"

        category_keywords = {
            NewsCategory.REAL_ESTATE: ["property", "real estate", "housing", "apartment", "villa", "rent", "sale"],
            NewsCategory.MARKET: ["market", "stock", "trading", "investment", "shares"],
            NewsCategory.ECONOMY: ["economy", "gdp", "economic", "inflation", "growth"],
            NewsCategory.REGULATION: ["regulation", "law", "legal", "policy", "visa", "government"],
            NewsCategory.DEVELOPMENT: ["development", "construction", "project", "build"],
            NewsCategory.INFRASTRUCTURE: ["infrastructure", "metro", "road", "transport", "airport"],
        }

        scores = {
            category: sum(1 for keyword in keywords if keyword in text)
            for category, keywords in category_keywords.items()
        }
        best_category = max(scores, key=scores.get, default=NewsCategory.GENERAL)
        return best_category if scores.get(best_category, 0) > 0 else NewsCategory.GENERAL

    @staticmethod
    async def analyze_and_update_article(db: AsyncSession, article_id: int) -> NewsArticle | None:
        result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
        article = result.scalar_one_or_none()
        if article is None:
            return None

        analysis = await AIService.analyze_article(article)
        article.sentiment = NewsSentiment(analysis["sentiment"])
        article.sentiment_score = analysis["sentiment_score"]
        article.keywords = analysis["keywords"] or None
        article.entities = analysis["entities"] or None
        article.relevance_score = analysis["relevance_score"]

        await db.commit()
        await db.refresh(article)
        await NewsService.invalidate_article_cache(article_id)
        articles_processed.inc()
        logger.info("AI analysis completed for article {}", article_id)
        return article

    @staticmethod
    async def cleanup_old_articles(db: AsyncSession, days: int = 90) -> int:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(delete(NewsArticle).where(NewsArticle.published_at < cutoff_date))
        await db.commit()
        await cache.delete_pattern("news:list:*")
        await cache.delete(cache.NEWS_FEATURED)
        await cache.delete_pattern("news:trending:*")
        await cache.delete_pattern("analytics:*")
        return result.rowcount or 0

    @staticmethod
    async def invalidate_article_cache(article_id: int) -> None:
        await cache.delete(cache.NEWS_DETAIL.format(article_id=article_id))
        await cache.delete_pattern("news:list:*")
        await cache.delete(cache.NEWS_FEATURED)
        await cache.delete_pattern("news:trending:*")
        await cache.delete_pattern("analytics:*")
