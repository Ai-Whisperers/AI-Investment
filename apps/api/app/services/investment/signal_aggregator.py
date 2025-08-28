"""Signal aggregation service for combining investment signals."""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class InvestmentHorizon(Enum):
    """Investment time horizons."""
    SHORT = "short"  # 1-3 months
    MEDIUM = "medium"  # 3-12 months
    LONG = "long"  # 1+ years


class SignalStrength(Enum):
    """Signal strength levels for investment decisions."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class InvestmentSignal:
    """Investment signal from a specific analysis type."""
    
    def __init__(
        self,
        signal_type: str,
        strength: SignalStrength,
        confidence: float,
        data: Dict[str, Any]
    ):
        self.signal_type = signal_type
        self.strength = strength
        self.confidence = confidence  # 0.0 to 1.0
        self.data = data
        self.timestamp = datetime.utcnow()


class SignalAggregator:
    """Service for aggregating multiple investment signals into decisions."""
    
    def __init__(self):
        """Initialize the signal aggregator."""
        # Default signal weights for long-term investing
        self.default_weights = {
            'fundamental': 0.40,  # Most important for long-term
            'technical': 0.20,    # For timing entry/exit
            'sentiment': 0.15,    # Market sentiment
            'momentum': 0.15,     # Price momentum
            'risk': 0.10         # Risk factors
        }
        
        # Adjusted weights by investment horizon
        self.horizon_weights = {
            InvestmentHorizon.SHORT: {
                'fundamental': 0.20,
                'technical': 0.35,
                'sentiment': 0.20,
                'momentum': 0.20,
                'risk': 0.05
            },
            InvestmentHorizon.MEDIUM: {
                'fundamental': 0.30,
                'technical': 0.25,
                'sentiment': 0.15,
                'momentum': 0.20,
                'risk': 0.10
            },
            InvestmentHorizon.LONG: {
                'fundamental': 0.45,
                'technical': 0.15,
                'sentiment': 0.10,
                'momentum': 0.15,
                'risk': 0.15
            }
        }
    
    def aggregate_signals(
        self,
        signals: List[InvestmentSignal],
        horizon: InvestmentHorizon = InvestmentHorizon.LONG
    ) -> Dict[str, Any]:
        """
        Aggregate multiple signals into an overall investment decision.
        
        Args:
            signals: List of investment signals from different analyzers
            horizon: Investment time horizon
            
        Returns:
            Aggregated decision with overall strength and confidence
        """
        if not signals:
            return {
                "overall_signal": SignalStrength.HOLD,
                "confidence": 0.0,
                "recommendation": "Insufficient data for analysis",
                "signal_breakdown": {}
            }
        
        # Get weights for the specified horizon
        weights = self.horizon_weights.get(horizon, self.default_weights)
        
        # Convert signal strengths to scores
        strength_scores = {
            SignalStrength.STRONG_BUY: 2.0,
            SignalStrength.BUY: 1.0,
            SignalStrength.HOLD: 0.0,
            SignalStrength.SELL: -1.0,
            SignalStrength.STRONG_SELL: -2.0
        }
        
        weighted_score = 0.0
        total_confidence = 0.0
        signal_breakdown = {}
        
        for signal in signals:
            signal_type = signal.signal_type
            if signal_type not in weights:
                continue
                
            weight = weights[signal_type]
            score = strength_scores.get(signal.strength, 0.0)
            
            # Weighted score considering both weight and confidence
            weighted_score += score * weight * signal.confidence
            total_confidence += weight * signal.confidence
            
            signal_breakdown[signal_type] = {
                "strength": signal.strength.value,
                "confidence": signal.confidence,
                "weight": weight,
                "contribution": score * weight * signal.confidence
            }
        
        # Normalize weighted score
        if total_confidence > 0:
            final_score = weighted_score / total_confidence
            overall_confidence = min(total_confidence, 1.0)
        else:
            final_score = 0.0
            overall_confidence = 0.0
        
        # Determine overall signal strength
        overall_signal = self._score_to_signal(final_score)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall_signal, 
            overall_confidence,
            horizon,
            signal_breakdown
        )
        
        return {
            "overall_signal": overall_signal,
            "confidence": overall_confidence,
            "score": final_score,
            "recommendation": recommendation,
            "signal_breakdown": signal_breakdown,
            "horizon": horizon.value
        }
    
    def _score_to_signal(self, score: float) -> SignalStrength:
        """Convert numerical score to signal strength."""
        if score >= 1.5:
            return SignalStrength.STRONG_BUY
        elif score >= 0.5:
            return SignalStrength.BUY
        elif score >= -0.5:
            return SignalStrength.HOLD
        elif score >= -1.5:
            return SignalStrength.SELL
        else:
            return SignalStrength.STRONG_SELL
    
    def _generate_recommendation(
        self,
        signal: SignalStrength,
        confidence: float,
        horizon: InvestmentHorizon,
        breakdown: Dict[str, Any]
    ) -> str:
        """Generate human-readable recommendation based on aggregated signals."""
        
        # Confidence qualifier
        if confidence >= 0.8:
            confidence_text = "High confidence"
        elif confidence >= 0.5:
            confidence_text = "Moderate confidence"
        else:
            confidence_text = "Low confidence"
        
        # Time horizon text
        horizon_text = {
            InvestmentHorizon.SHORT: "short-term (1-3 months)",
            InvestmentHorizon.MEDIUM: "medium-term (3-12 months)",
            InvestmentHorizon.LONG: "long-term (1+ years)"
        }.get(horizon, "long-term")
        
        # Base recommendation
        recommendations = {
            SignalStrength.STRONG_BUY: f"{confidence_text} strong buy signal for {horizon_text} investment",
            SignalStrength.BUY: f"{confidence_text} buy signal for {horizon_text} investment",
            SignalStrength.HOLD: f"{confidence_text} hold signal - maintain current position",
            SignalStrength.SELL: f"{confidence_text} sell signal - consider reducing position",
            SignalStrength.STRONG_SELL: f"{confidence_text} strong sell signal - exit position"
        }
        
        base_recommendation = recommendations.get(signal, "Neutral position recommended")
        
        # Add strongest contributing factors
        strong_signals = []
        weak_signals = []
        
        for signal_type, data in breakdown.items():
            if data['contribution'] > 0.3:
                strong_signals.append(signal_type)
            elif data['contribution'] < -0.3:
                weak_signals.append(signal_type)
        
        if strong_signals:
            base_recommendation += f". Strong positive signals from: {', '.join(strong_signals)}"
        if weak_signals:
            base_recommendation += f". Caution advised due to: {', '.join(weak_signals)}"
        
        return base_recommendation
    
    def calculate_position_size(
        self,
        signal_strength: SignalStrength,
        confidence: float,
        risk_tolerance: str = "moderate"
    ) -> float:
        """
        Calculate recommended position size based on signal and risk tolerance.
        
        Args:
            signal_strength: Overall signal strength
            confidence: Signal confidence (0.0 to 1.0)
            risk_tolerance: "conservative", "moderate", or "aggressive"
            
        Returns:
            Recommended position size as percentage of portfolio (0.0 to 1.0)
        """
        # Base position sizes by signal strength
        base_positions = {
            SignalStrength.STRONG_BUY: 0.15,
            SignalStrength.BUY: 0.10,
            SignalStrength.HOLD: 0.05,
            SignalStrength.SELL: 0.0,
            SignalStrength.STRONG_SELL: 0.0
        }
        
        # Risk tolerance multipliers
        risk_multipliers = {
            "conservative": 0.5,
            "moderate": 1.0,
            "aggressive": 1.5
        }
        
        base_size = base_positions.get(signal_strength, 0.05)
        risk_mult = risk_multipliers.get(risk_tolerance, 1.0)
        
        # Adjust by confidence
        confidence_mult = 0.5 + (confidence * 0.5)  # Range: 0.5 to 1.0
        
        # Calculate final position size
        position_size = base_size * risk_mult * confidence_mult
        
        # Cap at maximum position sizes
        max_positions = {
            "conservative": 0.10,  # 10% max
            "moderate": 0.15,      # 15% max
            "aggressive": 0.25     # 25% max
        }
        
        max_size = max_positions.get(risk_tolerance, 0.15)
        return min(position_size, max_size)
    
    def calculate_entry_exit_targets(
        self,
        current_price: float,
        signal_strength: SignalStrength,
        volatility: float,
        horizon: InvestmentHorizon
    ) -> Dict[str, float]:
        """
        Calculate entry and exit price targets.
        
        Args:
            current_price: Current asset price
            signal_strength: Overall signal strength
            volatility: Asset volatility (annualized)
            horizon: Investment time horizon
            
        Returns:
            Dictionary with entry, target, and stop-loss prices
        """
        # Adjust targets based on horizon and volatility
        horizon_multipliers = {
            InvestmentHorizon.SHORT: 0.5,
            InvestmentHorizon.MEDIUM: 1.0,
            InvestmentHorizon.LONG: 1.5
        }
        
        horizon_mult = horizon_multipliers.get(horizon, 1.0)
        volatility_adjusted = min(volatility * horizon_mult, 0.5)  # Cap at 50%
        
        # Calculate targets based on signal strength
        if signal_strength in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
            entry_price = current_price  # Buy at current or better
            target_price = current_price * (1 + volatility_adjusted * 2)  # 2x volatility upside
            stop_loss = current_price * (1 - volatility_adjusted * 0.5)  # 0.5x volatility downside
        elif signal_strength in [SignalStrength.SELL, SignalStrength.STRONG_SELL]:
            entry_price = current_price  # Sell at current or better
            target_price = current_price * (1 - volatility_adjusted)  # Downside target
            stop_loss = current_price * (1 + volatility_adjusted * 0.5)  # Upside stop
        else:  # HOLD
            entry_price = current_price * 0.98  # Small discount for entry
            target_price = current_price * (1 + volatility_adjusted)
            stop_loss = current_price * (1 - volatility_adjusted * 0.5)
        
        return {
            "entry_price": round(entry_price, 2),
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "risk_reward_ratio": abs((target_price - entry_price) / (entry_price - stop_loss))
            if (entry_price - stop_loss) != 0 else 0
        }