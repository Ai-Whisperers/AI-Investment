"""
Twitter/X Collector
Monitors FinTwit for market signals
Uses Nitter instances for rate limit bypass
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TwitterSignal:
    """Signal from Twitter/X."""
    tweet_id: str
    username: str  
    content: str
    likes: int
    retweets: int
    replies: int
    timestamp: datetime
    tickers: List[str]
    sentiment: float
    influence_score: float
    confidence: float


class TwitterCollector:
    """
    Collects signals from Twitter/X FinTwit community.
    Uses alternative methods to avoid API costs.
    """
    
    # High-value FinTwit accounts
    FINTWIT_INFLUENCERS = {
        "high_influence": [
            "jimcramer", "carlquintanilla", "scottappleby",
            "ReformedBroker", "Downtown", "TheStalwart"
        ],
        "traders": [
            "warrior_0719", "PeterLBrandt", "RaoulGMI",
            "zerohedge", "FirstSquawk", "LiveSquawk"
        ],
        "analysts": [
            "charliebilello", "callieabost", "GergelyOrosz",
            "SethCL", "chigrl", "hmeisler"
        ]
    }
    
    def __init__(self):
        """Initialize Twitter collector."""
        self.nitter_instances = [
            "nitter.net",
            "nitter.42l.fr",
            "nitter.pussthecat.org"
        ]
        self.current_instance = 0
        
    async def collect_fintwit_signals(self) -> List[TwitterSignal]:
        """Collect signals from FinTwit influencers."""
        signals = []
        
        # Placeholder implementation
        for category, accounts in self.FINTWIT_INFLUENCERS.items():
            for account in accounts[:2]:  # Limit for testing
                tweets = await self._get_user_tweets(account)
                for tweet in tweets:
                    signal = self._extract_signal(tweet, account)
                    if signal and signal.confidence > 0.6:
                        signals.append(signal)
                        
        return signals
    
    async def _get_user_tweets(self, username: str) -> List[Dict]:
        """Get recent tweets from user (placeholder)."""
        # Would scrape from Nitter in production
        return [
            {
                "id": f"tweet_{username}_1",
                "content": f"$NVDA breaking out! Target $1000",
                "likes": 500,
                "retweets": 100,
                "replies": 50,
                "timestamp": datetime.now()
            }
        ]
    
    def _extract_signal(self, tweet: Dict, username: str) -> Optional[TwitterSignal]:
        """Extract trading signal from tweet."""
        content = tweet.get("content", "")
        tickers = self._extract_tickers(content)
        
        if not tickers:
            return None
            
        return TwitterSignal(
            tweet_id=tweet["id"],
            username=username,
            content=content[:280],
            likes=tweet.get("likes", 0),
            retweets=tweet.get("retweets", 0),
            replies=tweet.get("replies", 0),
            timestamp=tweet.get("timestamp", datetime.now()),
            tickers=tickers,
            sentiment=self._calculate_sentiment(content),
            influence_score=self._get_influence_score(username),
            confidence=self._calculate_confidence(tweet, username)
        )
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract tickers from tweet text."""
        pattern = r'\$([A-Z]{1,5})\b'
        matches = re.findall(pattern, text)
        return list(set(matches))
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate tweet sentiment."""
        positive = ["bullish", "buy", "long", "breakout", "moon"]
        negative = ["bearish", "sell", "short", "crash", "dump"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive if word in text_lower)
        neg_count = sum(1 for word in negative if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.5
        return pos_count / (pos_count + neg_count)
    
    def _get_influence_score(self, username: str) -> float:
        """Get influence score for account."""
        if username in self.FINTWIT_INFLUENCERS["high_influence"]:
            return 0.9
        elif username in self.FINTWIT_INFLUENCERS["traders"]:
            return 0.7
        elif username in self.FINTWIT_INFLUENCERS["analysts"]:
            return 0.8
        return 0.5
    
    def _calculate_confidence(self, tweet: Dict, username: str) -> float:
        """Calculate signal confidence."""
        base = 0.5
        
        # Engagement boost
        if tweet.get("likes", 0) > 1000:
            base += 0.2
        elif tweet.get("likes", 0) > 500:
            base += 0.1
            
        # Influence boost
        base += self._get_influence_score(username) * 0.2
        
        return min(base, 1.0)