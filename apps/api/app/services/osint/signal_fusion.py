"""
Signal Fusion Engine
Combines signals from multiple OSINT sources to generate high-conviction trades
Implements cross-validation and confidence scoring
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of signals we process."""
    PRICE_MOMENTUM = "price_momentum"
    VOLUME_SPIKE = "volume_spike"
    INSIDER_BUYING = "insider_buying"
    INSIDER_SELLING = "insider_selling"
    SOCIAL_SENTIMENT = "social_sentiment"
    NEWS_SENTIMENT = "news_sentiment"
    REGULATORY_CATALYST = "regulatory_catalyst"
    PATENT_FILING = "patent_filing"
    CONGRESS_TRADE = "congress_trade"
    HEDGE_FUND_POSITION = "hedge_fund_position"
    OPTIONS_FLOW = "options_flow"
    TECHNICAL_BREAKOUT = "technical_breakout"
    EARNINGS_SURPRISE = "earnings_surprise"
    ANALYST_UPGRADE = "analyst_upgrade"
    SUPPLY_CHAIN_DISRUPTION = "supply_chain_disruption"


@dataclass
class Signal:
    """Individual signal from a data source."""
    source: str  # API or scraper that generated signal
    signal_type: SignalType
    symbol: str
    direction: str  # bullish, bearish, neutral
    strength: float  # 0-1 confidence score
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)
    expiry: Optional[datetime] = None  # When signal expires
    

@dataclass
class FusedSignal:
    """Combined signal with cross-validation."""
    symbol: str
    direction: str  # bullish, bearish, neutral
    conviction_score: float  # 0-1 overall confidence
    signal_count: int  # Number of confirming signals
    sources: List[str]  # Data sources confirming
    signal_types: List[SignalType]
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_horizon: str = "short"  # short, medium, long
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    

