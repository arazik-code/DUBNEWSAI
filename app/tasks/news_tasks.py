import asyncio
from datetime import datetime, timezone

from celery import shared_task
from loguru import logger

from app.database import AsyncSessionLocal
from app.integrations.newsapi_client import NewsAPIClient
from app.integrations.rss_parser import RSSFeedParser
from app.models.news import NewsSource
from app.schemas.news import NewsArticleCreate, NewsArticleResponse
from app.services.alert_service import AlertService
from app.services.broadcast_service import BroadcastService
from app.services.news_service import NewsService


@shared_task(name="fetch_newsapi_articles")
def fetch_newsapi_articles() -> None:
    asyncio.run(_fetch_newsapi_articles())


async def _fetch_newsapi_articles() -> None:
    client = NewsAPIClient()
    async with AsyncSessionLocal() as db:
        try:
            raw_articles = await client.fetch_dubai_real_estate_news(days_back=7, page_size=25)
            articles_to_create: list[NewsArticleCreate] = []

            for raw_article in raw_articles:
                try:
                    published_raw = raw_article.get("publishedAt")
                    if not published_raw:
                        published_at = datetime.now(timezone.utc)
                    else:
                        published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))

                    category = await NewsService.categorize_article(raw_article)
                    articles_to_create.append(
                        NewsArticleCreate(
                            title=raw_article["title"][:500],
                            description=(raw_article.get("description") or "")[:5000] or None,
                            content=(raw_article.get("content") or "")[:50000] or None,
                            url=raw_article["url"],
                            source=NewsSource.NEWSAPI,
                            source_name=raw_article.get("source", {}).get("name"),
                            author=raw_article.get("author"),
                            category=category,
                            published_at=published_at,
                            image_url=raw_article.get("urlToImage"),
                        )
                    )
                except Exception as exc:
                    logger.error("Error processing NewsAPI article: {}", str(exc))

            created_articles = []
            skipped = 0
            for article_data in articles_to_create:
                created_article = await NewsService.create_article(db, article_data)
                if created_article is None:
                    skipped += 1
                    continue
                created_articles.append(created_article)

            for article in created_articles:
                await AlertService.check_keyword_alerts(db, article)
                await AlertService.check_sentiment_alerts(db, article)
                await AlertService.check_category_alerts(db, article)
                article_payload = NewsArticleResponse.model_validate(article).model_dump(mode="json")
                await BroadcastService.broadcast_new_article(article_payload)

            created = len(created_articles)
            logger.info("NewsAPI import finished: {} created, {} skipped", created, skipped)
        except Exception as exc:
            logger.error("Error in NewsAPI fetch task: {}", str(exc))
        finally:
            await client.close()


@shared_task(name="fetch_rss_feeds")
def fetch_rss_feeds() -> None:
    asyncio.run(_fetch_rss_feeds())


async def _fetch_rss_feeds() -> None:
    parser = RSSFeedParser()
    async with AsyncSessionLocal() as db:
        try:
            all_feeds = await parser.fetch_all_feeds()
            source_mapping = {
                "gulf_news_real_estate": NewsSource.RSS_GULF_NEWS,
                "the_national_property": NewsSource.RSS_THE_NATIONAL,
                "khaleej_times_real_estate": NewsSource.RSS_KHALEEJ_TIMES,
                "arabian_business": NewsSource.RSS_ARABIAN_BUSINESS,
            }

            total_created = 0
            total_skipped = 0

            for feed_name, articles in all_feeds.items():
                articles_to_create: list[NewsArticleCreate] = []
                for raw_article in articles:
                    try:
                        category = await NewsService.categorize_article(raw_article)
                        articles_to_create.append(
                            NewsArticleCreate(
                                title=raw_article["title"][:500],
                                description=(raw_article.get("description") or "")[:5000] or None,
                                content=None,
                                url=raw_article["url"],
                                source=source_mapping.get(feed_name, NewsSource.RSS_GULF_NEWS),
                                source_name=feed_name.replace("_", " ").title(),
                                author=raw_article.get("author"),
                                category=category,
                                published_at=raw_article["published_at"],
                                image_url=raw_article.get("image_url"),
                            )
                        )
                    except Exception as exc:
                        logger.error("Error processing RSS article: {}", str(exc))

                created_articles = []
                skipped = 0
                for article_data in articles_to_create:
                    created_article = await NewsService.create_article(db, article_data)
                    if created_article is None:
                        skipped += 1
                        continue
                    created_articles.append(created_article)

                for article in created_articles:
                    await AlertService.check_keyword_alerts(db, article)
                    await AlertService.check_sentiment_alerts(db, article)
                    await AlertService.check_category_alerts(db, article)
                    article_payload = NewsArticleResponse.model_validate(article).model_dump(mode="json")
                    await BroadcastService.broadcast_new_article(article_payload)

                created = len(created_articles)
                total_created += created
                total_skipped += skipped

            logger.info("RSS import finished: {} created, {} skipped", total_created, total_skipped)
        except Exception as exc:
            logger.error("Error in RSS fetch task: {}", str(exc))
        finally:
            await parser.close()


@shared_task(name="cleanup_old_articles")
def cleanup_old_articles() -> None:
    asyncio.run(_cleanup_old_articles())


async def _cleanup_old_articles() -> None:
    async with AsyncSessionLocal() as db:
        deleted = await NewsService.cleanup_old_articles(db, days=90)
        logger.info("Cleaned up {} old articles", deleted)
