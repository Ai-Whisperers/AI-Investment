"""Refactored investment engine using focused service classes."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import logging
from sqlalchemy.orm import Session

from ...models import Asset, Price
from .signal_analyzer import SignalAnalyzer, SignalStrength
from .signal_aggregator import SignalAggregator, InvestmentHorizon
from .recommendation_generator import RecommendationGenerator, InvestmentRecommendation

logger = logging.getLogger(__name__)


class InvestmentEngine:
    """
    Refactored investment engine that orchestrates specialized services.
    Follows Single Responsibility Principle with focused, composable services.
    """
    
    def __init__(self, db: Session):
        """Initialize the investment engine with service dependencies."""
        self.db = db
        self.signal_analyzer = SignalAnalyzer(db)
        self.signal_aggregator = SignalAggregator()
        self.recommendation_generator = RecommendationGenerator()
    
    def analyze_investment(
        self,
        symbol: str,
        horizon: InvestmentHorizon = InvestmentHorizon.LONG,
        risk_tolerance: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Analyze an investment opportunity using all available signals.
        
        Args:
            symbol: Asset symbol to analyze
            horizon: Investment time horizon
            risk_tolerance: Risk tolerance level
            
        Returns:
            Complete investment analysis and recommendation
        """
        try:
            # Get asset data
            asset = self._get_asset_data(symbol)
            if not asset:
                return {
                    "error": f"Asset {symbol} not found",
                    "recommendation": None
                }
            
            # Collect all signals
            signals = self._collect_signals(asset)
            
            if not signals:
                return {
                    "error": "Insufficient data for analysis",
                    "recommendation": None
                }
            
            # Aggregate signals
            aggregated = self.signal_aggregator.aggregate_signals(signals, horizon)
            
            # Calculate position sizing
            position_size = self.signal_aggregator.calculate_position_size(
                aggregated["overall_signal"],
                aggregated["confidence"],
                risk_tolerance
            )
            
            # Calculate price targets
            current_price = self._get_current_price(asset)
            volatility = self._calculate_volatility(asset)
            
            price_targets = self.signal_aggregator.calculate_entry_exit_targets(
                current_price,
                aggregated["overall_signal"],
                volatility,
                horizon
            )
            
            # Generate recommendation
            recommendation = self.recommendation_generator.generate_recommendation(
                asset,
                aggregated,
                price_targets,
                position_size
            )
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "analysis": {
                    "signals": {s.signal_type: s.strength.value for s in signals},
                    "aggregated": aggregated,
                    "price_targets": price_targets,
                    "position_size": position_size,
                    "risk_tolerance": risk_tolerance
                },
                "recommendation": recommendation.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing investment for {symbol}: {e}")
            return {
                "error": str(e),
                "recommendation": None
            }
    
    def screen_opportunities(
        self,
        symbols: Optional[List[str]] = None,
        min_confidence: float = 0.6,
        horizon: InvestmentHorizon = InvestmentHorizon.LONG,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Screen multiple assets for investment opportunities.
        
        Args:
            symbols: List of symbols to screen (None for all)
            min_confidence: Minimum confidence threshold
            horizon: Investment time horizon
            limit: Maximum number of recommendations
            
        Returns:
            List of investment opportunities sorted by attractiveness
        """
        opportunities = []
        
        # Get assets to analyze
        if symbols:
            assets = self.db.query(Asset).filter(Asset.symbol.in_(symbols)).all()
        else:
            assets = self.db.query(Asset).limit(50).all()  # Limit for performance
        
        for asset in assets:
            try:
                # Analyze each asset
                analysis = self.analyze_investment(
                    asset.symbol,
                    horizon,
                    "moderate"
                )
                
                if "error" not in analysis and analysis.get("recommendation"):
                    rec = analysis["recommendation"]
                    confidence = rec.get("confidence", 0)
                    
                    if confidence >= min_confidence:
                        opportunities.append({
                            "symbol": asset.symbol,
                            "name": asset.name,
                            "sector": asset.sector,
                            "confidence": confidence,
                            "recommendation": rec.get("recommendation"),
                            "position_size": rec.get("position_size"),
                            "target_price": rec.get("target_price"),
                            "analysis": analysis
                        })
                        
            except Exception as e:
                logger.error(f"Error screening {asset.symbol}: {e}")
                continue
        
        # Sort by confidence and return top opportunities
        opportunities.sort(key=lambda x: x["confidence"], reverse=True)
        return opportunities[:limit]
    
    def generate_portfolio_allocation(
        self,
        symbols: List[str],
        portfolio_size: float = 1000000,
        risk_tolerance: str = "moderate",
        horizon: InvestmentHorizon = InvestmentHorizon.LONG
    ) -> Dict[str, Any]:
        """
        Generate portfolio allocation recommendations.
        
        Args:
            symbols: List of symbols to consider
            portfolio_size: Total portfolio value
            risk_tolerance: Risk tolerance level
            horizon: Investment horizon
            
        Returns:
            Portfolio allocation recommendations
        """
        recommendations = []
        
        for symbol in symbols:
            try:
                analysis = self.analyze_investment(symbol, horizon, risk_tolerance)
                
                if "error" not in analysis and analysis.get("recommendation"):
                    rec_dict = analysis["recommendation"]
                    
                    # Create recommendation object
                    rec = InvestmentRecommendation(
                        symbol=symbol,
                        recommendation=rec_dict.get("recommendation", ""),
                        confidence=rec_dict.get("confidence", 0),
                        target_price=rec_dict.get("target_price"),
                        stop_loss=rec_dict.get("stop_loss"),
                        horizon=horizon,
                        position_size=rec_dict.get("position_size", 0),
                        rationale=rec_dict.get("rationale", ""),
                        risks=rec_dict.get("risks", []),
                        catalysts=rec_dict.get("catalysts", [])
                    )
                    recommendations.append(rec)
                    
            except Exception as e:
                logger.error(f"Error analyzing {symbol} for portfolio: {e}")
                continue
        
        # Generate portfolio recommendations
        portfolio = self.recommendation_generator.generate_portfolio_recommendations(
            recommendations,
            portfolio_size,
            max_positions=20
        )
        
        return portfolio
    
    def _get_asset_data(self, symbol: str) -> Optional[Asset]:
        """Get asset data from database."""
        return self.db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    
    def _collect_signals(self, asset: Asset) -> List:
        """Collect all available signals for an asset."""
        signals = []
        
        # Fundamental analysis
        fundamental_signal = self.signal_analyzer.analyze_fundamentals(asset)
        if fundamental_signal:
            signals.append(fundamental_signal)
        
        # Technical analysis
        technical_signal = self.signal_analyzer.analyze_technicals(asset)
        if technical_signal:
            signals.append(technical_signal)
        
        # Momentum analysis
        momentum_signal = self.signal_analyzer.analyze_momentum(asset)
        if momentum_signal:
            signals.append(momentum_signal)
        
        # Risk analysis
        risk_signal = self.signal_analyzer.analyze_risk(asset)
        if risk_signal:
            signals.append(risk_signal)
        
        # Note: Sentiment analysis would be added here when available
        
        return signals
    
    def _get_current_price(self, asset: Asset) -> float:
        """Get current price for an asset."""
        latest_price = self.db.query(Price).filter(
            Price.asset_id == asset.id
        ).order_by(Price.date.desc()).first()
        
        return latest_price.close if latest_price else 0.0
    
    def _calculate_volatility(self, asset: Asset) -> float:
        """Calculate asset volatility."""
        from datetime import timedelta
        import pandas as pd
        
        try:
            # Get 1 year of price data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=252)
            
            prices = self.db.query(Price).filter(
                Price.asset_id == asset.id,
                Price.date >= start_date
            ).order_by(Price.date).all()
            
            if len(prices) < 30:
                return 0.25  # Default volatility
            
            price_series = pd.Series([p.close for p in prices])
            returns = price_series.pct_change().dropna()
            
            # Annualized volatility
            volatility = returns.std() * (252 ** 0.5)
            return min(volatility, 0.5)  # Cap at 50%
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {asset.symbol}: {e}")
            return 0.25  # Default volatility