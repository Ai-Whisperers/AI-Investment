"""Process signals for maximum alpha generation."""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.signals import Signal
from app.database import get_db
import logging

logger = logging.getLogger(__name__)


class SignalProcessor:
    """Process signals for maximum alpha >30% returns."""
    
    def __init__(self, db: Session):
        self.db = db
        self.existing_positions = []
        self.risk_limit = 0.20  # Max 20% in high-risk plays
        self.position_limits = {
            'extreme': 0.10,  # Max 10% for extreme signals
            'swing': 0.05,    # Max 5% for swing trades
            'long_term': 0.15  # Max 15% for long-term
        }
        
    async def process_signal(self, signal: Signal) -> Dict:
        """Decide how to act on signal for maximum returns."""
        
        # Calculate base allocation based on expected return
        if signal.expected_return > 0.50:  # >50% expected
            allocation = min(0.10, self.risk_limit)  # 10% position
        elif signal.expected_return > 0.30:  # >30% expected
            allocation = 0.05  # 5% position
        else:
            allocation = 0.02  # 2% position
            
        # Stack signals for mega-positions
        if self.has_confirming_signals(signal.ticker):
            allocation *= 1.5  # Increase by 50%
            logger.info(f"Stacking signal for {signal.ticker}, increased allocation to {allocation:.2%}")
            
        # Apply position type limits
        allocation = min(allocation, self.position_limits.get(signal.signal_type, 0.05))
        
        return {
            'action': 'BUY',
            'ticker': signal.ticker,
            'allocation': allocation,
            'confidence': signal.confidence,
            'stop_loss': -0.10,  # 10% stop loss
            'take_profit': signal.expected_return * 0.8,  # Take 80% of expected
            'timeframe': signal.timeframe,
            'sources': signal.sources
        }
    
    def has_confirming_signals(self, ticker: str) -> bool:
        """Check if we have multiple signals for the same ticker."""
        recent_signals = self.db.query(Signal).filter(
            Signal.ticker == ticker,
            Signal.executed == False,
            Signal.confidence > 0.7
        ).count()
        
        return recent_signals > 1
    
    async def evaluate_signal_quality(self, signal: Signal) -> float:
        """Evaluate signal quality based on pattern stack."""
        quality_score = signal.confidence
        
        # Boost score for multiple patterns
        if signal.pattern_stack:
            patterns = signal.pattern_stack if isinstance(signal.pattern_stack, list) else []
            quality_score *= (1 + 0.1 * len(patterns))  # 10% boost per pattern
            
        # Boost for extreme signals
        if signal.signal_type == 'extreme':
            quality_score *= 1.2
            
        # Boost for high meme velocity
        if signal.meme_velocity and signal.meme_velocity > 5:
            quality_score *= 1.3
            
        return min(quality_score, 1.0)  # Cap at 100%
    
    async def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """Calculate optimal position size based on Kelly Criterion."""
        # Simplified Kelly: f = (p*b - q) / b
        # p = probability of win, b = odds, q = probability of loss
        
        p = signal.confidence
        q = 1 - p
        b = signal.expected_return
        
        if b <= 0:
            return 0
            
        kelly_fraction = (p * b - q) / b
        
        # Apply safety factor (use 25% of Kelly)
        safe_fraction = kelly_fraction * 0.25
        
        # Apply limits
        safe_fraction = max(0.01, min(safe_fraction, 0.10))  # 1-10% range
        
        return portfolio_value * safe_fraction