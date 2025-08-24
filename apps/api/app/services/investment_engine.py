"""Investment Decision Engine - Core intelligence for investment recommendations."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from ..models import Asset, Price
from .technical_indicators import TechnicalIndicators
from .fundamental_analysis import FundamentalAnalysis
from .asset_classifier import AssetClassifier
from .strategy import StrategyService

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels."""
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


@dataclass
class InvestmentSignal:
    """Individual investment signal from a specific source."""
    source: str
    strength: SignalStrength
    confidence: float  # 0-1
    rationale: str
    data_points: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestmentRecommendation:
    """Comprehensive investment recommendation."""
    symbol: str
    action: SignalStrength
    confidence_score: float  # 0-100
    investment_score: float  # 0-100
    risk_score: float  # 0-100
    horizon: InvestmentHorizon
    target_allocation: float  # Percentage of portfolio
    entry_price_range: Tuple[float, float]
    exit_price_target: Optional[float]
    stop_loss: Optional[float]
    signals: List[InvestmentSignal]
    rationale: str
    risks: List[str]
    catalysts: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class InvestmentDecisionEngine:
    """
    Core engine for making investment decisions based on multiple data sources.
    Focuses on long-term value investing with risk management.
    """
    
    def __init__(self, db: Session):
        """Initialize the investment decision engine."""
        self.db = db
        self.fundamental_analyzer = FundamentalAnalysis(db)
        self.strategy_service = StrategyService(db)
        
        # Signal weights for long-term investing
        self.signal_weights = {
            'fundamental': 0.40,  # Most important for long-term
            'technical': 0.20,    # For timing entry/exit
            'sentiment': 0.15,    # Market sentiment
            'momentum': 0.15,     # Price momentum
            'risk': 0.10         # Risk factors
        }
    
    def analyze_investment_opportunity(
        self,
        symbol: str,
        horizon: InvestmentHorizon = InvestmentHorizon.LONG
    ) -> InvestmentRecommendation:
        """
        Analyze an investment opportunity and generate recommendation.
        
        Args:
            symbol: Asset symbol
            horizon: Investment time horizon
            
        Returns:
            Comprehensive investment recommendation
        """
        try:
            # Get asset data
            asset = self._get_asset_data(symbol)
            if not asset:
                raise ValueError(f"Asset {symbol} not found")
            
            # Collect signals from all sources
            signals = []
            
            # 1. Fundamental Analysis
            fundamental_signal = self._analyze_fundamentals(asset)
            if fundamental_signal:
                signals.append(fundamental_signal)
            
            # 2. Technical Analysis
            technical_signal = self._analyze_technicals(asset)
            if technical_signal:
                signals.append(technical_signal)
            
            # 3. Market Sentiment
            sentiment_signal = self._analyze_sentiment(asset)
            if sentiment_signal:
                signals.append(sentiment_signal)
            
            # 4. Price Momentum
            momentum_signal = self._analyze_momentum(asset)
            if momentum_signal:
                signals.append(momentum_signal)
            
            # 5. Risk Assessment
            risk_signal = self._analyze_risk(asset)
            if risk_signal:
                signals.append(risk_signal)
            
            # Aggregate signals into recommendation
            recommendation = self._aggregate_signals(asset, signals, horizon)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error analyzing investment opportunity for {symbol}: {e}")
            raise
    
    def _get_asset_data(self, symbol: str) -> Optional[Asset]:
        """Get asset with all relevant data."""
        return self.db.query(Asset).filter(
            Asset.symbol == symbol.upper()
        ).first()
    
    def _analyze_fundamentals(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze fundamental metrics."""
        try:
            fundamentals = self.fundamental_analyzer.get_asset_fundamentals(asset.symbol)
            
            if 'error' in fundamentals:
                return None
            
            # Evaluate fundamental strength
            score = 0
            rationale_points = []
            
            # P/E Ratio analysis
            if asset.pe_ratio:
                if asset.pe_ratio < 15:
                    score += 2
                    rationale_points.append("Attractive P/E ratio")
                elif asset.pe_ratio < 25:
                    score += 1
                    rationale_points.append("Reasonable P/E ratio")
                elif asset.pe_ratio > 35:
                    score -= 1
                    rationale_points.append("High P/E ratio")
            
            # Dividend yield
            if asset.dividend_yield:
                if asset.dividend_yield > 3:
                    score += 2
                    rationale_points.append(f"Strong dividend yield ({asset.dividend_yield:.1f}%)")
                elif asset.dividend_yield > 1.5:
                    score += 1
                    rationale_points.append(f"Moderate dividend yield ({asset.dividend_yield:.1f}%)")
            
            # ESG Score
            if asset.esg_score:
                if asset.esg_score > 70:
                    score += 1
                    rationale_points.append(f"High ESG score ({asset.esg_score:.0f})")
                elif asset.esg_score < 40:
                    score -= 1
                    rationale_points.append(f"Low ESG score ({asset.esg_score:.0f})")
            
            # Health assessment
            if 'health_assessment' in fundamentals:
                health = fundamentals['health_assessment']
                if health.get('overall') == 'excellent':
                    score += 2
                    rationale_points.append("Excellent financial health")
                elif health.get('overall') == 'good':
                    score += 1
                    rationale_points.append("Good financial health")
                elif health.get('overall') == 'poor':
                    score -= 2
                    rationale_points.append("Poor financial health")
            
            # Convert score to signal strength
            if score >= 3:
                strength = SignalStrength.STRONG_BUY
            elif score >= 1:
                strength = SignalStrength.BUY
            elif score >= -1:
                strength = SignalStrength.HOLD
            elif score >= -2:
                strength = SignalStrength.SELL
            else:
                strength = SignalStrength.STRONG_SELL
            
            confidence = min(0.9, 0.5 + (abs(score) * 0.1))
            
            return InvestmentSignal(
                source="fundamental",
                strength=strength,
                confidence=confidence,
                rationale="; ".join(rationale_points) if rationale_points else "Neutral fundamentals",
                data_points={
                    'pe_ratio': asset.pe_ratio,
                    'dividend_yield': asset.dividend_yield,
                    'esg_score': asset.esg_score,
                    'score': score
                }
            )
            
        except Exception as e:
            logger.error(f"Error in fundamental analysis: {e}")
            return None
    
    def _analyze_technicals(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze technical indicators."""
        try:
            # Get price history
            prices = self.db.query(Price).filter(
                Price.asset_id == asset.id
            ).order_by(Price.date.desc()).limit(200).all()
            
            if len(prices) < 50:
                return None
            
            price_series = pd.Series(
                [p.close for p in reversed(prices)],
                index=[p.date for p in reversed(prices)]
            )
            
            # Calculate indicators
            rsi = TechnicalIndicators.calculate_rsi(price_series, period=14)
            macd_data = TechnicalIndicators.calculate_macd(price_series)
            bb_data = TechnicalIndicators.calculate_bollinger_bands(price_series)
            sma_50 = TechnicalIndicators.calculate_sma(price_series, 50)
            sma_200 = TechnicalIndicators.calculate_sma(price_series, 200)
            
            score = 0
            rationale_points = []
            
            # RSI analysis
            current_rsi = rsi.iloc[-1]
            if current_rsi < 30:
                score += 2
                rationale_points.append(f"Oversold (RSI: {current_rsi:.0f})")
            elif current_rsi < 40:
                score += 1
                rationale_points.append(f"Near oversold (RSI: {current_rsi:.0f})")
            elif current_rsi > 70:
                score -= 2
                rationale_points.append(f"Overbought (RSI: {current_rsi:.0f})")
            
            # MACD analysis
            if len(macd_data['histogram']) > 1:
                macd_hist = macd_data['histogram'].iloc[-1]
                macd_prev = macd_data['histogram'].iloc[-2]
                if macd_hist > 0 and macd_prev <= 0:
                    score += 2
                    rationale_points.append("MACD bullish crossover")
                elif macd_hist < 0 and macd_prev >= 0:
                    score -= 2
                    rationale_points.append("MACD bearish crossover")
            
            # Moving average analysis
            current_price = price_series.iloc[-1]
            if current_price > sma_50.iloc[-1] > sma_200.iloc[-1]:
                score += 1
                rationale_points.append("Price above moving averages (uptrend)")
            elif current_price < sma_50.iloc[-1] < sma_200.iloc[-1]:
                score -= 1
                rationale_points.append("Price below moving averages (downtrend)")
            
            # Bollinger Bands
            if current_price < bb_data['lower'].iloc[-1]:
                score += 1
                rationale_points.append("Price at lower Bollinger Band")
            elif current_price > bb_data['upper'].iloc[-1]:
                score -= 1
                rationale_points.append("Price at upper Bollinger Band")
            
            # Convert score to signal
            if score >= 3:
                strength = SignalStrength.STRONG_BUY
            elif score >= 1:
                strength = SignalStrength.BUY
            elif score >= -1:
                strength = SignalStrength.HOLD
            elif score >= -2:
                strength = SignalStrength.SELL
            else:
                strength = SignalStrength.STRONG_SELL
            
            confidence = min(0.8, 0.4 + (abs(score) * 0.1))
            
            return InvestmentSignal(
                source="technical",
                strength=strength,
                confidence=confidence,
                rationale="; ".join(rationale_points) if rationale_points else "Neutral technicals",
                data_points={
                    'rsi': float(current_rsi),
                    'price': float(current_price),
                    'sma_50': float(sma_50.iloc[-1]),
                    'sma_200': float(sma_200.iloc[-1]),
                    'score': score
                }
            )
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return None
    
    def _analyze_sentiment(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze market sentiment."""
        # Simplified sentiment based on sector and market cap
        # In production, integrate with news sentiment analysis
        
        score = 0
        rationale_points = []
        
        # Sector sentiment (simplified)
        bullish_sectors = ['Technology', 'Healthcare', 'Consumer']
        bearish_sectors = ['Energy', 'Utilities']
        
        if asset.sector in bullish_sectors:
            score += 1
            rationale_points.append(f"Positive sector sentiment ({asset.sector})")
        elif asset.sector in bearish_sectors:
            score -= 1
            rationale_points.append(f"Negative sector sentiment ({asset.sector})")
        
        # Market cap preference (quality bias)
        if asset.market_cap and asset.market_cap > 10_000_000_000:
            score += 1
            rationale_points.append("Large-cap stability")
        
        # Default neutral sentiment
        strength = SignalStrength.HOLD
        if score > 0:
            strength = SignalStrength.BUY
        elif score < 0:
            strength = SignalStrength.SELL
        
        return InvestmentSignal(
            source="sentiment",
            strength=strength,
            confidence=0.5,
            rationale="; ".join(rationale_points) if rationale_points else "Neutral market sentiment",
            data_points={'score': score}
        )
    
    def _analyze_momentum(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze price momentum."""
        try:
            prices = self.db.query(Price).filter(
                Price.asset_id == asset.id
            ).order_by(Price.date.desc()).limit(60).all()
            
            if len(prices) < 30:
                return None
            
            # Calculate returns over different periods
            current_price = prices[0].close
            price_1m_ago = prices[min(20, len(prices)-1)].close
            price_3m_ago = prices[min(59, len(prices)-1)].close
            
            return_1m = (current_price - price_1m_ago) / price_1m_ago * 100
            return_3m = (current_price - price_3m_ago) / price_3m_ago * 100
            
            score = 0
            rationale_points = []
            
            # 1-month momentum
            if return_1m > 10:
                score += 2
                rationale_points.append(f"Strong 1-month momentum ({return_1m:.1f}%)")
            elif return_1m > 5:
                score += 1
                rationale_points.append(f"Positive 1-month momentum ({return_1m:.1f}%)")
            elif return_1m < -10:
                score -= 2
                rationale_points.append(f"Weak 1-month momentum ({return_1m:.1f}%)")
            
            # 3-month momentum
            if return_3m > 20:
                score += 1
                rationale_points.append(f"Strong 3-month trend ({return_3m:.1f}%)")
            elif return_3m < -20:
                score -= 1
                rationale_points.append(f"Weak 3-month trend ({return_3m:.1f}%)")
            
            # Convert to signal
            if score >= 2:
                strength = SignalStrength.BUY
            elif score <= -2:
                strength = SignalStrength.SELL
            else:
                strength = SignalStrength.HOLD
            
            return InvestmentSignal(
                source="momentum",
                strength=strength,
                confidence=0.6,
                rationale="; ".join(rationale_points) if rationale_points else "Neutral momentum",
                data_points={
                    'return_1m': return_1m,
                    'return_3m': return_3m,
                    'score': score
                }
            )
            
        except Exception as e:
            logger.error(f"Error in momentum analysis: {e}")
            return None
    
    def _analyze_risk(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze investment risks."""
        score = 0
        rationale_points = []
        risk_factors = []
        
        # Volatility risk
        if asset.volatility_30d:
            if asset.volatility_30d > 0.5:
                score -= 2
                risk_factors.append("High volatility")
            elif asset.volatility_30d > 0.3:
                score -= 1
                risk_factors.append("Moderate volatility")
            else:
                score += 1
                rationale_points.append("Low volatility")
        
        # Valuation risk
        if asset.pe_ratio and asset.pe_ratio > 40:
            score -= 1
            risk_factors.append("High valuation risk")
        
        # Concentration risk
        if asset.sector == 'Technology' and asset.market_cap and asset.market_cap > 1_000_000_000_000:
            score -= 1
            risk_factors.append("Mega-cap tech concentration")
        
        # Convert to signal
        if score >= 0:
            strength = SignalStrength.BUY
            rationale = "; ".join(rationale_points) if rationale_points else "Acceptable risk profile"
        else:
            strength = SignalStrength.HOLD
            rationale = "Risk factors: " + "; ".join(risk_factors)
        
        return InvestmentSignal(
            source="risk",
            strength=strength,
            confidence=0.7,
            rationale=rationale,
            data_points={
                'volatility': asset.volatility_30d,
                'risk_factors': risk_factors,
                'score': score
            }
        )
    
    def _aggregate_signals(
        self,
        asset: Asset,
        signals: List[InvestmentSignal],
        horizon: InvestmentHorizon
    ) -> InvestmentRecommendation:
        """Aggregate all signals into final recommendation."""
        
        # Calculate weighted scores
        signal_scores = {
            SignalStrength.STRONG_BUY: 2,
            SignalStrength.BUY: 1,
            SignalStrength.HOLD: 0,
            SignalStrength.SELL: -1,
            SignalStrength.STRONG_SELL: -2
        }
        
        total_score = 0
        total_confidence = 0
        total_weight = 0
        
        for signal in signals:
            weight = self.signal_weights.get(signal.source, 0.1)
            score = signal_scores[signal.strength]
            
            total_score += score * weight * signal.confidence
            total_confidence += signal.confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            final_score = total_score / total_weight
            avg_confidence = (total_confidence / total_weight) * 100
        else:
            final_score = 0
            avg_confidence = 50
        
        # Determine final action
        if final_score >= 1.5:
            action = SignalStrength.STRONG_BUY
        elif final_score >= 0.5:
            action = SignalStrength.BUY
        elif final_score >= -0.5:
            action = SignalStrength.HOLD
        elif final_score >= -1.5:
            action = SignalStrength.SELL
        else:
            action = SignalStrength.STRONG_SELL
        
        # Calculate investment score (0-100)
        investment_score = 50 + (final_score * 25)
        investment_score = max(0, min(100, investment_score))
        
        # Calculate risk score based on volatility and other factors
        risk_score = 50
        if asset.volatility_30d:
            risk_score = min(100, asset.volatility_30d * 200)
        
        # Determine target allocation based on scores
        if action in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
            if investment_score > 75 and risk_score < 50:
                target_allocation = 0.10  # 10% for high conviction, low risk
            elif investment_score > 60:
                target_allocation = 0.05  # 5% for moderate conviction
            else:
                target_allocation = 0.03  # 3% for low conviction
        else:
            target_allocation = 0.0
        
        # Get current price for entry/exit calculations
        latest_price = self.db.query(Price).filter(
            Price.asset_id == asset.id
        ).order_by(Price.date.desc()).first()
        
        current_price = latest_price.close if latest_price else 100
        
        # Calculate entry price range
        if action in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
            entry_low = current_price * 0.98  # 2% below current
            entry_high = current_price * 1.02  # 2% above current
        else:
            entry_low = current_price
            entry_high = current_price
        
        # Set targets based on horizon
        if horizon == InvestmentHorizon.LONG:
            exit_target = current_price * 1.30  # 30% gain target
            stop_loss = current_price * 0.85   # 15% stop loss
        elif horizon == InvestmentHorizon.MEDIUM:
            exit_target = current_price * 1.15  # 15% gain target
            stop_loss = current_price * 0.90   # 10% stop loss
        else:
            exit_target = current_price * 1.08  # 8% gain target
            stop_loss = current_price * 0.95   # 5% stop loss
        
        # Generate comprehensive rationale
        rationale = self._generate_rationale(asset, signals, action, investment_score)
        
        # Identify risks and catalysts
        risks = self._identify_risks(asset, signals)
        catalysts = self._identify_catalysts(asset, signals)
        
        return InvestmentRecommendation(
            symbol=asset.symbol,
            action=action,
            confidence_score=avg_confidence,
            investment_score=investment_score,
            risk_score=risk_score,
            horizon=horizon,
            target_allocation=target_allocation,
            entry_price_range=(entry_low, entry_high),
            exit_price_target=exit_target if action != SignalStrength.HOLD else None,
            stop_loss=stop_loss if action != SignalStrength.HOLD else None,
            signals=signals,
            rationale=rationale,
            risks=risks,
            catalysts=catalysts,
            metadata={
                'sector': asset.sector,
                'market_cap': asset.market_cap,
                'analysis_date': datetime.now().isoformat()
            }
        )
    
    def _generate_rationale(
        self,
        asset: Asset,
        signals: List[InvestmentSignal],
        action: SignalStrength,
        investment_score: float
    ) -> str:
        """Generate human-readable investment rationale."""
        
        rationale_parts = []
        
        # Overall recommendation
        if action == SignalStrength.STRONG_BUY:
            rationale_parts.append(f"Strong buy recommendation for {asset.symbol} with {investment_score:.0f}% investment score.")
        elif action == SignalStrength.BUY:
            rationale_parts.append(f"Buy recommendation for {asset.symbol} with {investment_score:.0f}% investment score.")
        elif action == SignalStrength.HOLD:
            rationale_parts.append(f"Hold recommendation for {asset.symbol}. No action needed at current levels.")
        elif action == SignalStrength.SELL:
            rationale_parts.append(f"Consider reducing position in {asset.symbol}.")
        else:
            rationale_parts.append(f"Strong sell recommendation for {asset.symbol}. Exit position.")
        
        # Add key signal rationales
        for signal in signals:
            if signal.confidence > 0.6 and signal.strength != SignalStrength.HOLD:
                rationale_parts.append(f"{signal.source.capitalize()}: {signal.rationale}")
        
        return " ".join(rationale_parts)
    
    def _identify_risks(self, asset: Asset, signals: List[InvestmentSignal]) -> List[str]:
        """Identify key investment risks."""
        risks = []
        
        # Check signal-specific risks
        for signal in signals:
            if 'risk_factors' in signal.data_points:
                risks.extend(signal.data_points['risk_factors'])
        
        # Add general risks
        if asset.pe_ratio and asset.pe_ratio > 30:
            risks.append("High valuation multiple")
        
        if asset.volatility_30d and asset.volatility_30d > 0.4:
            risks.append("High price volatility")
        
        if not asset.dividend_yield or asset.dividend_yield < 0.5:
            risks.append("No significant dividend support")
        
        return list(set(risks))  # Remove duplicates
    
    def _identify_catalysts(self, asset: Asset, signals: List[InvestmentSignal]) -> List[str]:
        """Identify potential positive catalysts."""
        catalysts = []
        
        # Check for positive factors
        if asset.sector == 'Technology':
            catalysts.append("Technology sector growth trends")
        
        if asset.esg_score and asset.esg_score > 70:
            catalysts.append("Strong ESG credentials attracting institutional investors")
        
        for signal in signals:
            if signal.source == 'technical' and 'Oversold' in signal.rationale:
                catalysts.append("Technical oversold bounce potential")
            elif signal.source == 'fundamental' and 'dividend' in signal.rationale.lower():
                catalysts.append("Attractive dividend yield")
        
        return catalysts
    
    def screen_opportunities(
        self,
        filters: Dict[str, Any],
        limit: int = 20
    ) -> List[InvestmentRecommendation]:
        """
        Screen for investment opportunities based on filters.
        
        Args:
            filters: Screening criteria
            limit: Maximum number of results
            
        Returns:
            List of investment recommendations
        """
        # Get assets matching basic filters
        query = self.db.query(Asset)
        
        if 'sectors' in filters:
            query = query.filter(Asset.sector.in_(filters['sectors']))
        
        if 'min_market_cap' in filters:
            query = query.filter(Asset.market_cap >= filters['min_market_cap'])
        
        if 'max_pe' in filters:
            query = query.filter(Asset.pe_ratio <= filters['max_pe'])
        
        if 'min_dividend' in filters:
            query = query.filter(Asset.dividend_yield >= filters['min_dividend'])
        
        assets = query.limit(limit * 2).all()  # Get extra for filtering
        
        # Analyze each asset
        recommendations = []
        for asset in assets:
            try:
                rec = self.analyze_investment_opportunity(
                    asset.symbol,
                    InvestmentHorizon.LONG
                )
                
                # Filter by minimum investment score
                min_score = filters.get('min_investment_score', 60)
                if rec.investment_score >= min_score:
                    recommendations.append(rec)
                    
                if len(recommendations) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Error analyzing {asset.symbol}: {e}")
                continue
        
        # Sort by investment score
        recommendations.sort(key=lambda x: x.investment_score, reverse=True)
        
        return recommendations[:limit]