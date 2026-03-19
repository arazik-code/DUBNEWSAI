from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.integrations.base_client import BaseNewsClient

settings = get_settings()


class NewsDataClient(BaseNewsClient):
    """NewsData.io client."""

    def __init__(self) -> None:
        super().__init__(
            base_url="https://newsdata.io/api/1",
            api_key=settings.NEWSDATA_API_KEY or None,
            use_bearer_auth=False,
        )

    async def search_news(
        self,
        query: str,
        *,
        max_age_hours: int = 24,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        del max_age_hours
        if not self.api_key:
            return []
        payload = await self.get(
            "/news",
            params={
                "apikey": self.api_key,
                "q": query,
                "language": "en",
                "country": "ae",
            },
        )
        return [self._normalize_article(article) for article in payload.get("results", [])[:max_results]]

    @staticmethod
    def _normalize_article(article: dict[str, Any]) -> dict[str, Any]:
        creator = article.get("creator")
        if isinstance(creator, list):
            creator = creator[0] if creator else ""
        return {
            "title": article.get("title", ""),
            "url": article.get("link", ""),
            "description": article.get("description", ""),
            "content": article.get("content", ""),
            "published_at": article.get("pubDate"),
            "source": article.get("source_id", "NewsData"),
            "author": creator or "",
            "image_url": article.get("image_url", ""),
            "provider": "newsdata",
        }
