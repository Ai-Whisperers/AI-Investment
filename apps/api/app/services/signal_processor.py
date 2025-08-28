"""Process signals for maximum alpha generation."""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Signal, Asset, Price, ExtremeEvent, PatternDetection
from app.services.pattern_recognition import (
    MultiLayerAlphaDetection,
    AsymmetryExploiter,
    MemeVelocityTracker
)
from app.services.extreme_events import (
    ExtremeEventDetector,
    FortyEightHourStrategy,
    SmartMoneyDivergence
)
import asyncio
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
            'long_term': 0.15,  # Max 15% for long-term
            'meme': 0.05,      # Max 5% for meme plays
            'divergence': 0.07  # Max 7% for divergence plays
        }
        
        # Initialize detection modules
        self.multi_layer = MultiLayerAlphaDetection(db)
        self.asymmetry = AsymmetryExploiter(db)
        self.meme_tracker = MemeVelocityTracker(db)
        self.extreme_detector = ExtremeEventDetector(db)
        self.forty_eight = FortyEightHourStrategy(db)
        self.divergence = SmartMoneyDivergence(db)
        
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
    
    async def scan_all_sources(self, data: Dict[str, Any]) -> List[Signal]:
        """Scan all data sources for extreme alpha signals."""
        signals = []
        tasks = []
        
        # Run all scanners in parallel
        for ticker in data.get('tickers', []):
            ticker_data = data.get(ticker, {})
            
            tasks.extend([
                self.multi_layer.detect_alpha_event(ticker, ticker_data),
                self.extreme_detector.scan_for_extremes(ticker, ticker_data),
                self.meme_tracker.calculate_meme_velocity(ticker, ticker_data.get('platforms', {}))
            ])
        
        # Process early sources
        if 'early_sources' in data:
            tasks.append(self.asymmetry.find_early_signals(data['early_sources']))
            
        if 'chan_posts' in data:
            tasks.append(self.forty_eight.detect_early_signal(data['chan_posts']))
            
        # Run divergence analysis
        if 'sp500_tickers' in data:
            tasks.append(self.divergence.analyze_divergence(data['sp500_tickers'][:20]))
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect signals
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in signal detection: {result}")
                continue
                
            if result and isinstance(result, dict) and 'signal_id' in result:
                signal = self.db.query(Signal).filter_by(id=result['signal_id']).first()
                if signal:
                    signals.append(signal)
            elif isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and 'signal_id' in item:
                        signal = self.db.query(Signal).filter_by(id=item['signal_id']).first()
                        if signal:
                            signals.append(signal)
        
        return signals
    
    def get_active_signals(self, limit: int = 20) -> List[Dict]:
        """Get active signals sorted by confidence."""
        signals = self.db.query(Signal).filter(
            Signal.executed == False,
            Signal.created_at > datetime.utcnow() - timedelta(days=7)
        ).order_by(Signal.confidence.desc()).limit(limit).all()
        
        return [signal.to_dict() for signal in signals]
    
    def get_signal_performance(self) -> Dict[str, Any]:
        """Get overall signal performance metrics."""
        closed_signals = self.db.query(Signal).filter(
            Signal.executed == True,
            Signal.exit_time != None
        ).all()
        
        if not closed_signals:
            return {
                'total_signals': 0,
                'win_rate': 0,
                'average_return': 0,
                'best_return': 0,
                'worst_return': 0,
                'total_return': 0
            }
        
        returns = [s.result for s in closed_signals if s.result is not None]
        wins = [r for r in returns if r > 0]
        
        return {
            'total_signals': len(closed_signals),
            'win_rate': len(wins) / len(returns) if returns else 0,
            'average_return': sum(returns) / len(returns) if returns else 0,
            'best_return': max(returns) if returns else 0,
            'worst_return': min(returns) if returns else 0,
            'total_return': sum(returns) if returns else 0
        }