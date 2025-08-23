"""
4chan /biz/ Collector
Monitors 4chan's business board for early signals
This is where GME was first discovered - pure alpha source
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import re
import json
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)


@dataclass 
class ChanSignal:
    """Signal from 4chan /biz/ board."""
    thread_id: str
    board: str
    subject: str
    comment: str
    replies: int
    images: int
    unique_ips: int
    timestamp: datetime
    tickers: List[str]
    signal_type: str  # shill, fud, dd, insider, pump
    sentiment: float
    urgency: float  # How time-sensitive
    confidence: float
    

class ChanCollector:
    """
    Collects signals from 4chan /biz/ and other boards.
    The most unfiltered, early-stage alpha source.
    """
    
    # Patterns that indicate high-value threads
    SIGNAL_PATTERNS = {
        "insider": [
            r"work at", r"friend at", r"insider", r"leaked",
            r"not public", r"announcement tomorrow", r"before market"
        ],
        "pump_coordination": [
            r"pump at", r"everyone buy", r"coordinated", r"telegram group",
            r"discord", r"all in at \d+"
        ],
        "technical_analysis": [
            r"chart", r"support at", r"resistance", r"breakout",
            r"golden cross", r"cup and handle", r"ascending triangle"
        ],
        "fundamental_dd": [
            r"financials", r"earnings", r"revenue", r"P/E",
            r"undervalued", r"market cap", r"book value"
        ],
        "early_discovery": [
            r"found this", r"no one talking about", r"before it moons",
            r"next GME", r"hidden gem", r"under radar"
        ]
    }
    
    # Keywords that indicate urgency
    URGENCY_KEYWORDS = {
        "high": ["tomorrow", "today", "now", "immediately", "asap", "before close"],
        "medium": ["this week", "soon", "next week", "earnings coming"],
        "low": ["long term", "hold", "accumulate", "DCA"]
    }
    
    # Boards to monitor
    BOARDS = {
        "biz": "business",  # Main board for crypto and stocks
        "g": "technology",  # Tech stocks
        "pol": "politically_incorrect"  # Geopolitical events affecting markets
    }
    
    def __init__(self):
        """Initialize 4chan collector."""
        self.base_url = "https://a.4cdn.org"
        self.last_request_time = datetime.now()
        self.seen_threads = set()  # Track processed threads
        self.rate_limit_delay = 1  # 1 second between requests
        
    async def collect_board(
        self,
        board: str = "biz",
        pages: int = 3
    ) -> List[ChanSignal]:
        """
        Collect signals from a 4chan board.
        Focuses on high-engagement threads.
        """
        signals = []
        
        try:
            # Get catalog (all threads)
            threads = await self._get_catalog(board, pages)
            
            for thread in threads:
                # Skip if already processed
                thread_id = str(thread.get("no", ""))
                if thread_id in self.seen_threads:
                    continue
                    
                # Analyze for signals
                signal = self._extract_signal(thread, board)
                
                if signal and signal.confidence > 0.5:
                    signals.append(signal)
                    self.seen_threads.add(thread_id)
                    
                    # Get full thread if high value
                    if signal.confidence > 0.7:
                        full_thread = await self._get_full_thread(board, thread_id)
                        additional_signals = self._analyze_thread_replies(full_thread, board)
                        signals.extend(additional_signals)
            
            logger.info(f"Collected {len(signals)} signals from /{board}/")
            
        except Exception as e:
            logger.error(f"Error collecting from /{board}/: {e}")
            
        return signals
    
    async def _get_catalog(self, board: str, pages: int) -> List[Dict]:
        """Get board catalog (placeholder - would use actual API)."""
        await self._rate_limit()
        
        # Simulated catalog data
        threads = []
        for page in range(pages):
            threads.extend([
                {
                    "no": f"{page}_{i}",
                    "sub": "INSIDER INFO: Major acquisition tomorrow",
                    "com": "My friend works at NVDA. Big announcement pre-market. Load up now.",
                    "replies": 150 - i * 10,
                    "images": 20 - i,
                    "unique_ips": 80 - i * 5,
                    "time": int(datetime.now().timestamp())
                }
                for i in range(5)
            ])
            
        return threads
    
    async def _get_full_thread(self, board: str, thread_id: str) -> Dict:
        """Get full thread with all replies."""
        await self._rate_limit()
        
        # Simulated thread data
        return {
            "posts": [
                {
                    "no": f"reply_{i}",
                    "com": "Confirmed, I work there too. It's happening.",
                    "time": int(datetime.now().timestamp())
                }
                for i in range(10)
            ]
        }
    
    async def _rate_limit(self):
        """Enforce rate limiting (1 req/sec)."""
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = datetime.now()
    
    def _extract_signal(self, thread: Dict, board: str) -> Optional[ChanSignal]:
        """Extract trading signal from thread."""
        subject = thread.get("sub", "")
        comment = self._clean_html(thread.get("com", ""))
        full_text = f"{subject} {comment}"
        
        # Extract tickers
        tickers = self._extract_tickers(full_text)
        if not tickers and board == "biz":
            # On /biz/, also look for crypto symbols
            tickers = self._extract_crypto_symbols(full_text)
            
        if not tickers:
            return None
            
        # Classify signal type
        signal_type = self._classify_thread(full_text)
        
        # Calculate urgency
        urgency = self._calculate_urgency(full_text)
        
        # Calculate sentiment
        sentiment = self._calculate_sentiment(full_text)
        
        # Calculate confidence
        confidence = self._calculate_confidence(thread, signal_type, urgency)
        
        return ChanSignal(
            thread_id=str(thread.get("no", "")),
            board=board,
            subject=subject[:100],
            comment=comment[:500],
            replies=thread.get("replies", 0),
            images=thread.get("images", 0),
            unique_ips=thread.get("unique_ips", 0),
            timestamp=datetime.fromtimestamp(thread.get("time", 0)),
            tickers=tickers,
            signal_type=signal_type,
            sentiment=sentiment,
            urgency=urgency,
            confidence=confidence
        )
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from 4chan text."""
        # Remove common HTML tags
        text = re.sub(r'<br>', ' ', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&amp;', '&', text)
        return text
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text."""
        # Common patterns on 4chan
        patterns = [
            r'\$([A-Z]{1,5})\b',  # $TICKER
            r'\b([A-Z]{2,5})\b(?:\s+stock|\s+calls|\s+puts)',  # TICKER stock/calls/puts
            r'ticker:?\s*([A-Z]{1,5})',  # ticker: TICKER
        ]
        
        tickers = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tickers.update(match.upper() for match in matches if 2 <= len(match) <= 5)
            
        # Filter out common false positives
        false_positives = {"THE", "AND", "FOR", "ARE", "BUT", "NOT", "ALL", "NEW", "ONE"}
        tickers = tickers - false_positives
        
        return list(tickers)
    
    def _extract_crypto_symbols(self, text: str) -> List[str]:
        """Extract crypto symbols from text."""
        crypto_patterns = [
            r'\b(BTC|ETH|BNB|SOL|ADA|DOT|AVAX|MATIC|LINK|UNI)\b',
            r'\$([A-Z]{3,6})\b',  # Crypto often 3-6 chars
        ]
        
        cryptos = set()
        for pattern in crypto_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            cryptos.update(match.upper() for match in matches)
            
        return list(cryptos)
    
    def _classify_thread(self, text: str) -> str:
        """Classify the type of signal."""
        text_lower = text.lower()
        
        # Check each pattern category
        for signal_type, patterns in self.SIGNAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return signal_type
                    
        # Default classification based on keywords
        if "buy" in text_lower or "long" in text_lower:
            return "shill"
        elif "sell" in text_lower or "short" in text_lower:
            return "fud"
        else:
            return "discussion"
    
    def _calculate_urgency(self, text: str) -> float:
        """Calculate how time-sensitive the signal is."""
        text_lower = text.lower()
        
        for urgency_level, keywords in self.URGENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if urgency_level == "high":
                        return 0.9
                    elif urgency_level == "medium":
                        return 0.6
                    else:
                        return 0.3
                        
        return 0.5  # Default medium urgency
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment (bullish/bearish)."""
        bullish = ["moon", "pump", "buy", "calls", "long", "rocket", "lambo", "gains"]
        bearish = ["dump", "sell", "puts", "short", "crash", "rug", "scam", "ponzi"]
        
        text_lower = text.lower()
        bull_count = sum(1 for word in bullish if word in text_lower)
        bear_count = sum(1 for word in bearish if word in text_lower)
        
        if bull_count + bear_count == 0:
            return 0.5
            
        return bull_count / (bull_count + bear_count)
    
    def _calculate_confidence(
        self,
        thread: Dict,
        signal_type: str,
        urgency: float
    ) -> float:
        """Calculate confidence in the signal."""
        base_confidence = 0.3  # Start low for 4chan
        
        # Boost for engagement
        replies = thread.get("replies", 0)
        if replies > 100:
            base_confidence += 0.25
        elif replies > 50:
            base_confidence += 0.15
        elif replies > 20:
            base_confidence += 0.1
            
        # Boost for unique IPs (not samefagging)
        unique_ips = thread.get("unique_ips", 0)
        if unique_ips > 50:
            base_confidence += 0.2
        elif unique_ips > 25:
            base_confidence += 0.1
            
        # Boost for insider/leak signals
        if signal_type == "insider":
            base_confidence += 0.3
        elif signal_type == "early_discovery":
            base_confidence += 0.2
        elif signal_type == "pump_coordination":
            base_confidence -= 0.1  # Lower confidence for pumps
            
        # Urgency modifier
        if urgency > 0.8:
            base_confidence += 0.1  # Time-sensitive info often valuable
            
        return min(max(base_confidence, 0), 1.0)
    
    def _analyze_thread_replies(
        self,
        thread_data: Dict,
        board: str
    ) -> List[ChanSignal]:
        """Analyze replies for additional signals."""
        signals = []
        
        for post in thread_data.get("posts", []):
            comment = self._clean_html(post.get("com", ""))
            
            # Look for confirmation or refutation
            if any(word in comment.lower() for word in ["confirm", "true", "happening"]):
                # Confirmation increases confidence
                pass
            elif any(word in comment.lower() for word in ["fake", "larp", "false"]):
                # Refutation decreases confidence
                pass
                
        return signals
    
    async def monitor_insider_threads(self) -> List[ChanSignal]:
        """
        Specifically monitor for insider information threads.
        These are the highest value signals on 4chan.
        """
        high_value_signals = []
        
        # Search all boards for insider keywords
        for board in ["biz", "g"]:
            signals = await self.collect_board(board, pages=2)
            
            # Filter for insider signals
            insider_signals = [
                s for s in signals
                if s.signal_type == "insider" and s.confidence > 0.6
            ]
            
            high_value_signals.extend(insider_signals)
            
        return high_value_signals
    
    async def detect_coordinated_pumps(self) -> List[Dict]:
        """
        Detect coordinated pump attempts.
        These can be profitable if entered early.
        """
        pumps = []
        
        signals = await self.collect_board("biz", pages=1)
        
        for signal in signals:
            if signal.signal_type == "pump_coordination":
                pumps.append({
                    "ticker": signal.tickers[0] if signal.tickers else "UNKNOWN",
                    "thread_id": signal.thread_id,
                    "participants": signal.unique_ips,
                    "urgency": signal.urgency,
                    "timestamp": signal.timestamp,
                    "warning": "Coordinated pump detected - high risk"
                })
                
        return pumps
    
    def calculate_thread_velocity(
        self,
        thread_id: str,
        board: str = "biz"
    ) -> float:
        """
        Calculate how fast a thread is gaining replies.
        High velocity = emerging trend.
        """
        # Would track reply rate over time
        # High velocity threads often contain alpha
        return 0.5  # Placeholder