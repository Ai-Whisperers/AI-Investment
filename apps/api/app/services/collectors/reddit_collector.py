"""
Reddit Collector
Monitors WSB, investing subreddits, and micro-communities for alpha signals
Uses PRAW with careful rate limiting (60 requests/min)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import re
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RedditSignal:
    """Signal extracted from Reddit post/comment."""
    subreddit: str
    post_id: str
    title: str
    body: str
    score: int
    comments: int
    author: str
    created_utc: datetime
    tickers: List[str]
    sentiment: float
    signal_type: str  # DD, gain, loss, discussion, meme
    confidence: float
    

class RedditCollector:
    """
    Collects signals from Reddit using PRAW API.
    Focuses on communities with alpha generation potential.
    """
    
    # High-value subreddits for different signal types
    SUBREDDIT_TARGETS = {
        "momentum": [
            "wallstreetbets",
            "stocks", 
            "StockMarket",
            "pennystocks",
            "Shortsqueeze"
        ],
        "fundamental": [
            "investing",
            "SecurityAnalysis",
            "ValueInvesting",
            "stocks",
            "StockMarket"
        ],
        "micro_communities": [
            "RobinHoodPennyStocks",
            "Biotechplays",
            "SPACs",
            "UraniumSqueeze",
            "Vitards"  # Steel gang
        ],
        "crypto": [
            "CryptoCurrency",
            "CryptoMoonShots",
            "SatoshiStreetBets"
        ],
        "insider_knowledge": [
            "wallstreetbetsOGs",
            "options",
            "thetagang"
        ]
    }
    
    # Patterns that indicate high-value posts
    SIGNAL_PATTERNS = {
        "dd_post": r"(DD|Due Diligence|Deep Dive|Research)",
        "gain_porn": r"(Gain|Profit|Up \d+%|Made \$)",
        "unusual_activity": r"(Unusual|Strange|Weird|Massive) (Options|Volume|Activity)",
        "insider": r"(Work at|Employee|Inside|Know someone)",
        "catalyst": r"(Catalyst|Upcoming|Announcement|Earnings|FDA)",
        "squeeze": r"(Squeeze|Short Interest|SI|CTB|Borrow)"
    }
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        """Initialize Reddit collector (credentials optional for read-only)."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.reddit = None  # Will initialize PRAW instance
        self.rate_limit_remaining = 60
        self.last_request_time = datetime.now()
        self.ticker_cache = self._load_ticker_list()
        
    def _load_ticker_list(self) -> Set[str]:
        """Load list of valid tickers for extraction."""
        # Common tickers (would load from file in production)
        return {
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA",
            "AMD", "INTC", "NFLX", "DIS", "PYPL", "SQ", "ROKU",
            "GME", "AMC", "BB", "NOK", "PLTR", "SOFI", "WISH",
            "SPY", "QQQ", "IWM", "VXX", "UVXY", "SQQQ", "TQQQ"
        }
        
    async def collect_subreddit(
        self, 
        subreddit: str, 
        sort: str = "hot",
        limit: int = 25,
        time_filter: str = "day"
    ) -> List[RedditSignal]:
        """
        Collect signals from a specific subreddit.
        Respects rate limits and extracts high-value content.
        """
        signals = []
        
        try:
            # Rate limiting
            await self._enforce_rate_limit()
            
            # Fetch posts (simplified - would use PRAW in production)
            posts = await self._fetch_posts(subreddit, sort, limit, time_filter)
            
            for post in posts:
                # Extract signal if high-value
                signal = self._extract_signal(post, subreddit)
                if signal and signal.confidence > 0.6:
                    signals.append(signal)
                    
                # Also check top comments for signals
                if post.get("num_comments", 0) > 50:
                    comment_signals = await self._extract_comment_signals(
                        post["id"], subreddit
                    )
                    signals.extend(comment_signals)
            
            logger.info(f"Collected {len(signals)} signals from r/{subreddit}")
            
        except Exception as e:
            logger.error(f"Error collecting from r/{subreddit}: {e}")
            
        return signals
    
    async def _enforce_rate_limit(self):
        """Enforce Reddit API rate limits (60/min)."""
        time_since_last = (datetime.now() - self.last_request_time).total_seconds()
        
        if time_since_last < 1:  # Minimum 1 second between requests
            await asyncio.sleep(1 - time_since_last)
            
        self.last_request_time = datetime.now()
        
    async def _fetch_posts(
        self, 
        subreddit: str, 
        sort: str, 
        limit: int,
        time_filter: str
    ) -> List[Dict]:
        """Fetch posts from Reddit (placeholder - would use PRAW)."""
        # Simulated data for testing
        return [
            {
                "id": f"post_{i}",
                "title": f"$NVDA DD: AI revolution just starting",
                "selftext": "Massive opportunity in AI chips. NVDA to $1000.",
                "score": 1500 - i * 100,
                "num_comments": 200 - i * 10,
                "author": f"user_{i}",
                "created_utc": datetime.now().timestamp(),
                "upvote_ratio": 0.9
            }
            for i in range(min(limit, 5))
        ]
    
    def _extract_signal(self, post: Dict, subreddit: str) -> Optional[RedditSignal]:
        """Extract trading signal from Reddit post."""
        # Extract tickers mentioned
        tickers = self._extract_tickers(
            post.get("title", "") + " " + post.get("selftext", "")
        )
        
        if not tickers:
            return None
            
        # Determine signal type
        signal_type = self._classify_post(post)
        
        # Calculate sentiment
        sentiment = self._calculate_sentiment(post)
        
        # Calculate confidence based on engagement
        confidence = self._calculate_confidence(post, signal_type)
        
        return RedditSignal(
            subreddit=subreddit,
            post_id=post["id"],
            title=post.get("title", ""),
            body=post.get("selftext", "")[:500],  # Truncate
            score=post.get("score", 0),
            comments=post.get("num_comments", 0),
            author=post.get("author", "unknown"),
            created_utc=datetime.fromtimestamp(post.get("created_utc", 0)),
            tickers=tickers,
            sentiment=sentiment,
            signal_type=signal_type,
            confidence=confidence
        )
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text."""
        # Look for $TICKER or TICKER patterns
        pattern = r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{2,5})(?:\s|$|\.|\,)'
        matches = re.findall(pattern, text)
        
        tickers = []
        for match in matches:
            ticker = match[0] or match[1]
            if ticker in self.ticker_cache:
                tickers.append(ticker)
                
        return list(set(tickers))  # Remove duplicates
    
    def _classify_post(self, post: Dict) -> str:
        """Classify the type of Reddit post."""
        title = post.get("title", "").lower()
        text = post.get("selftext", "").lower()
        full_text = title + " " + text
        
        for pattern_name, pattern in self.SIGNAL_PATTERNS.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                return pattern_name
                
        return "discussion"
    
    def _calculate_sentiment(self, post: Dict) -> float:
        """Calculate sentiment score for post."""
        # Simple sentiment based on keywords (would use NLP in production)
        positive_words = ["bullish", "moon", "squeeze", "buy", "calls", "up", "gains"]
        negative_words = ["bearish", "puts", "short", "sell", "crash", "down", "loss"]
        
        text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count + negative_count == 0:
            return 0.5
            
        return positive_count / (positive_count + negative_count)
    
    def _calculate_confidence(self, post: Dict, signal_type: str) -> float:
        """Calculate confidence score for signal."""
        base_confidence = 0.5
        
        # Boost for high engagement
        score = post.get("score", 0)
        if score > 1000:
            base_confidence += 0.2
        elif score > 500:
            base_confidence += 0.1
            
        # Boost for many comments (discussion)
        comments = post.get("num_comments", 0)
        if comments > 200:
            base_confidence += 0.15
        elif comments > 100:
            base_confidence += 0.1
            
        # Boost for DD posts
        if signal_type == "dd_post":
            base_confidence += 0.2
        elif signal_type == "unusual_activity":
            base_confidence += 0.15
        elif signal_type == "insider":
            base_confidence += 0.25
            
        # High upvote ratio
        if post.get("upvote_ratio", 0) > 0.9:
            base_confidence += 0.1
            
        return min(base_confidence, 1.0)
    
    async def _extract_comment_signals(
        self, 
        post_id: str, 
        subreddit: str
    ) -> List[RedditSignal]:
        """Extract signals from post comments."""
        # Would fetch and analyze comments in production
        return []
    
    async def monitor_live_stream(
        self, 
        subreddits: List[str],
        callback: callable
    ):
        """
        Monitor Reddit in real-time for signals.
        Uses submission stream for live updates.
        """
        logger.info(f"Starting live monitoring of {subreddits}")
        
        while True:
            try:
                for subreddit in subreddits:
                    # Check new posts
                    signals = await self.collect_subreddit(
                        subreddit, 
                        sort="new", 
                        limit=10
                    )
                    
                    for signal in signals:
                        if signal.confidence > 0.7:
                            await callback(signal)
                            
                # Sleep to respect rate limits
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in live monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    async def collect_wsb_daily_discussion(self) -> List[Dict]:
        """
        Special collector for WSB daily discussion thread.
        This is where the real alpha hides.
        """
        signals = []
        
        # Find daily discussion thread
        daily_thread = await self._find_daily_thread("wallstreetbets")
        
        if daily_thread:
            # Analyze comments for ticker mentions and sentiment
            comments = await self._fetch_thread_comments(daily_thread["id"])
            
            # Aggregate ticker mentions
            ticker_mentions = {}
            
            for comment in comments:
                tickers = self._extract_tickers(comment.get("body", ""))
                sentiment = self._calculate_sentiment(comment)
                
                for ticker in tickers:
                    if ticker not in ticker_mentions:
                        ticker_mentions[ticker] = {
                            "mentions": 0,
                            "sentiment_sum": 0,
                            "bullish": 0,
                            "bearish": 0
                        }
                    
                    ticker_mentions[ticker]["mentions"] += 1
                    ticker_mentions[ticker]["sentiment_sum"] += sentiment
                    
                    if sentiment > 0.6:
                        ticker_mentions[ticker]["bullish"] += 1
                    elif sentiment < 0.4:
                        ticker_mentions[ticker]["bearish"] += 1
            
            # Convert to signals
            for ticker, data in ticker_mentions.items():
                if data["mentions"] >= 5:  # Minimum threshold
                    avg_sentiment = data["sentiment_sum"] / data["mentions"]
                    
                    signals.append({
                        "ticker": ticker,
                        "mentions": data["mentions"],
                        "sentiment": avg_sentiment,
                        "bullish_count": data["bullish"],
                        "bearish_count": data["bearish"],
                        "source": "wsb_daily",
                        "confidence": min(data["mentions"] / 50, 1.0)  # More mentions = higher confidence
                    })
            
        return sorted(signals, key=lambda x: x["mentions"], reverse=True)
    
    async def _find_daily_thread(self, subreddit: str) -> Optional[Dict]:
        """Find the daily discussion thread."""
        # Placeholder - would search for pinned daily thread
        return {"id": "daily_thread_id", "title": "Daily Discussion Thread"}
    
    async def _fetch_thread_comments(self, thread_id: str) -> List[Dict]:
        """Fetch all comments from a thread."""
        # Placeholder - would fetch actual comments
        return [
            {"body": "$NVDA to the moon!", "score": 50},
            {"body": "Loading up on TSLA calls", "score": 30},
            {"body": "PLTR is the play boys", "score": 25}
        ]