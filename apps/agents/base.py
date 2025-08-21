"""
Base classes and interfaces for AI agents system.
Follows the same patterns as the existing providers architecture.
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Generic, TypeVar
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SignalType(Enum):
    """Types of trading signals."""
    
    LONG_TERM = "long_term"          # 6-24 month holds
    SWING = "swing"                  # 1-4 week holds
    EXTREME = "extreme"              # High conviction, >30% expected return
    MOMENTUM = "momentum"            # Short-term momentum plays
    DIVERGENCE = "divergence"        # Smart money vs retail divergence


class SignalStrength(Enum):
    """Signal strength levels."""
    
    WEAK = "weak"                    # <60% confidence
    MEDIUM = "medium"                # 60-80% confidence  
    STRONG = "strong"                # 80-90% confidence
    EXTREME = "extreme"              # >90% confidence


class SourceType(Enum):
    """Data source types."""
    
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    CHAN = "4chan"
    TWITTER = "twitter"
    DISCORD = "discord"
    TELEGRAM = "telegram"


@dataclass
class RawContent:
    """Raw content from social platforms."""
    
    id: str
    source: SourceType
    platform_id: str
    title: Optional[str]
    text: str
    author: Optional[str]
    created_at: datetime
    engagement: Dict[str, Any]  # views, likes, comments, etc.
    url: Optional[str]
    metadata: Dict[str, Any]


@dataclass  
class ProcessedSignal:
    """Processed trading signal from AI analysis."""
    
    id: str
    ticker: str
    signal_type: SignalType
    strength: SignalStrength
    confidence: float  # 0.0 - 1.0
    expected_return: float  # Expected % return
    timeframe: str  # Expected holding period
    action: str  # BUY, SELL, HOLD
    
    # Analysis details
    thesis: str
    catalyst: str
    key_points: List[str]
    risks: List[str]
    
    # Source attribution
    sources: List[SourceType]
    source_count: int
    cross_platform_validation: bool
    
    # Timestamps
    created_at: datetime
    expires_at: Optional[datetime]
    
    # Metadata
    pattern_detected: Optional[str]
    sentiment_score: float
    momentum_score: float
    credibility_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            'id': self.id,
            'ticker': self.ticker,
            'signal_type': self.signal_type.value,
            'strength': self.strength.value,
            'confidence': self.confidence,
            'expected_return': self.expected_return,
            'timeframe': self.timeframe,
            'action': self.action,
            'thesis': self.thesis,
            'catalyst': self.catalyst,
            'key_points': self.key_points,
            'risks': self.risks,
            'sources': [s.value for s in self.sources],
            'source_count': self.source_count,
            'cross_platform_validation': self.cross_platform_validation,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'pattern_detected': self.pattern_detected,
            'sentiment_score': self.sentiment_score,
            'momentum_score': self.momentum_score,
            'credibility_score': self.credibility_score
        }


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class CollectionError(AgentError):
    """Raised when data collection fails."""
    
    def __init__(self, message: str, source: SourceType, retry_after: Optional[int] = None):
        super().__init__(message)
        self.source = source
        self.retry_after = retry_after


class ProcessingError(AgentError):
    """Raised when signal processing fails."""
    
    def __init__(self, message: str, content_id: str):
        super().__init__(message)
        self.content_id = content_id


class ValidationError(AgentError):
    """Raised when signal validation fails."""
    pass


class BaseCollector(ABC):
    """
    Abstract base class for social media collectors.
    Follows the same pattern as existing providers.
    """
    
    def __init__(self, source_type: SourceType, rate_limit_per_hour: int = 60):
        self.source_type = source_type
        self.rate_limit = rate_limit_per_hour
        self._request_count = 0
        self._last_request_time = 0.0
        self._error_count = 0
        self._success_count = 0
        
    @abstractmethod
    def get_collector_name(self) -> str:
        """Return the collector name."""
        pass
        
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate collector configuration."""
        pass
        
    @abstractmethod
    async def collect_content(self, **kwargs) -> List[RawContent]:
        """Collect raw content from the platform."""
        pass
        
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        return {
            "collector": self.get_collector_name(),
            "source": self.source_type.value,
            "requests": self._request_count,
            "successes": self._success_count,
            "errors": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "last_request": self._last_request_time,
            "rate_limit": self.rate_limit
        }
        
    def _check_rate_limit(self):
        """Check if we're within rate limits."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < (3600 / self.rate_limit):  # Convert to seconds
            sleep_time = (3600 / self.rate_limit) - time_since_last
            logger.warning(f"Rate limit reached for {self.source_type.value}, sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
            
    def _record_request(self):
        """Record request for statistics."""
        self._request_count += 1
        self._last_request_time = time.time()
        
    def _record_success(self):
        """Record successful request."""
        self._success_count += 1
        
    def _record_error(self):
        """Record failed request."""
        self._error_count += 1


class BaseProcessor(ABC, Generic[T]):
    """
    Abstract base class for content processors.
    """
    
    def __init__(self, name: str):
        self.name = name
        self._processing_time = 0.0
        self._items_processed = 0
        self._items_failed = 0
        
    @abstractmethod
    async def process(self, content: List[RawContent]) -> T:
        """Process raw content into structured output."""
        pass
        
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        return {
            "processor": self.name,
            "items_processed": self._items_processed,
            "items_failed": self._items_failed,
            "success_rate": self._items_processed / max(self._items_processed + self._items_failed, 1),
            "avg_processing_time": self._processing_time / max(self._items_processed, 1)
        }
        
    def _record_processing_start(self) -> float:
        """Record start of processing."""
        return time.time()
        
    def _record_processing_end(self, start_time: float, success: bool = True):
        """Record end of processing."""
        processing_time = time.time() - start_time
        self._processing_time += processing_time
        
        if success:
            self._items_processed += 1
        else:
            self._items_failed += 1


class ExtremePatternsDetector:
    """
    Detects patterns that historically lead to >30% returns.
    """
    
    EXTREME_PATTERNS = {
        "insider_language": {
            "keywords": ["screenshot this", "trust me", "I work at", "my source", "insider"],
            "confidence_boost": 0.2,
            "expected_return": 0.45
        },
        "meme_velocity": {
            "keywords": ["to the moon", "diamond hands", "HODL", "squeeze", "gamma"],
            "velocity_threshold": 5.0,  # 500% increase in mentions
            "expected_return": 0.60
        },
        "smart_money_divergence": {
            "institution_sentiment_threshold": 0.7,
            "retail_sentiment_threshold": -0.3,
            "expected_return": 0.35
        },
        "earnings_leak": {
            "keywords": ["beat", "miss", "guidance", "announcement", "earnings"],
            "timing_words": ["tomorrow", "monday", "next week"],
            "expected_return": 0.25
        }
    }
    
    @staticmethod
    def detect_pattern(content: RawContent) -> Optional[str]:
        """Detect if content matches extreme return patterns."""
        text_lower = content.text.lower()
        
        for pattern_name, pattern_config in ExtremePatternsDetector.EXTREME_PATTERNS.items():
            if "keywords" in pattern_config:
                keyword_matches = sum(1 for keyword in pattern_config["keywords"] 
                                    if keyword in text_lower)
                if keyword_matches >= 2:  # At least 2 keywords
                    return pattern_name
                    
        return None
        
    @staticmethod
    def calculate_pattern_confidence(pattern_name: str, content: RawContent) -> float:
        """Calculate confidence boost for detected pattern."""
        if pattern_name not in ExtremePatternsDetector.EXTREME_PATTERNS:
            return 0.0
            
        pattern_config = ExtremePatternsDetector.EXTREME_PATTERNS[pattern_name]
        return pattern_config.get("confidence_boost", 0.0)
        
    @staticmethod
    def get_expected_return(pattern_name: str) -> float:
        """Get expected return for pattern."""
        if pattern_name not in ExtremePatternsDetector.EXTREME_PATTERNS:
            return 0.0
            
        pattern_config = ExtremePatternsDetector.EXTREME_PATTERNS[pattern_name]
        return pattern_config.get("expected_return", 0.0)


class TickerExtractor:
    """
    Utility class for extracting stock tickers from text.
    """
    
    import re
    
    # Common words that match ticker pattern but aren't tickers
    FALSE_POSITIVES = {
        'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'NEW', 'OLD',
        'NYSE', 'NASDAQ', 'CEO', 'CFO', 'IPO', 'FDA', 'SEC', 'USA', 'USD',
        'LOL', 'WTF', 'ETF', 'SPY', 'QQQ', 'VTI', 'BTC', 'ETH'
    }
    
    TICKER_PATTERN = re.compile(r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{2,5})(?=\s|$|\.|,)')
    
    @staticmethod
    def extract_tickers(text: str, max_tickers: int = 10) -> List[str]:
        """Extract stock tickers from text."""
        if not text:
            return []
            
        matches = TickerExtractor.TICKER_PATTERN.findall(text.upper())
        tickers = []
        
        for match in matches:
            ticker = match[0] if match[0] else match[1]
            
            if (ticker not in TickerExtractor.FALSE_POSITIVES and 
                len(ticker) >= 2 and 
                ticker not in tickers):
                tickers.append(ticker)
                
        return tickers[:max_tickers]
        
    @staticmethod
    def validate_ticker(ticker: str) -> bool:
        """Validate if a string is likely a real ticker."""
        if not ticker or len(ticker) < 2 or len(ticker) > 5:
            return False
            
        if ticker in TickerExtractor.FALSE_POSITIVES:
            return False
            
        # Additional validation logic could go here
        # (e.g., checking against known ticker database)
        return True