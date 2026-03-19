from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx
from dateutil import parser as date_parser
from loguru import logger


class RSSFeedParser:
    RSS_FEEDS = {
        "gulf_news_real_estate": "https://gulfnews.com/business/property/rss",
        "the_national_property": "https://www.thenationalnews.com/business/property/rss/",
        "khaleej_times_real_estate": "https://www.khaleejtimes.com/real-estate/rss",
        "arabian_business": "https://www.arabianbusiness.com/industries/real-estate/rss",
    }

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
                )
            },
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def fetch_feed(self, feed_url: str) -> list[dict[str, Any]]:
        try:
            response = await self.client.get(feed_url)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            articles: list[dict[str, Any]] = []

            for entry in feed.entries:
                articles.append(
                    {
                        "title": entry.get("title", ""),
                        "description": entry.get("summary", entry.get("description", "")),
                        "url": entry.get("link", ""),
                        "published_at": self._parse_date(entry.get("published", entry.get("updated"))),
                        "author": entry.get("author", ""),
                        "image_url": self._extract_image(entry),
                    }
                )

            logger.info("Fetched {} RSS articles from {}", len(articles), feed_url)
            return articles
        except Exception as exc:
            logger.error("Error fetching RSS feed {}: {}", feed_url, str(exc))
            return []

    async def fetch_all_feeds(self) -> dict[str, list[dict[str, Any]]]:
        results: dict[str, list[dict[str, Any]]] = {}
        for feed_name, feed_url in self.RSS_FEEDS.items():
            results[feed_name] = await self.fetch_feed(feed_url)
        return results

    @staticmethod
    def _parse_date(date_str: str | None) -> datetime:
        if not date_str:
            return datetime.now(timezone.utc)

        try:
            parsed = date_parser.parse(date_str)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            return datetime.now(timezone.utc)

    @staticmethod
    def _extract_image(entry: dict[str, Any]) -> str | None:
        media_content = entry.get("media_content")
        if media_content:
            return media_content[0].get("url")

        media_thumbnail = entry.get("media_thumbnail")
        if media_thumbnail:
            return media_thumbnail[0].get("url")

        enclosures = entry.get("enclosures")
        if enclosures:
            for enclosure in enclosures:
                if "image" in enclosure.get("type", ""):
                    return enclosure.get("href")

        return None
