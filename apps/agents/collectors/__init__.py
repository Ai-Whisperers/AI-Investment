"""
Social media collectors for zero-budget data collection.

Implements collectors for Reddit, YouTube, TikTok, and 4chan following
the priority structure defined in the data sources mermaid diagram.
"""

from .reddit_collector import RedditCollector
from .youtube_collector import YouTubeCollector  
from .chan_collector import ChanCollector
from .tiktok_collector import TikTokCollector
from .base_collector import SocialCollector, CollectorOrchestrator

__all__ = [
    "RedditCollector",
    "YouTubeCollector", 
    "ChanCollector",
    "TikTokCollector", 
    "SocialCollector",
    "CollectorOrchestrator",
]