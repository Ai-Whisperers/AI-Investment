"""
AI Agents system for social signal processing and extreme alpha generation.

This module implements the zero-budget architecture for processing millions of 
social media posts to generate >30% annual returns through information asymmetry.
"""

__version__ = "1.0.0"
__author__ = "Waardhaven AutoIndex Team"

from .collectors import RedditCollector, YouTubeCollector, ChanCollector, TikTokCollector
from .processors import ClaudeMCPProcessor, SignalExtractor, ContextManager
from .backtesting import BacktestEngine, HistoricalDataLoader, MetricsCalculator

__all__ = [
    "RedditCollector",
    "YouTubeCollector", 
    "ChanCollector",
    "TikTokCollector",
    "ClaudeMCPProcessor",
    "SignalExtractor",
    "ContextManager",
    "BacktestEngine",
    "HistoricalDataLoader",
    "MetricsCalculator",
]