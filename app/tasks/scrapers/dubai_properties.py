from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class ScrapedInsight:
    title: str
    url: str
    excerpt: str | None
    source_name: str
    published_at: datetime
    image_url: str | None = None


class DubaiPropertyScraper:
    """Scrape publicly available property insight pages with light-touch rate limits."""

    HEADERS = {
        "User-Agent": "DUBNEWSAI/1.0 (+https://dubnewsai.com; Educational Research Bot)",
        "Accept": "text/html,application/xhtml+xml",
    }

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers=self.HEADERS,
        )

    async def close(self) -> None:
        await self.client.aclose()

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            parsed = date_parser.parse(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            return datetime.now(timezone.utc)

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        if not value:
            return None
        cleaned = " ".join(value.split()).strip()
        return cleaned or None

    @staticmethod
    def _build_insight_from_card(card: Any, source_name: str) -> ScrapedInsight | None:
        anchor = card.find("a", href=True)
        title_node = card.find(["h1", "h2", "h3", "h4"]) or anchor
        if anchor is None or title_node is None:
            return None

        title = DubaiPropertyScraper._clean_text(title_node.get_text(" ", strip=True))
        url = anchor["href"]
        excerpt_node = card.find("p")
        time_node = card.find("time")
        image = card.find("img")

        if not title or not url:
            return None

        return ScrapedInsight(
            title=title[:500],
            url=url,
            excerpt=DubaiPropertyScraper._clean_text(excerpt_node.get_text(" ", strip=True) if excerpt_node else None),
            source_name=source_name,
            published_at=DubaiPropertyScraper._parse_datetime(
                time_node.get("datetime") if time_node else None
            ),
            image_url=image.get("src") if image and image.get("src") else None,
        )

    async def _scrape_listing_page(
        self,
        url: str,
        source_name: str,
        selectors: list[str],
        limit: int = 10,
    ) -> list[ScrapedInsight]:
        response = await self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        cards: list[Any] = []
        for selector in selectors:
            cards.extend(soup.select(selector))

        insights: list[ScrapedInsight] = []
        seen_urls: set[str] = set()
        for card in cards:
            insight = self._build_insight_from_card(card, source_name)
            if insight is None or insight.url in seen_urls:
                continue
            seen_urls.add(insight.url)
            insights.append(insight)
            if len(insights) >= limit:
                break
        return insights

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def scrape_bayut_trends(self) -> list[ScrapedInsight]:
        return await self._scrape_listing_page(
            url="https://www.bayut.com/mybayut/tag/dubai-property-market/",
            source_name="Bayut",
            selectors=[
                "article",
                ".jeg_post",
                ".post-item",
            ],
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def scrape_propertyfinder_insights(self) -> list[ScrapedInsight]:
        return await self._scrape_listing_page(
            url="https://www.propertyfinder.ae/blog/category/market-insights/",
            source_name="Property Finder",
            selectors=[
                "article",
                ".post-card",
                ".jeg_post",
            ],
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def scrape_dubizzle_property(self) -> list[ScrapedInsight]:
        return await self._scrape_listing_page(
            url="https://blog.dubizzle.com/property/",
            source_name="Dubizzle Property",
            selectors=[
                "article",
                ".post",
                ".blog-post",
            ],
        )

    async def fetch_all(self) -> list[ScrapedInsight]:
        results = await asyncio.gather(
            self.scrape_bayut_trends(),
            self.scrape_propertyfinder_insights(),
            self.scrape_dubizzle_property(),
            return_exceptions=True,
        )

        insights: list[ScrapedInsight] = []
        for result in results:
            if isinstance(result, Exception):
                continue
            insights.extend(result)
        return insights
