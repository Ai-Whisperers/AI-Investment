"""
MarketAux API client.
Handles low-level API communication with MarketAux news service.
"""

import logging
from typing import Any

import requests

from ....core.config import settings
from ...base import APIError, RateLimitError

logger = logging.getLogger(__name__)


class MarketAuxAPIClient:
    """
    Low-level MarketAux API client.
    Handles direct API communication.
    """

    BASE_URL = "https://api.marketaux.com/v1"

    def __init__(self, api_key: str | None = None):
        """
        Initialize API client.

        Args:
            api_key: MarketAux API key
        """
        self.api_key = api_key or settings.MARKETAUX_API_KEY

        if not self.api_key:
            raise ValueError("MarketAux API key not configured")

    def make_request(
        self,
        endpoint: str,
        params: dict | None = None,
        method: str = "GET"
    ) -> dict[str, Any]:
        """
        Make API request to MarketAux.

        Args:
            endpoint: API endpoint
            params: Request parameters
            method: HTTP method

        Returns:
            API response data
        """
        if params is None:
            params = {}

        # Add API key
        params["api_token"] = self.api_key

        url = f"{self.BASE_URL}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=30)
            else:
                response = requests.post(url, json=params, timeout=30)

            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise RateLimitError(
                    "MarketAux rate limit exceeded",
                    retry_after=int(retry_after)
                )

            # Check for errors
            if response.status_code != 200:
                raise APIError(
                    f"MarketAux API error: {response.text}",
                    status_code=response.status_code,
                )

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(f"Failed to connect to MarketAux: {e}")

    def search_news(self, params: dict) -> dict[str, Any]:
        """
        Search for news articles.

        Args:
            params: Search parameters

        Returns:
            API response with articles
        """
        return self.make_request("/news/all", params)

    def get_article(self, article_id: str) -> dict[str, Any] | None:
        """
        Get specific article by ID.

        Args:
            article_id: Article UUID

        Returns:
            Article data or None
        """
        try:
            response = self.make_request(f"/news/{article_id}")
            return response.get("data")
        except APIError:
            return None

    def get_trending_news(self, limit: int = 10) -> dict[str, Any]:
        """
        Get trending news articles.

        Args:
            limit: Number of articles to fetch

        Returns:
            Trending articles response
        """
        params = {"limit": limit, "sort": "trending"}
        return self.make_request("/news/all", params)

    def get_sentiment_analysis(self, text: str) -> dict | None:
        """
        Get sentiment analysis for text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result
        """
        try:
            params = {"text": text}
            response = self.make_request("/sentiment", params, method="POST")
            return response.get("data")
        except APIError:
            return None

    def health_check(self) -> bool:
        """
        Check API health.

        Returns:
            True if API is healthy
        """
        try:
            response = self.make_request("/news/all", {"limit": 1})
            return bool(response and "data" in response)
        except Exception:
            return False
