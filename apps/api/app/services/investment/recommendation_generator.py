"""Investment recommendation generation service."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging

from ...models import Asset

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels for investment decisions."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class InvestmentHorizon(Enum):
    """Investment time horizons."""
    SHORT = "short"  # 1-3 months
    MEDIUM = "medium"  # 3-12 months
    LONG = "long"  # 1+ years


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
        self.confidence = confidence
        self.data = data
        self.timestamp = datetime.utcnow()


class InvestmentRecommendation:
    """Complete investment recommendation for an asset."""
    
    def __init__(
        self,
        symbol: str,
        recommendation: str,
        confidence: float,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        horizon: InvestmentHorizon = InvestmentHorizon.LONG,
        position_size: float = 0.05,
        rationale: str = "",
        risks: Optional[List[str]] = None,
        catalysts: Optional[List[str]] = None
    ):
        self.symbol = symbol
        self.recommendation = recommendation
        self.confidence = confidence
        self.target_price = target_price
        self.stop_loss = stop_loss
        self.horizon = horizon
        self.position_size = position_size
        self.rationale = rationale
        self.risks = risks or []
        self.catalysts = catalysts or []
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary format."""
        return {
            "symbol": self.symbol,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "horizon": self.horizon.value,
            "position_size": self.position_size,
            "rationale": self.rationale,
            "risks": self.risks,
            "catalysts": self.catalysts,
            "timestamp": self.timestamp.isoformat()
        }


