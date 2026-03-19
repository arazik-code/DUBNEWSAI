from datetime import datetime, timedelta, timezone

from loguru import logger

from app.config import get_settings
from app.integrations.base_client import BaseAPIClient

settings = get_settings()


class NewsAPIClient(BaseAPIClient):
    LOCATION_TERMS = ("dubai", "uae", "abu dhabi", "emirates")
    PROPERTY_TERMS = (
        "real estate",
        "property",
        "housing",
        "rental",
        "rent",
        "villa",
        "apartment",
        "mortgage",
        "off-plan",
        "developer",
    )

    def __init__(self) -> None:
        super().__init__(
            base_url="https://newsapi.org/v2",
            api_key=settings.NEWSAPI_KEY or None,
            use_bearer_auth=False,
        )

    @classmethod
    def _is_relevant_article(cls, article: dict) -> bool:
        headline_text = " ".join(
            str(article.get(field) or "")
            for field in ("title", "description")
        ).lower()
        body_text = f"{headline_text} {str(article.get('content') or '').lower()}"
        has_location = any(term in body_text for term in cls.LOCATION_TERMS)
        has_property_term = any(term in headline_text for term in cls.PROPERTY_TERMS)
        return has_location and has_property_term

    async def fetch_dubai_real_estate_news(
        self,
        days_back: int = 1,
        page_size: int = 100,
    ) -> list[dict]:
        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
        params = {
            "qInTitle": 'Dubai AND (property OR "real estate" OR housing OR villa OR apartment OR rental)',
            "language": "en",
            "sortBy": "publishedAt",
            "from": from_date,
            "pageSize": page_size,
            "apiKey": self.api_key,
        }

        try:
            response = await self.get("/everything", params=params)
            articles = response.get("articles", [])
            filtered_articles = [article for article in articles if self._is_relevant_article(article)]
            logger.info(
                "Fetched {} articles from NewsAPI, kept {} relevant articles",
                len(articles),
                len(filtered_articles),
            )
            return filtered_articles
        except Exception as exc:
            logger.error("Error fetching NewsAPI articles: {}", str(exc))
            return []

    async def fetch_by_category(self, category: str, country: str = "ae") -> list[dict]:
        params = {
            "country": country,
            "category": category,
            "pageSize": 100,
            "apiKey": self.api_key,
        }
        try:
            response = await self.get("/top-headlines", params=params)
            return response.get("articles", [])
        except Exception as exc:
            logger.error("Error fetching category news from NewsAPI: {}", str(exc))
            return []
