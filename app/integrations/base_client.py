from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import APIClientError


class BaseAPIClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        timeout: int = 30,
        use_bearer_auth: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_headers = dict(default_headers or {})
        self.timeout = timeout
        self.use_bearer_auth = use_bearer_auth
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self.client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_headers = dict(self.default_headers)
        request_headers.update(dict(headers or {}))
        if self.api_key and self.use_bearer_auth and "Authorization" not in request_headers:
            request_headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                headers=request_headers,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("HTTP error from external API: {} {}", exc.response.status_code, exc.response.text)
            raise APIClientError(f"API request failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("Request error from external API: {}", str(exc))
            raise APIClientError(f"Request failed: {str(exc)}") from exc

    async def get(
        self,
        endpoint: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self._request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        json_data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self._request("POST", endpoint, headers=headers, json_data=json_data)


class BaseNewsClient(BaseAPIClient, ABC):
    """Abstract base class for search-oriented news providers."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        timeout: int = 30,
        use_bearer_auth: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            default_headers=default_headers,
            timeout=timeout,
            use_bearer_auth=use_bearer_auth,
        )

    def _get_date_range(self, max_age_hours: int) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        from_date = now - timedelta(hours=max_age_hours)
        return from_date, now

    @abstractmethod
    async def search_news(
        self,
        query: str,
        *,
        max_age_hours: int = 24,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
