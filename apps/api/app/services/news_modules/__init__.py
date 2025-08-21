"""
News service module for handling news data and sentiment analysis.
"""

from .entity_extractor import EntityExtractor, ExtractedEntity
from .news_aggregator import NewsAggregator
from .news_processor import NewsProcessor
from .sentiment_analyzer import SentimentAnalyzer

__all__ = [
    'SentimentAnalyzer',
    'EntityExtractor',
    'ExtractedEntity',
    'NewsAggregator',
    'NewsProcessor'
]
