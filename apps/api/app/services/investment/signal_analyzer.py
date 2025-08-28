"""Signal analysis service for investment decisions."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import pandas as pd
from sqlalchemy.orm import Session

from ...models import Asset, Price
from ...services.technical_indicators import TechnicalIndicators
from ...services.fundamental_analysis import FundamentalAnalysis

logger = logging.getLogger(__name__)


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


class SignalAnalyzer:
    """Service for analyzing various investment signals."""
    
    def __init__(self, db: Session):
        """Initialize the signal analyzer."""
        self.db = db
        self.fundamental_analyzer = FundamentalAnalysis(db)
    
    def analyze_fundamentals(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze fundamental indicators for investment decision."""
        try:
            # Get fundamental metrics
            metrics = self.fundamental_analyzer.get_fundamental_metrics(asset.symbol)
            if not metrics:
                return None
            
            # Score based on value investing principles
            score = 0
            confidence = 0.0
            reasons = []
            
            # P/E Ratio analysis
            pe_ratio = metrics.get('pe_ratio')
            if pe_ratio:
                if pe_ratio < 15:
                    score += 2
                    reasons.append(f"Low P/E ratio ({pe_ratio:.2f})")
                elif pe_ratio < 25:
                    score += 1
                    reasons.append(f"Moderate P/E ratio ({pe_ratio:.2f})")
                elif pe_ratio > 40:
                    score -= 2
                    reasons.append(f"High P/E ratio ({pe_ratio:.2f})")
                confidence += 0.2
            
            # P/B Ratio analysis
            pb_ratio = metrics.get('pb_ratio')
            if pb_ratio:
                if pb_ratio < 1.0:
                    score += 2
                    reasons.append(f"Trading below book value ({pb_ratio:.2f})")
                elif pb_ratio < 3.0:
                    score += 1
                    reasons.append(f"Reasonable P/B ratio ({pb_ratio:.2f})")
                elif pb_ratio > 5.0:
                    score -= 1
                    reasons.append(f"High P/B ratio ({pb_ratio:.2f})")
                confidence += 0.2
            
            # Dividend Yield
            dividend_yield = metrics.get('dividend_yield', 0)
            if dividend_yield > 0.03:  # 3%
                score += 1
                reasons.append(f"Attractive dividend yield ({dividend_yield*100:.2f}%)")
                confidence += 0.1
            
            # Debt to Equity
            debt_to_equity = metrics.get('debt_to_equity')
            if debt_to_equity is not None:
                if debt_to_equity < 0.5:
                    score += 1
                    reasons.append("Low debt levels")
                elif debt_to_equity > 2.0:
                    score -= 1
                    reasons.append("High debt levels")
                confidence += 0.15
            
            # ROE
            roe = metrics.get('roe')
            if roe:
                if roe > 0.15:  # 15%
                    score += 1
                    reasons.append(f"Strong ROE ({roe*100:.2f}%)")
                elif roe < 0.05:  # 5%
                    score -= 1
                    reasons.append(f"Weak ROE ({roe*100:.2f}%)")
                confidence += 0.15
            
            # Determine signal strength
            if score >= 4:
                strength = SignalStrength.STRONG_BUY
            elif score >= 2:
                strength = SignalStrength.BUY
            elif score >= -1:
                strength = SignalStrength.HOLD
            elif score >= -3:
                strength = SignalStrength.SELL
            else:
                strength = SignalStrength.STRONG_SELL
            
            return InvestmentSignal(
                signal_type="fundamental",
                strength=strength,
                confidence=min(confidence, 1.0),
                data={
                    "metrics": metrics,
                    "score": score,
                    "reasons": reasons
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing fundamentals for {asset.symbol}: {e}")
            return None
    
    def analyze_technicals(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze technical indicators for investment timing."""
        try:
            # Get price history
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=200)
            
            prices = self.db.query(Price).filter(
                Price.asset_id == asset.id,
                Price.date >= start_date
            ).order_by(Price.date).all()
            
            if len(prices) < 50:
                return None
            
            price_series = pd.Series([p.close for p in prices])
            
            score = 0
            confidence = 0.0
            indicators = {}
            
            # RSI Analysis
            rsi = TechnicalIndicators.calculate_rsi(price_series, period=14)
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
                indicators['rsi'] = current_rsi
                
                if current_rsi < 30:
                    score += 2  # Oversold
                    confidence += 0.3
                elif current_rsi < 40:
                    score += 1
                    confidence += 0.2
                elif current_rsi > 70:
                    score -= 2  # Overbought
                    confidence += 0.3
                elif current_rsi > 60:
                    score -= 1
                    confidence += 0.2
                else:
                    confidence += 0.1
            
            # MACD Analysis
            macd_data = TechnicalIndicators.calculate_macd(price_series)
            if 'histogram' in macd_data:
                histogram = macd_data['histogram']
                if len(histogram) > 0:
                    current_hist = histogram.iloc[-1]
                    prev_hist = histogram.iloc[-2] if len(histogram) > 1 else 0
                    
                    indicators['macd_histogram'] = current_hist
                    
                    # Bullish crossover
                    if current_hist > 0 and prev_hist <= 0:
                        score += 2
                        confidence += 0.3
                    # Bearish crossover
                    elif current_hist < 0 and prev_hist >= 0:
                        score -= 2
                        confidence += 0.3
                    # Trending
                    elif current_hist > prev_hist:
                        score += 1
                        confidence += 0.2
                    else:
                        score -= 1
                        confidence += 0.2
            
            # Moving Average Analysis
            sma_50 = price_series.rolling(window=50).mean()
            sma_200 = price_series.rolling(window=200).mean() if len(price_series) >= 200 else None
            
            current_price = price_series.iloc[-1]
            if not sma_50.empty:
                indicators['sma_50'] = sma_50.iloc[-1]
                
                if current_price > sma_50.iloc[-1]:
                    score += 1
                    confidence += 0.15
                else:
                    score -= 1
                    confidence += 0.15
            
            if sma_200 is not None and not sma_200.empty:
                indicators['sma_200'] = sma_200.iloc[-1]
                
                if sma_50.iloc[-1] > sma_200.iloc[-1]:
                    score += 1  # Golden cross territory
                    confidence += 0.15
                else:
                    score -= 1  # Death cross territory
                    confidence += 0.15
            
            # Determine signal strength
            if score >= 4:
                strength = SignalStrength.STRONG_BUY
            elif score >= 2:
                strength = SignalStrength.BUY
            elif score >= -1:
                strength = SignalStrength.HOLD
            elif score >= -3:
                strength = SignalStrength.SELL
            else:
                strength = SignalStrength.STRONG_SELL
            
            return InvestmentSignal(
                signal_type="technical",
                strength=strength,
                confidence=min(confidence, 1.0),
                data={
                    "indicators": indicators,
                    "score": score,
                    "price_trend": "bullish" if score > 0 else "bearish" if score < 0 else "neutral"
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing technicals for {asset.symbol}: {e}")
            return None
    
    def analyze_momentum(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze price momentum for trend following."""
        try:
            # Get price history
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365)
            
            prices = self.db.query(Price).filter(
                Price.asset_id == asset.id,
                Price.date >= start_date
            ).order_by(Price.date).all()
            
            if len(prices) < 30:
                return None
            
            score = 0
            confidence = 0.0
            momentum_data = {}
            
            # Calculate returns over different periods
            current_price = prices[-1].close
            
            # 1-month momentum
            if len(prices) >= 21:
                price_1m = prices[-21].close
                return_1m = (current_price - price_1m) / price_1m
                momentum_data['return_1m'] = return_1m
                
                if return_1m > 0.05:
                    score += 1
                    confidence += 0.2
                elif return_1m < -0.05:
                    score -= 1
                    confidence += 0.2
            
            # 3-month momentum
            if len(prices) >= 63:
                price_3m = prices[-63].close
                return_3m = (current_price - price_3m) / price_3m
                momentum_data['return_3m'] = return_3m
                
                if return_3m > 0.10:
                    score += 2
                    confidence += 0.3
                elif return_3m < -0.10:
                    score -= 2
                    confidence += 0.3
            
            # 6-month momentum
            if len(prices) >= 126:
                price_6m = prices[-126].close
                return_6m = (current_price - price_6m) / price_6m
                momentum_data['return_6m'] = return_6m
                
                if return_6m > 0.15:
                    score += 2
                    confidence += 0.3
                elif return_6m < -0.15:
                    score -= 2
                    confidence += 0.3
            
            # Volume trend (if available)
            # Note: Volume data would need to be added to Price model
            
            # Determine signal strength
            if score >= 3:
                strength = SignalStrength.STRONG_BUY
            elif score >= 1:
                strength = SignalStrength.BUY
            elif score >= -1:
                strength = SignalStrength.HOLD
            elif score >= -3:
                strength = SignalStrength.SELL
            else:
                strength = SignalStrength.STRONG_SELL
            
            return InvestmentSignal(
                signal_type="momentum",
                strength=strength,
                confidence=min(confidence, 1.0),
                data={
                    "momentum": momentum_data,
                    "score": score,
                    "trend": "positive" if score > 0 else "negative" if score < 0 else "neutral"
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing momentum for {asset.symbol}: {e}")
            return None
    
    def analyze_risk(self, asset: Asset) -> Optional[InvestmentSignal]:
        """Analyze risk factors for the investment."""
        try:
            # Get price history for volatility calculation
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=252)  # 1 year
            
            prices = self.db.query(Price).filter(
                Price.asset_id == asset.id,
                Price.date >= start_date
            ).order_by(Price.date).all()
            
            if len(prices) < 30:
                return None
            
            price_series = pd.Series([p.close for p in prices])
            returns = price_series.pct_change().dropna()
            
            risk_score = 0
            confidence = 0.0
            risk_metrics = {}
            
            # Volatility analysis
            volatility = returns.std() * (252 ** 0.5)  # Annualized
            risk_metrics['volatility'] = volatility
            
            if volatility < 0.15:  # Less than 15%
                risk_score += 2
                confidence += 0.3
            elif volatility < 0.25:  # Less than 25%
                risk_score += 1
                confidence += 0.2
            elif volatility > 0.40:  # More than 40%
                risk_score -= 2
                confidence += 0.3
            else:
                confidence += 0.1
            
            # Maximum drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            risk_metrics['max_drawdown'] = max_drawdown
            
            if max_drawdown > -0.10:  # Less than 10% drawdown
                risk_score += 1
                confidence += 0.2
            elif max_drawdown < -0.30:  # More than 30% drawdown
                risk_score -= 2
                confidence += 0.3
            else:
                confidence += 0.1
            
            # Sharpe ratio (simplified, assuming risk-free rate of 2%)
            if len(returns) > 0:
                annual_return = returns.mean() * 252
                sharpe_ratio = (annual_return - 0.02) / volatility if volatility > 0 else 0
                risk_metrics['sharpe_ratio'] = sharpe_ratio
                
                if sharpe_ratio > 1.0:
                    risk_score += 1
                    confidence += 0.2
                elif sharpe_ratio < 0:
                    risk_score -= 1
                    confidence += 0.2
            
            # Convert risk score to signal (inverted - lower risk is better)
            if risk_score >= 2:
                strength = SignalStrength.BUY  # Low risk
            elif risk_score >= 0:
                strength = SignalStrength.HOLD
            else:
                strength = SignalStrength.SELL  # High risk
            
            return InvestmentSignal(
                signal_type="risk",
                strength=strength,
                confidence=min(confidence, 1.0),
                data={
                    "metrics": risk_metrics,
                    "risk_level": "low" if risk_score >= 2 else "medium" if risk_score >= 0 else "high"
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing risk for {asset.symbol}: {e}")
            return None