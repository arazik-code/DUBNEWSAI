from app.integrations.news_clients.bing_client import BingNewsClient
from app.integrations.news_clients.currents_client import CurrentsClient
from app.integrations.news_clients.gnews_client import GNewsClient
from app.integrations.news_clients.newsapi_client import NewsAPIClient
from app.integrations.news_clients.newsdata_client import NewsDataClient
from app.integrations.news_clients.rss_parser import RSSFeedParser


class ClientFactory:
    """Shared client registry for multi-source news ingestion."""

    _clients: dict[str, object] | None = None

    @classmethod
    def get_clients(cls) -> dict[str, object]:
        if cls._clients is None:
            cls._clients = {
                "newsapi": NewsAPIClient(),
                "gnews": GNewsClient(),
                "currents": CurrentsClient(),
                "newsdata": NewsDataClient(),
                "bing_news": BingNewsClient(),
                "rss": RSSFeedParser(),
            }
        return cls._clients

    @classmethod
    async def close_all(cls) -> None:
        if cls._clients is None:
            return
        for client in cls._clients.values():
            close = getattr(client, "close", None)
            if close is not None:
                await close()
        cls._clients = None


__all__ = [
    "BingNewsClient",
    "ClientFactory",
    "CurrentsClient",
    "GNewsClient",
    "NewsAPIClient",
    "NewsDataClient",
    "RSSFeedParser",
]