class RecommendationGenerator:
    """Service for generating investment recommendations."""
    
    def __init__(self):
        """Initialize the recommendation generator."""
        pass
    
    def generate_recommendation(
        self,
        asset: Asset,
        aggregated_signals: Dict[str, Any],
        price_targets: Dict[str, float],
        position_size: float
    ) -> InvestmentRecommendation:
        """
        Generate a complete investment recommendation.
        
        Args:
            asset: The asset being analyzed
            aggregated_signals: Aggregated signal analysis results
            price_targets: Entry, target, and stop-loss prices
            position_size: Recommended position size
            
        Returns:
            Complete investment recommendation
        """
        # Extract key information
        overall_signal = aggregated_signals.get("overall_signal", SignalStrength.HOLD)
        confidence = aggregated_signals.get("confidence", 0.0)
        horizon = InvestmentHorizon(aggregated_signals.get("horizon", "long"))
        signal_breakdown = aggregated_signals.get("signal_breakdown", {})
        
        # Generate rationale
        rationale = self._generate_rationale(
            asset,
            overall_signal,
            confidence,
            signal_breakdown
        )
        
        # Identify risks
        risks = self._identify_risks(asset, signal_breakdown)
        
        # Identify catalysts
        catalysts = self._identify_catalysts(asset, signal_breakdown)
        
        # Create recommendation text
        recommendation_text = aggregated_signals.get(
            "recommendation",
            "Hold - Insufficient data for strong recommendation"
        )
        
        return InvestmentRecommendation(
            symbol=asset.symbol,
            recommendation=recommendation_text,
            confidence=confidence,
            target_price=price_targets.get("target_price"),
            stop_loss=price_targets.get("stop_loss"),
            horizon=horizon,
            position_size=position_size,
            rationale=rationale,
            risks=risks,
            catalysts=catalysts
        )
    
    def _generate_rationale(
        self,
        asset: Asset,
        signal: SignalStrength,
        confidence: float,
        signal_breakdown: Dict[str, Any]
    ) -> str:
        """Generate detailed rationale for the recommendation."""
        rationale_parts = []
        
        # Opening statement
        if signal == SignalStrength.STRONG_BUY:
            rationale_parts.append(f"{asset.symbol} presents a compelling investment opportunity")
        elif signal == SignalStrength.BUY:
            rationale_parts.append(f"{asset.symbol} shows favorable investment characteristics")
        elif signal == SignalStrength.SELL:
            rationale_parts.append(f"{asset.symbol} exhibits concerning indicators")
        elif signal == SignalStrength.STRONG_SELL:
            rationale_parts.append(f"{asset.symbol} shows significant risks")
        else:
            rationale_parts.append(f"{asset.symbol} presents a neutral investment case")
        
        # Add confidence qualifier
        if confidence >= 0.8:
            rationale_parts.append("with high confidence based on multiple converging signals.")
        elif confidence >= 0.5:
            rationale_parts.append("with moderate confidence from our analysis.")
        else:
            rationale_parts.append("though conviction is limited by mixed signals.")
        
        # Detail key contributing factors
        strong_contributors = []
        weak_contributors = []
        
        for signal_type, data in signal_breakdown.items():
            contribution = data.get('contribution', 0)
            if contribution > 0.2:
                strong_contributors.append(self._describe_signal(signal_type, data))
            elif contribution < -0.2:
                weak_contributors.append(self._describe_signal(signal_type, data))
        
        if strong_contributors:
            rationale_parts.append("\n\nPositive factors include:")
            for factor in strong_contributors:
                rationale_parts.append(f"\n• {factor}")
        
        if weak_contributors:
            rationale_parts.append("\n\nConcerns include:")
            for factor in weak_contributors:
                rationale_parts.append(f"\n• {factor}")
        
        return " ".join(rationale_parts)
    
    def _describe_signal(self, signal_type: str, data: Dict[str, Any]) -> str:
        """Generate human-readable description of a signal."""
        strength = data.get('strength', 'neutral')
        confidence = data.get('confidence', 0)
        
        descriptions = {
            'fundamental': {
                'strong_buy': "Exceptional fundamental value with strong financials",
                'buy': "Solid fundamentals and attractive valuation",
                'hold': "Fair fundamental valuation",
                'sell': "Weak fundamentals or overvaluation concerns",
                'strong_sell': "Significant fundamental deterioration"
            },
            'technical': {
                'strong_buy': "Strong technical setup with bullish momentum",
                'buy': "Positive technical indicators and trend",
                'hold': "Neutral technical picture",
                'sell': "Negative technical breakdown",
                'strong_sell': "Severe technical weakness"
            },
            'momentum': {
                'strong_buy': "Exceptional price momentum and trend strength",
                'buy': "Positive momentum and upward trend",
                'hold': "Sideways price action",
                'sell': "Negative momentum developing",
                'strong_sell': "Strong downward momentum"
            },
            'risk': {
                'buy': "Low risk profile with stable volatility",
                'hold': "Moderate risk levels",
                'sell': "Elevated risk and high volatility"
            }
        }
        
        base_description = descriptions.get(signal_type, {}).get(strength, f"{signal_type} signal")
        
        # Add confidence qualifier
        if confidence >= 0.8:
            return f"{base_description} (high confidence)"
        elif confidence >= 0.5:
            return f"{base_description} (moderate confidence)"
        else:
            return f"{base_description} (low confidence)"
    
    def _identify_risks(
        self,
        asset: Asset,
        signal_breakdown: Dict[str, Any]
    ) -> List[str]:
        """Identify key risks for the investment."""
        risks = []
        
        # Check for weak signals
        for signal_type, data in signal_breakdown.items():
            strength = data.get('strength', '')
            if 'sell' in strength.lower():
                if signal_type == 'fundamental':
                    risks.append("Fundamental weakness or overvaluation")
                elif signal_type == 'technical':
                    risks.append("Technical breakdown risk")
                elif signal_type == 'momentum':
                    risks.append("Negative momentum could accelerate")
                elif signal_type == 'risk':
                    risks.append("High volatility and drawdown risk")
        
        # Add general market risks
        risks.append("General market volatility and systematic risk")
        
        # Sector-specific risks
        if asset.sector:
            if asset.sector == "Technology":
                risks.append("Technology sector rotation risk")
            elif asset.sector == "Financial":
                risks.append("Interest rate and credit risk")
            elif asset.sector == "Energy":
                risks.append("Commodity price volatility")
        
        return risks[:5]  # Limit to top 5 risks
    
    def _identify_catalysts(
        self,
        asset: Asset,
        signal_breakdown: Dict[str, Any]
    ) -> List[str]:
        """Identify potential catalysts for the investment."""
        catalysts = []
        
        # Check for strong signals
        for signal_type, data in signal_breakdown.items():
            strength = data.get('strength', '')
            if 'buy' in strength.lower():
                if signal_type == 'fundamental':
                    catalysts.append("Improving fundamentals and valuation re-rating potential")
                elif signal_type == 'technical':
                    catalysts.append("Technical breakout potential")
                elif signal_type == 'momentum':
                    catalysts.append("Momentum acceleration could drive further gains")
        
        # Add general catalysts
        if any('buy' in data.get('strength', '').lower() for data in signal_breakdown.values()):
            catalysts.append("Potential for analyst upgrades")
            catalysts.append("Sector rotation into undervalued names")
        
        return catalysts[:5]  # Limit to top 5 catalysts
    
    def generate_portfolio_recommendations(
        self,
        recommendations: List[InvestmentRecommendation],
        portfolio_size: float = 1000000,
        max_positions: int = 20
    ) -> Dict[str, Any]:
        """
        Generate portfolio-level recommendations.
        
        Args:
            recommendations: List of individual asset recommendations
            portfolio_size: Total portfolio value
            max_positions: Maximum number of positions
            
        Returns:
            Portfolio allocation recommendations
        """
        # Sort by confidence and signal strength
        sorted_recs = sorted(
            recommendations,
            key=lambda x: (x.confidence, x.recommendation.count('buy')),
            reverse=True
        )
        
        # Select top recommendations up to max positions
        selected = sorted_recs[:max_positions]
        
        # Calculate allocations
        allocations = []
        total_allocation = 0
        
        for rec in selected:
            if 'buy' in rec.recommendation.lower():
                allocation = rec.position_size * portfolio_size
                allocations.append({
                    "symbol": rec.symbol,
                    "allocation": allocation,
                    "percentage": rec.position_size * 100,
                    "shares": int(allocation / (rec.target_price or 100)),
                    "confidence": rec.confidence
                })
                total_allocation += rec.position_size
        
        # Cash allocation
        cash_allocation = 1.0 - total_allocation
        
        return {
            "recommended_positions": len(allocations),
            "total_allocation": total_allocation,
            "cash_allocation": cash_allocation,
            "allocations": allocations,
            "portfolio_value": portfolio_size,
            "generated_at": datetime.utcnow().isoformat()
        }