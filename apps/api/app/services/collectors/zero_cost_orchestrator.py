"""
Zero-Cost Orchestrator
Coordinates all collectors within free tier limits
Implements intelligent scheduling and prioritization
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import os

from .reddit_collector import RedditCollector, RedditSignal
from .youtube_collector import YouTubeCollector, YouTubeSignal
from .chan_collector import ChanCollector, ChanSignal

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSignal:
    """Unified signal from all sources."""
    ticker: str
    sources: List[str]
    signal_strength: float
    sentiment: float
    urgency: float
    confidence: float
    timestamp: datetime
    metadata: Dict
    action: str  # buy, sell, hold, watch
    expected_return: float
    risk_level: str  # low, medium, high, extreme
    

class ZeroCostOrchestrator:
    """
    Master orchestrator for zero-cost data collection.
    Manages all collectors within free tier limits.
    """
    
    # Daily quota allocations
    DAILY_QUOTAS = {
        "reddit": {
            "requests": 3600,  # 60/min * 60 min
            "priority": 0.3  # 30% of collection time
        },
        "youtube": {
            "units": 10000,  # API quota
            "priority": 0.2  # 20% of collection time
        },
        "chan": {
            "requests": 3600,  # 1/sec * 3600 sec
            "priority": 0.25  # 25% of collection time
        },
        "github_actions": {
            "minutes": 60,  # Daily budget (2000/month ÷ 30)
            "runs": 4  # 4 runs per day
        }
    }
    
    # Collection schedule (UTC times)
    SCHEDULE = {
        "06:00": {
            "duration": 20,
            "focus": "overnight_developments",
            "sources": ["chan", "reddit", "youtube"]
        },
        "13:30": {
            "duration": 15,
            "focus": "market_open_momentum",
            "sources": ["reddit", "chan"]
        },
        "20:00": {
            "duration": 15,
            "focus": "after_hours_analysis",
            "sources": ["youtube", "reddit"]
        },
        "03:00": {
            "duration": 10,
            "focus": "asia_market_signals",
            "sources": ["chan"]
        }
    }
    
    def __init__(self):
        """Initialize orchestrator with all collectors."""
        self.reddit = RedditCollector()
        self.youtube = YouTubeCollector()
        self.chan = ChanCollector()
        
        self.quota_used = {
            "reddit": 0,
            "youtube": 0,
            "chan": 0,
            "github_minutes": 0
        }
        
        self.signals_collected = []
        self.high_priority_tickers = set()
        
    async def run_scheduled_collection(self):
        """
        Run collection based on schedule.
        Called by GitHub Actions at scheduled times.
        """
        current_hour = datetime.now().strftime("%H:00")
        
        if current_hour not in self.SCHEDULE:
            logger.warning(f"No scheduled collection for {current_hour}")
            return
            
        schedule_config = self.SCHEDULE[current_hour]
        duration = schedule_config["duration"]
        focus = schedule_config["focus"]
        sources = schedule_config["sources"]
        
        logger.info(f"Starting {focus} collection for {duration} minutes")
        
        # Set timeout for collection
        try:
            await asyncio.wait_for(
                self._collect_from_sources(sources, focus),
                timeout=duration * 60
            )
        except asyncio.TimeoutError:
            logger.warning(f"Collection timeout after {duration} minutes")
            
        # Process and store signals
        unified_signals = await self._process_signals()
        await self._store_signals(unified_signals)
        
        # Update quota tracking
        self.quota_used["github_minutes"] += duration
        
        logger.info(f"Collection complete. Found {len(unified_signals)} signals")
        
    async def _collect_from_sources(
        self,
        sources: List[str],
        focus: str
    ):
        """Collect from specified sources based on focus."""
        tasks = []
        
        if "reddit" in sources:
            tasks.append(self._collect_reddit(focus))
            
        if "youtube" in sources:
            tasks.append(self._collect_youtube(focus))
            
        if "chan" in sources:
            tasks.append(self._collect_chan(focus))
            
        # Run all collections in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Collection error: {result}")
            elif isinstance(result, list):
                self.signals_collected.extend(result)
                
    async def _collect_reddit(self, focus: str) -> List[RedditSignal]:
        """Collect from Reddit based on focus."""
        signals = []
        
        if focus == "market_open_momentum":
            # Focus on WSB and momentum subs
            subreddits = ["wallstreetbets", "stocks", "Shortsqueeze"]
            sort = "hot"
            
        elif focus == "overnight_developments":
            # Check all investing subs for overnight news
            subreddits = ["investing", "StockMarket", "SecurityAnalysis"]
            sort = "new"
            
        else:
            # General collection
            subreddits = ["wallstreetbets", "stocks"]
            sort = "hot"
            
        for subreddit in subreddits:
            if self.quota_used["reddit"] >= self.DAILY_QUOTAS["reddit"]["requests"]:
                break
                
            sub_signals = await self.reddit.collect_subreddit(
                subreddit,
                sort=sort,
                limit=25
            )
            signals.extend(sub_signals)
            self.quota_used["reddit"] += 25  # Approximate request count
            
        # Also check daily discussion if WSB
        if "wallstreetbets" in subreddits:
            daily_signals = await self.reddit.collect_wsb_daily_discussion()
            signals.extend(daily_signals)
            
        return signals
    
    async def _collect_youtube(self, focus: str) -> List[YouTubeSignal]:
        """Collect from YouTube based on focus."""
        signals = []
        
        if focus == "after_hours_analysis":
            # Search for daily market wrap-ups
            query = "stock market today analysis"
            
        elif focus == "overnight_developments":
            # Search for deep research
            query = "stock fundamental analysis DD"
            
        else:
            query = "stocks to buy now"
            
        # Search for videos (uses 100 quota units)
        if self.quota_used["youtube"] + 100 <= self.DAILY_QUOTAS["youtube"]["units"]:
            video_signals = await self.youtube.search_investment_videos(
                query=query,
                max_results=10,
                order="relevance",
                published_after=datetime.now() - timedelta(days=1)
            )
            signals.extend(video_signals)
            self.quota_used["youtube"] += 100
            
        # Monitor trending if quota allows
        if self.quota_used["youtube"] + 100 <= self.DAILY_QUOTAS["youtube"]["units"]:
            trending = await self.youtube.monitor_trending_finance()
            signals.extend(trending)
            self.quota_used["youtube"] += 100
            
        return signals
    
    async def _collect_chan(self, focus: str) -> List[ChanSignal]:
        """Collect from 4chan based on focus."""
        signals = []
        
        if focus == "asia_market_signals":
            # Focus on Asian market discussions
            boards = ["biz"]
            pages = 2
            
        elif focus == "market_open_momentum":
            # Look for insider threads
            return await self.chan.monitor_insider_threads()
            
        else:
            boards = ["biz"]
            pages = 1
            
        for board in boards:
            if self.quota_used["chan"] >= self.DAILY_QUOTAS["chan"]["requests"]:
                break
                
            board_signals = await self.chan.collect_board(board, pages)
            signals.extend(board_signals)
            self.quota_used["chan"] += pages * 10  # Approximate request count
            
        return signals
    
    async def _process_signals(self) -> List[UnifiedSignal]:
        """Process collected signals into unified format."""
        # Group signals by ticker
        ticker_signals = {}
        
        for signal in self.signals_collected:
            tickers = []
            
            if isinstance(signal, RedditSignal):
                tickers = signal.tickers
                source = f"reddit_{signal.subreddit}"
                
            elif isinstance(signal, YouTubeSignal):
                tickers = signal.tickers
                source = f"youtube_{signal.channel}"
                
            elif isinstance(signal, ChanSignal):
                tickers = signal.tickers
                source = f"4chan_{signal.board}"
                
            for ticker in tickers:
                if ticker not in ticker_signals:
                    ticker_signals[ticker] = []
                    
                ticker_signals[ticker].append({
                    "source": source,
                    "signal": signal
                })
                
        # Create unified signals
        unified = []
        
        for ticker, signals in ticker_signals.items():
            if len(signals) >= 2:  # Need at least 2 sources
                unified_signal = self._create_unified_signal(ticker, signals)
                if unified_signal.confidence > 0.6:
                    unified.append(unified_signal)
                    
        # Sort by confidence
        unified.sort(key=lambda x: x.confidence, reverse=True)
        
        return unified
    
    def _create_unified_signal(
        self,
        ticker: str,
        signals: List[Dict]
    ) -> UnifiedSignal:
        """Create unified signal from multiple sources."""
        sources = [s["source"] for s in signals]
        
        # Aggregate metrics
        sentiments = []
        confidences = []
        urgencies = []
        
        for sig_data in signals:
            signal = sig_data["signal"]
            
            if hasattr(signal, "sentiment"):
                sentiments.append(signal.sentiment)
            if hasattr(signal, "confidence"):
                confidences.append(signal.confidence)
            if hasattr(signal, "urgency"):
                urgencies.append(signal.urgency)
                
        # Calculate aggregates
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.5
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        avg_urgency = sum(urgencies) / len(urgencies) if urgencies else 0.5
        
        # Boost confidence for multiple sources
        source_boost = min(len(set(sources)) * 0.1, 0.3)
        final_confidence = min(avg_confidence + source_boost, 1.0)
        
        # Determine action
        if avg_sentiment > 0.7 and final_confidence > 0.7:
            action = "buy"
            expected_return = 0.15 + (final_confidence - 0.7) * 0.5  # 15-30%
        elif avg_sentiment < 0.3 and final_confidence > 0.7:
            action = "sell"
            expected_return = -0.1
        else:
            action = "watch"
            expected_return = 0.0
            
        # Determine risk level
        if "4chan" in str(sources):
            risk_level = "high" if avg_urgency > 0.7 else "medium"
        else:
            risk_level = "medium" if final_confidence > 0.8 else "low"
            
        return UnifiedSignal(
            ticker=ticker,
            sources=sources,
            signal_strength=len(signals) / 10,  # Normalize
            sentiment=avg_sentiment,
            urgency=avg_urgency,
            confidence=final_confidence,
            timestamp=datetime.now(),
            metadata={
                "signal_count": len(signals),
                "unique_sources": len(set(sources))
            },
            action=action,
            expected_return=expected_return,
            risk_level=risk_level
        )
    
    async def _store_signals(self, signals: List[UnifiedSignal]):
        """Store signals to database or file."""
        # Store to JSON file (would use database in production)
        output_file = f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        signal_data = []
        for signal in signals:
            signal_data.append({
                "ticker": signal.ticker,
                "sources": signal.sources,
                "confidence": signal.confidence,
                "sentiment": signal.sentiment,
                "urgency": signal.urgency,
                "action": signal.action,
                "expected_return": signal.expected_return,
                "risk_level": signal.risk_level,
                "timestamp": signal.timestamp.isoformat()
            })
            
        with open(output_file, 'w') as f:
            json.dump(signal_data, f, indent=2)
            
        logger.info(f"Stored {len(signals)} signals to {output_file}")
        
        # Also store high-priority signals separately
        high_priority = [s for s in signals if s.confidence > 0.8]
        if high_priority:
            await self._alert_high_priority(high_priority)
            
    async def _alert_high_priority(self, signals: List[UnifiedSignal]):
        """Alert for high-priority signals."""
        for signal in signals:
            logger.warning(
                f"HIGH PRIORITY: {signal.ticker} - "
                f"Action: {signal.action}, "
                f"Expected Return: {signal.expected_return:.1%}, "
                f"Confidence: {signal.confidence:.2f}"
            )
            
    def get_quota_status(self) -> Dict:
        """Get current quota usage status."""
        status = {}
        
        for source, quota in self.DAILY_QUOTAS.items():
            if source == "github_actions":
                used = self.quota_used.get("github_minutes", 0)
                limit = quota["minutes"]
                remaining = limit - used
            elif source == "reddit":
                used = self.quota_used.get("reddit", 0)
                limit = quota["requests"]
                remaining = limit - used
            elif source == "youtube":
                used = self.quota_used.get("youtube", 0)
                limit = quota["units"]
                remaining = limit - used
            elif source == "chan":
                used = self.quota_used.get("chan", 0)
                limit = quota["requests"]
                remaining = limit - used
            else:
                continue
                
            status[source] = {
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "percentage_used": (used / limit * 100) if limit > 0 else 0
            }
            
        return status