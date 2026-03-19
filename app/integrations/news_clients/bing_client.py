from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.integrations.base_client import BaseNewsClient

settings = get_settings()


class BingNewsClient(BaseNewsClient):
    """Bing News Search API client."""

    def __init__(self) -> None:
        super().__init__(
            base_url="https://api.bing.microsoft.com/v7.0/news",
            api_key=settings.BING_NEWS_API_KEY or None,
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
        payload = await self.get(
            "/search",
            params={
                "q": query,
                "mkt": "en-AE",
                "count": min(max_results, 100),
                "freshness": "Day" if max_age_hours <= 24 else "Week",
            },
            headers={"Ocp-Apim-Subscription-Key": self.api_key},
        )
        return [self._normalize_article(article) for article in payload.get("value", [])]

    @staticmethod
    def _normalize_article(article: dict[str, Any]) -> dict[str, Any]:
        image_url = ""
        if article.get("image"):
            image_url = article["image"].get("thumbnail", {}).get("contentUrl", "")
        return {
            "title": article.get("name", ""),
            "url": article.get("url", ""),
            "description": article.get("description", ""),
            "content": article.get("description", ""),
            "published_at": article.get("datePublished"),
            "source": article.get("provider", [{}])[0].get("name", "Bing News"),
            "author": None,
            "image_url": image_url,
            "provider": "bing_news",
        }
