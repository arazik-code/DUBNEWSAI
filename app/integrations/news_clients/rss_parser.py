from __future__ import annotations

from datetime import datetime, timedelta, timezone
from time import struct_time
from typing import Any

import feedparser
from dateutil import parser as date_parser

from app.integrations.base_client import BaseNewsClient


class RSSFeedParser(BaseNewsClient):
    """RSS/Atom parser exposed behind the news-client contract."""

    def __init__(self) -> None:
        super().__init__(base_url="rss://dubnewsai", api_key=None)

    async def search_news(
        self,
        query: str,
        *,
        max_age_hours: int = 24,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        del query, max_age_hours, max_results
        return []

    async def parse_feed(
        self,
        feed_url: str,
        *,
        max_age_hours: int = 24,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        response = await self.client.get(feed_url)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        articles: list[dict[str, Any]] = []
        for entry in feed.entries:
            published_at = self._parse_entry_date(entry)
            if published_at and published_at < cutoff:
                continue
            articles.append(self._normalize_entry(entry, feed.feed))
            if len(articles) >= max_results:
                break
        return articles

    @staticmethod
    def _parse_entry_date(entry: dict[str, Any]) -> datetime | None:
        for field in ("published_parsed", "updated_parsed", "created_parsed"):
            value = entry.get(field)
            if isinstance(value, struct_time):
                return datetime(*value[:6], tzinfo=timezone.utc)

        for field in ("published", "updated", "created"):
            value = entry.get(field)
            if not value:
                continue
            try:
                parsed = date_parser.parse(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed
            except Exception:
                continue
        return None

    @staticmethod
    def _normalize_entry(entry: dict[str, Any], feed_info: dict[str, Any]) -> dict[str, Any]:
        image_url = ""
        media_content = entry.get("media_content")
        if media_content:
            image_url = media_content[0].get("url", "")
        elif entry.get("media_thumbnail"):
            image_url = entry["media_thumbnail"][0].get("url", "")
        elif entry.get("enclosures"):
            for enclosure in entry["enclosures"]:
                if "image" in enclosure.get("type", ""):
                    image_url = enclosure.get("href", "")
                    break

        content = ""
        if entry.get("content"):
            content = entry["content"][0].get("value", "")
        elif entry.get("summary"):
            content = entry.get("summary", "")

        return {
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "description": entry.get("summary", ""),
            "content": content,
            "published_at": RSSFeedParser._parse_entry_date(entry),
            "source": feed_info.get("title", "RSS Feed"),
            "author": entry.get("author", ""),
            "image_url": image_url,
            "provider": "rss",
        }
