"""
YouTube Collector
Extracts investment signals from YouTube videos and comments
Uses YouTube Data API v3 (10,000 units/day free quota)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class YouTubeSignal:
    """Signal extracted from YouTube content."""
    video_id: str
    title: str
    channel: str
    views: int
    likes: int
    comments: int
    published_at: datetime
    tickers: List[str]
    sentiment: float
    signal_strength: float
    key_points: List[str]
    confidence: float
    

class YouTubeCollector:
    """
    Collects investment signals from YouTube videos.
    Focuses on finance channels and analyzes transcripts.
    """
    
    # High-value YouTube channels for different strategies
    CHANNEL_TARGETS = {
        "institutional_grade": [
            "Bloomberg Television",
            "Yahoo Finance",
            "CNBC Television",
            "Financial Times"
        ],
        "retail_influencers": [
            "MeetKevin",
            "Andrei Jikh",
            "Graham Stephan",
            "Jeremy Financial Education"
        ],
        "technical_analysis": [
            "The Chart Guys",
            "Rayner Teo",
            "The Trading Channel"
        ],
        "deep_research": [
            "The Plain Bagel",
            "Ben Felix",
            "The Swedish Investor",
            "New Money"
        ],
        "momentum_traders": [
            "ZipTrader",
            "Stock Moe",
            "Traveling Trader"
        ]
    }
    
    # API quota management (10,000 units/day)
    QUOTA_COSTS = {
        "search": 100,  # Search request
        "video_details": 1,  # Video metadata
        "comments": 1,  # Comment threads
        "captions": 200,  # Transcript download
        "channel": 1  # Channel info
    }
    
    def __init__(self, api_key: str = None):
        """Initialize YouTube collector."""
        self.api_key = api_key
        self.daily_quota = 10000
        self.quota_used = 0
        self.quota_reset_time = datetime.now() + timedelta(days=1)
        
    async def search_investment_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = "relevance",
        published_after: Optional[datetime] = None
    ) -> List[YouTubeSignal]:
        """
        Search for investment-related videos.
        Optimizes API quota usage.
        """
        signals = []
        
        # Check quota
        if not self._check_quota(self.QUOTA_COSTS["search"]):
            logger.warning("YouTube API quota exceeded")
            return signals
        
        try:
            # Search for videos (simplified - would use actual API)
            videos = await self._search_videos(query, max_results, order, published_after)
            
            for video in videos:
                # Only analyze high-engagement videos
                if video["views"] > 10000 or video["channel"] in self._get_all_channels():
                    signal = await self._analyze_video(video)
                    if signal and signal.confidence > 0.6:
                        signals.append(signal)
            
            logger.info(f"Found {len(signals)} signals from YouTube search: {query}")
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            
        return signals
    
    def _check_quota(self, cost: int) -> bool:
        """Check if we have enough quota remaining."""
        # Reset quota if new day
        if datetime.now() > self.quota_reset_time:
            self.quota_used = 0
            self.quota_reset_time = datetime.now() + timedelta(days=1)
            
        if self.quota_used + cost > self.daily_quota:
            return False
            
        self.quota_used += cost
        return True
    
    def _get_all_channels(self) -> List[str]:
        """Get all tracked channels."""
        all_channels = []
        for channels in self.CHANNEL_TARGETS.values():
            all_channels.extend(channels)
        return all_channels
    
    async def _search_videos(
        self,
        query: str,
        max_results: int,
        order: str,
        published_after: Optional[datetime]
    ) -> List[Dict]:
        """Search YouTube for videos (placeholder)."""
        # Simulated search results
        return [
            {
                "video_id": f"vid_{i}",
                "title": f"Why {query} Stock Will 10X in 2025",
                "channel": "Stock Moe",
                "views": 50000 - i * 5000,
                "likes": 2000 - i * 200,
                "comments": 500 - i * 50,
                "published_at": datetime.now() - timedelta(days=i),
                "description": f"Deep analysis of {query} fundamentals and catalysts"
            }
            for i in range(min(max_results, 3))
        ]
    
    async def _analyze_video(self, video: Dict) -> Optional[YouTubeSignal]:
        """
        Analyze video for investment signals.
        Extracts tickers, sentiment, and key points.
        """
        # Extract tickers from title and description
        text = video["title"] + " " + video.get("description", "")
        tickers = self._extract_tickers(text)
        
        if not tickers:
            return None
        
        # Calculate signal strength based on engagement
        signal_strength = self._calculate_signal_strength(video)
        
        # Extract key points (would analyze transcript in production)
        key_points = self._extract_key_points(video)
        
        # Calculate confidence
        confidence = self._calculate_confidence(video, signal_strength)
        
        return YouTubeSignal(
            video_id=video["video_id"],
            title=video["title"],
            channel=video["channel"],
            views=video["views"],
            likes=video["likes"],
            comments=video["comments"],
            published_at=video["published_at"],
            tickers=tickers,
            sentiment=0.7,  # Would analyze transcript
            signal_strength=signal_strength,
            key_points=key_points,
            confidence=confidence
        )
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text."""
        # Common tickers (would use comprehensive list)
        common_tickers = {
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA",
            "AMD", "INTC", "NFLX", "DIS", "PYPL", "SQ", "ROKU", "PLTR"
        }
        
        pattern = r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{2,5})(?:\s|$|\.|\,)'
        matches = re.findall(pattern, text)
        
        tickers = []
        for match in matches:
            ticker = match[0] or match[1]
            if ticker in common_tickers:
                tickers.append(ticker)
                
        return list(set(tickers))
    
    def _calculate_signal_strength(self, video: Dict) -> float:
        """Calculate signal strength based on engagement metrics."""
        views = video.get("views", 0)
        likes = video.get("likes", 0)
        comments = video.get("comments", 0)
        
        # Engagement rate
        if views > 0:
            engagement_rate = (likes + comments) / views
        else:
            engagement_rate = 0
            
        # Normalize signal strength
        if views > 100000 and engagement_rate > 0.05:
            return 0.9
        elif views > 50000 and engagement_rate > 0.03:
            return 0.7
        elif views > 10000 and engagement_rate > 0.02:
            return 0.5
        else:
            return 0.3
    
    def _extract_key_points(self, video: Dict) -> List[str]:
        """Extract key investment points from video."""
        # Would analyze transcript in production
        return [
            "Strong Q4 earnings expected",
            "New product launch catalyst",
            "Institutional buying detected"
        ]
    
    def _calculate_confidence(self, video: Dict, signal_strength: float) -> float:
        """Calculate confidence in the signal."""
        base_confidence = signal_strength * 0.7
        
        # Boost for trusted channels
        if video["channel"] in self.CHANNEL_TARGETS.get("institutional_grade", []):
            base_confidence += 0.2
        elif video["channel"] in self.CHANNEL_TARGETS.get("deep_research", []):
            base_confidence += 0.15
            
        # Recency boost
        days_old = (datetime.now() - video["published_at"]).days
        if days_old <= 1:
            base_confidence += 0.1
        elif days_old <= 3:
            base_confidence += 0.05
            
        return min(base_confidence, 1.0)
    
    async def analyze_channel_history(
        self,
        channel_name: str,
        max_videos: int = 20
    ) -> Dict[str, List[YouTubeSignal]]:
        """
        Analyze a channel's recent videos for patterns.
        Useful for tracking influencer sentiment shifts.
        """
        signals_by_ticker = {}
        
        # Get recent videos from channel
        videos = await self._get_channel_videos(channel_name, max_videos)
        
        for video in videos:
            signal = await self._analyze_video(video)
            if signal:
                for ticker in signal.tickers:
                    if ticker not in signals_by_ticker:
                        signals_by_ticker[ticker] = []
                    signals_by_ticker[ticker].append(signal)
        
        return signals_by_ticker
    
    async def _get_channel_videos(
        self,
        channel_name: str,
        max_videos: int
    ) -> List[Dict]:
        """Get recent videos from a channel."""
        # Placeholder - would fetch actual channel videos
        return [
            {
                "video_id": f"{channel_name}_vid_{i}",
                "title": f"Stock Pick #{i}: Hidden Gem",
                "channel": channel_name,
                "views": 30000,
                "likes": 1500,
                "comments": 200,
                "published_at": datetime.now() - timedelta(days=i),
                "description": "Analysis of undervalued stocks"
            }
            for i in range(min(max_videos, 3))
        ]
    
    async def extract_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Extract transcript from video for deep analysis.
        Uses captions API (200 quota units).
        """
        if not self._check_quota(self.QUOTA_COSTS["captions"]):
            return None
            
        # Would fetch actual transcript
        return """
        Today we're looking at NVDA, the AI leader.
        Three reasons I'm bullish:
        1. Data center revenue growing 400% YoY
        2. New H200 chips sold out through 2025
        3. Expanding TAM with inference market
        Price target: $1000 by end of year.
        """
    
    async def monitor_trending_finance(self) -> List[YouTubeSignal]:
        """
        Monitor trending finance videos for emerging signals.
        Efficient use of API quota.
        """
        signals = []
        
        # Search for trending finance content
        trending = await self.search_investment_videos(
            query="stocks investing",
            max_results=10,
            order="viewCount",
            published_after=datetime.now() - timedelta(days=1)
        )
        
        # Filter for high-confidence signals
        high_confidence = [s for s in trending if s.confidence > 0.75]
        
        return high_confidence
    
    async def analyze_comments_sentiment(
        self,
        video_id: str,
        max_comments: int = 100
    ) -> Dict[str, float]:
        """
        Analyze video comments for sentiment and ticker mentions.
        Comments often contain contrarian signals.
        """
        if not self._check_quota(self.QUOTA_COSTS["comments"]):
            return {}
            
        # Fetch comments (placeholder)
        comments = [
            "NVDA is overvalued, buying puts",
            "Loading up on TSLA before earnings",
            "AMD better value than NVDA"
        ]
        
        ticker_sentiment = {}
        
        for comment in comments:
            tickers = self._extract_tickers(comment)
            sentiment = self._analyze_comment_sentiment(comment)
            
            for ticker in tickers:
                if ticker not in ticker_sentiment:
                    ticker_sentiment[ticker] = []
                ticker_sentiment[ticker].append(sentiment)
        
        # Average sentiment per ticker
        result = {}
        for ticker, sentiments in ticker_sentiment.items():
            result[ticker] = sum(sentiments) / len(sentiments)
            
        return result
    
    def _analyze_comment_sentiment(self, comment: str) -> float:
        """Simple sentiment analysis for comments."""
        positive = ["bull", "buy", "long", "moon", "up", "calls"]
        negative = ["bear", "sell", "short", "puts", "down", "crash"]
        
        comment_lower = comment.lower()
        pos_count = sum(1 for word in positive if word in comment_lower)
        neg_count = sum(1 for word in negative if word in comment_lower)
        
        if pos_count + neg_count == 0:
            return 0.5
            
        return pos_count / (pos_count + neg_count)