class SignalFusionEngine:
    """
    Fuses signals from multiple sources to generate high-conviction trades.
    The key to alpha: multiple independent signals pointing same direction.
    """
    
    # Signal weights by type (based on historical accuracy)
    SIGNAL_WEIGHTS = {
        SignalType.INSIDER_BUYING: 0.95,
        SignalType.CONGRESS_TRADE: 0.90,
        SignalType.HEDGE_FUND_POSITION: 0.85,
        SignalType.OPTIONS_FLOW: 0.80,
        SignalType.REGULATORY_CATALYST: 0.85,
        SignalType.PATENT_FILING: 0.75,
        SignalType.TECHNICAL_BREAKOUT: 0.70,
        SignalType.VOLUME_SPIKE: 0.65,
        SignalType.PRICE_MOMENTUM: 0.60,
        SignalType.EARNINGS_SURPRISE: 0.75,
        SignalType.ANALYST_UPGRADE: 0.55,
        SignalType.NEWS_SENTIMENT: 0.50,
        SignalType.SOCIAL_SENTIMENT: 0.45,
        SignalType.INSIDER_SELLING: -0.60,  # Negative weight
        SignalType.SUPPLY_CHAIN_DISRUPTION: -0.70
    }
    
    # Minimum signals required for different conviction levels
    MIN_SIGNALS_FOR_CONVICTION = {
        "high": 4,
        "medium": 3,
        "low": 2
    }
    
    def __init__(self):
        """Initialize fusion engine."""
        self.active_signals = []  # Current active signals
        self.signal_history = []  # Historical signals for backtesting
        self.fused_signals = []  # Generated fused signals
        self.performance_tracker = defaultdict(lambda: {"correct": 0, "total": 0})
        
    def add_signal(self, signal: Signal):
        """Add a new signal to the fusion engine."""
        # Set expiry if not provided (default 7 days)
        if not signal.expiry:
            signal.expiry = signal.timestamp + timedelta(days=7)
        
        self.active_signals.append(signal)
        
        # Clean expired signals
        self._clean_expired_signals()
        
        # Check if this creates new fusion opportunities
        self._check_fusion_opportunities(signal.symbol)
    
    def add_bulk_signals(self, signals: List[Signal]):
        """Add multiple signals at once."""
        for signal in signals:
            self.add_signal(signal)
    
    def _clean_expired_signals(self):
        """Remove expired signals from active list."""
        now = datetime.now()
        self.active_signals = [
            s for s in self.active_signals 
            if s.expiry > now
        ]
    
    def _check_fusion_opportunities(self, symbol: str):
        """
        Check if we have enough signals to create a fused signal.
        This is where the magic happens - finding convergence.
        """
        # Get all active signals for this symbol
        symbol_signals = [
            s for s in self.active_signals 
            if s.symbol == symbol
        ]
        
        if len(symbol_signals) < self.MIN_SIGNALS_FOR_CONVICTION["low"]:
            return
        
        # Group by direction
        bullish_signals = [s for s in symbol_signals if s.direction == "bullish"]
        bearish_signals = [s for s in symbol_signals if s.direction == "bearish"]
        
        # Check if we have consensus
        if len(bullish_signals) > len(bearish_signals) * 2:
            self._create_fused_signal(symbol, "bullish", bullish_signals)
        elif len(bearish_signals) > len(bullish_signals) * 2:
            self._create_fused_signal(symbol, "bearish", bearish_signals)
    
    def _create_fused_signal(
        self, 
        symbol: str, 
        direction: str, 
        signals: List[Signal]
    ) -> FusedSignal:
        """Create a fused signal from multiple confirming signals."""
        # Calculate conviction score
        conviction = self._calculate_conviction(signals)
        
        # Extract unique sources and types
        sources = list(set(s.source for s in signals))
        signal_types = list(set(s.signal_type for s in signals))
        
        # Estimate price targets
        current_price = self._get_current_price(symbol)
        entry_price = current_price
        
        if direction == "bullish":
            target_price = current_price * (1 + 0.05 * conviction)  # 5-25% based on conviction
            stop_loss = current_price * 0.92  # 8% stop loss
        else:
            target_price = current_price * (1 - 0.05 * conviction)
            stop_loss = current_price * 1.08
        
        # Determine time horizon
        time_horizon = self._determine_time_horizon(signal_types)
        
        fused = FusedSignal(
            symbol=symbol,
            direction=direction,
            conviction_score=conviction,
            signal_count=len(signals),
            sources=sources,
            signal_types=signal_types,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            time_horizon=time_horizon,
            metadata={
                "signal_details": [
                    {
                        "type": s.signal_type.value,
                        "strength": s.strength,
                        "source": s.source
                    }
                    for s in signals
                ]
            }
        )
        
        self.fused_signals.append(fused)
        logger.info(f"Created fused signal: {symbol} {direction} conviction={conviction:.2f}")
        
        return fused
    
    def _calculate_conviction(self, signals: List[Signal]) -> float:
        """
        Calculate overall conviction score for fused signal.
        Weighted average with bonuses for multiple sources.
        """
        if not signals:
            return 0.0
        
        # Base score from weighted average
        weighted_sum = 0
        weight_sum = 0
        
        for signal in signals:
            weight = abs(self.SIGNAL_WEIGHTS.get(signal.signal_type, 0.5))
            weighted_sum += signal.strength * weight
            weight_sum += weight
        
        base_score = weighted_sum / weight_sum if weight_sum > 0 else 0.5
        
        # Bonus for multiple independent sources
        unique_sources = len(set(s.source for s in signals))
        source_bonus = min(unique_sources * 0.05, 0.2)  # Max 20% bonus
        
        # Bonus for multiple signal types
        unique_types = len(set(s.signal_type for s in signals))
        type_bonus = min(unique_types * 0.03, 0.15)  # Max 15% bonus
        
        # Bonus for high-value signals
        has_insider = any(s.signal_type == SignalType.INSIDER_BUYING for s in signals)
        has_congress = any(s.signal_type == SignalType.CONGRESS_TRADE for s in signals)
        has_hedge_fund = any(s.signal_type == SignalType.HEDGE_FUND_POSITION for s in signals)
        
        high_value_bonus = 0
        if has_insider:
            high_value_bonus += 0.1
        if has_congress:
            high_value_bonus += 0.08
        if has_hedge_fund:
            high_value_bonus += 0.07
        
        # Combine all factors
        total_score = min(base_score + source_bonus + type_bonus + high_value_bonus, 1.0)
        
        return total_score
    
    def _determine_time_horizon(self, signal_types: List[SignalType]) -> str:
        """Determine investment time horizon based on signal types."""
        # Short-term signals
        short_term = [
            SignalType.PRICE_MOMENTUM,
            SignalType.VOLUME_SPIKE,
            SignalType.TECHNICAL_BREAKOUT,
            SignalType.OPTIONS_FLOW
        ]
        
        # Long-term signals
        long_term = [
            SignalType.PATENT_FILING,
            SignalType.REGULATORY_CATALYST,
            SignalType.HEDGE_FUND_POSITION
        ]
        
        short_count = sum(1 for st in signal_types if st in short_term)
        long_count = sum(1 for st in signal_types if st in long_term)
        
        if short_count > long_count * 2:
            return "short"  # 1-4 weeks
        elif long_count > short_count * 2:
            return "long"  # 3+ months
        else:
            return "medium"  # 1-3 months
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (placeholder)."""
        # In production, would fetch from API
        prices = {
            "AAPL": 195.50,
            "GOOGL": 157.25,
            "MSFT": 430.80,
            "TSLA": 242.50,
            "NVDA": 880.75
        }
        return prices.get(symbol, 100.0)
    
    def get_top_opportunities(
        self, 
        min_conviction: float = 0.7,
        direction_filter: Optional[str] = None
    ) -> List[FusedSignal]:
        """Get top trading opportunities based on conviction."""
        # Clean expired signals first
        self._clean_expired_signals()
        
        # Filter fused signals
        opportunities = [
            fs for fs in self.fused_signals
            if fs.conviction_score >= min_conviction
        ]
        
        if direction_filter:
            opportunities = [
                fs for fs in opportunities
                if fs.direction == direction_filter
            ]
        
        # Sort by conviction score
        opportunities.sort(key=lambda x: x.conviction_score, reverse=True)
        
        return opportunities
    
    def analyze_signal_convergence(self, symbol: str) -> Dict:
        """
        Analyze how signals are converging for a symbol.
        Provides detailed breakdown of all signals.
        """
        symbol_signals = [
            s for s in self.active_signals
            if s.symbol == symbol
        ]
        
        analysis = {
            "symbol": symbol,
            "total_signals": len(symbol_signals),
            "by_direction": {
                "bullish": len([s for s in symbol_signals if s.direction == "bullish"]),
                "bearish": len([s for s in symbol_signals if s.direction == "bearish"]),
                "neutral": len([s for s in symbol_signals if s.direction == "neutral"])
            },
            "by_type": {},
            "by_source": {},
            "avg_strength": 0,
            "consensus": "none",
            "conviction": 0
        }
        
        if not symbol_signals:
            return analysis
        
        # Analyze by type
        for signal in symbol_signals:
            sig_type = signal.signal_type.value
            if sig_type not in analysis["by_type"]:
                analysis["by_type"][sig_type] = {"count": 0, "avg_strength": []}
            analysis["by_type"][sig_type]["count"] += 1
            analysis["by_type"][sig_type]["avg_strength"].append(signal.strength)
        
        # Calculate averages
        for sig_type in analysis["by_type"]:
            strengths = analysis["by_type"][sig_type]["avg_strength"]
            analysis["by_type"][sig_type]["avg_strength"] = statistics.mean(strengths)
        
        # Analyze by source
        for signal in symbol_signals:
            source = signal.source
            if source not in analysis["by_source"]:
                analysis["by_source"][source] = 0
            analysis["by_source"][source] += 1
        
        # Calculate overall metrics
        analysis["avg_strength"] = statistics.mean([s.strength for s in symbol_signals])
        
        # Determine consensus
        bullish = analysis["by_direction"]["bullish"]
        bearish = analysis["by_direction"]["bearish"]
        
        if bullish > bearish * 2:
            analysis["consensus"] = "strong_bullish"
            analysis["conviction"] = self._calculate_conviction(
                [s for s in symbol_signals if s.direction == "bullish"]
            )
        elif bullish > bearish:
            analysis["consensus"] = "bullish"
            analysis["conviction"] = self._calculate_conviction(
                [s for s in symbol_signals if s.direction == "bullish"]
            ) * 0.8
        elif bearish > bullish * 2:
            analysis["consensus"] = "strong_bearish"
            analysis["conviction"] = self._calculate_conviction(
                [s for s in symbol_signals if s.direction == "bearish"]
            )
        elif bearish > bullish:
            analysis["consensus"] = "bearish"
            analysis["conviction"] = self._calculate_conviction(
                [s for s in symbol_signals if s.direction == "bearish"]
            ) * 0.8
        else:
            analysis["consensus"] = "mixed"
            analysis["conviction"] = 0.3
        
        return analysis
    
    def backtest_signal_accuracy(self) -> Dict:
        """
        Analyze historical accuracy of different signal types.
        Used to adjust weights over time.
        """
        accuracy = {}
        
        for signal_type in SignalType:
            tracker = self.performance_tracker[signal_type]
            if tracker["total"] > 0:
                accuracy[signal_type.value] = {
                    "accuracy": tracker["correct"] / tracker["total"],
                    "total_signals": tracker["total"],
                    "current_weight": self.SIGNAL_WEIGHTS.get(signal_type, 0.5)
                }
        
        return accuracy
    
    def update_signal_performance(
        self, 
        signal_type: SignalType, 
        was_correct: bool
    ):
        """Update performance tracking for a signal type."""
        self.performance_tracker[signal_type]["total"] += 1
        if was_correct:
            self.performance_tracker[signal_type]["correct"] += 1
        
        # Adjust weight based on performance (simple adaptive learning)
        total = self.performance_tracker[signal_type]["total"]
        if total >= 10:  # Need at least 10 samples
            accuracy = self.performance_tracker[signal_type]["correct"] / total
            
            # Adjust weight towards actual accuracy
            current_weight = self.SIGNAL_WEIGHTS.get(signal_type, 0.5)
            new_weight = current_weight * 0.9 + accuracy * 0.1  # Slow adjustment
            self.SIGNAL_WEIGHTS[signal_type] = new_weight
            
            logger.info(f"Updated {signal_type.value} weight: {current_weight:.3f} -> {new_weight:.3f}")
    
    def get_statistics(self) -> Dict:
        """Get statistics about signal fusion performance."""
        return {
            "active_signals": len(self.active_signals),
            "fused_signals": len(self.fused_signals),
            "unique_symbols": len(set(s.symbol for s in self.active_signals)),
            "signal_types": {
                st.value: len([s for s in self.active_signals if s.signal_type == st])
                for st in SignalType
            },
            "avg_conviction": statistics.mean([fs.conviction_score for fs in self.fused_signals])
                            if self.fused_signals else 0,
            "high_conviction_count": len([fs for fs in self.fused_signals 
                                         if fs.conviction_score >= 0.8])
        }