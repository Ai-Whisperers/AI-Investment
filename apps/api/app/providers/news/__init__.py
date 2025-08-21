"""
News providers module.
"""

from .interface import (
    NewsArticle,
    NewsEntity,
    NewsProvider,
    NewsSearchParams,
    NewsSentiment,
    SentimentLabel,
)
from .marketaux import MarketauxProvider

__all__ = [
    "NewsProvider",
    "NewsArticle",
    "NewsSentiment",
    "NewsEntity",
    "NewsSearchParams",
    "SentimentLabel",
    "MarketauxProvider",
]
