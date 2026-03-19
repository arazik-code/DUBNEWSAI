from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.integrations.base_client import BaseNewsClient

settings = get_settings()


class CurrentsClient(BaseNewsClient):
    """Currents API client."""

    def __init__(self) -> None:
        super().__init__(
            base_url="https://api.currentsapi.services/v1",
            api_key=settings.CURRENTS_API_KEY or None,
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
        from_date, _ = self._get_date_range(max_age_hours)
        payload = await self.get(
            "/search",
            params={
                "keywords": query,
                "language": "en",
                "country": "AE",
                "start_date": from_date.strftime("%Y-%m-%d"),
                "apiKey": self.api_key,
            },
        )
        return [self._normalize_article(article) for article in payload.get("news", [])[:max_results]]

    @staticmethod
    def _normalize_article(article: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "description": article.get("description", ""),
            "content": article.get("description", ""),
            "published_at": article.get("published"),
            "source": article.get("author", "Currents"),
            "author": article.get("author", ""),
            "image_url": article.get("image", ""),
            "provider": "currents",
        }
