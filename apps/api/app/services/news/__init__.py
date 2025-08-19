"""
News service module for handling news data and sentiment analysis.
"""

from .sentiment_analyzer import SentimentAnalyzer
from .entity_extractor import EntityExtractor, ExtractedEntity
from .news_aggregator import NewsAggregator
from .news_processor import NewsProcessor

__all__ = [
    'SentimentAnalyzer',
    'EntityExtractor',
    'ExtractedEntity',
    'NewsAggregator',
    'NewsProcessor'
]