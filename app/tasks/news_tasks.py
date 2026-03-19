import asyncio

from celery import shared_task
from loguru import logger

from app.database import AsyncSessionLocal
from app.integrations.free_data_sources import FreeDataAggregator
from app.schemas.news import NewsArticleResponse
from app.services.alert_service import AlertService
from app.services.broadcast_service import BroadcastService
from app.services.news_service import NewsService


@shared_task(name="fetch_newsapi_articles")
def fetch_newsapi_articles() -> None:
    asyncio.run(_fetch_newsapi_articles())


async def _fetch_newsapi_articles() -> None:
    aggregator = FreeDataAggregator()
    async with AsyncSessionLocal() as db:
        try:
            articles_to_create = await aggregator.fetch_news_articles(
                include_api=True,
                include_rss=False,
                include_scraped=False,
            )

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
            logger.info("API news import finished: {} created, {} skipped", created, skipped)
        except Exception as exc:
            logger.error("Error in API news fetch task: {}", str(exc))
        finally:
            await aggregator.close()


@shared_task(name="fetch_rss_feeds")
def fetch_rss_feeds() -> None:
    asyncio.run(_fetch_rss_feeds())


async def _fetch_rss_feeds() -> None:
    aggregator = FreeDataAggregator()
    async with AsyncSessionLocal() as db:
        try:
            articles_to_create = await aggregator.fetch_news_articles(
                include_api=False,
                include_rss=True,
                include_scraped=True,
            )

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

            logger.info("RSS and scraper import finished: {} created, {} skipped", len(created_articles), skipped)
        except Exception as exc:
            logger.error("Error in RSS fetch task: {}", str(exc))
        finally:
            await aggregator.close()


@shared_task(name="cleanup_old_articles")
def cleanup_old_articles() -> None:
    asyncio.run(_cleanup_old_articles())


async def _cleanup_old_articles() -> None:
    async with AsyncSessionLocal() as db:
        deleted = await NewsService.cleanup_old_articles(db, days=90)
        logger.info("Cleaned up {} old articles", deleted)
