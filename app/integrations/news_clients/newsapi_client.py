from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.integrations.base_client import BaseNewsClient

settings = get_settings()


class NewsAPIClient(BaseNewsClient):
    """NewsAPI.org search client."""

    def __init__(self) -> None:
        super().__init__(
            base_url="https://newsapi.org/v2",
            api_key=settings.NEWSAPI_KEY or None,
            use_bearer_auth=False,
        )

    async def search_news(
        self,
        query: str,
        *,
        max_age_hours: int = 24,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        if not self.api_key:
            return []
        from_date, to_date = self._get_date_range(max_age_hours)
        payload = await self.get(
            "/everything",
            params={
                "q": query,
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": min(max_results, 100),
                "apiKey": self.api_key,
            },
        )
        return [self._normalize_article(article) for article in payload.get("articles", [])]

    @staticmethod
    def _normalize_article(article: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "description": article.get("description", ""),
            "content": article.get("content", ""),
            "published_at": article.get("publishedAt"),
            "source": article.get("source", {}).get("name", "NewsAPI"),
            "author": article.get("author", ""),
            "image_url": article.get("urlToImage", ""),
            "provider": "newsapi",
        }
