"""Domain service for technical analysis operations.

This service contains pure business logic for technical analysis,
following Clean Architecture principles. No HTTP or DB dependencies.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass

from ..technical_indicators import TechnicalIndicators


@dataclass
class PriceData:
    """Domain entity for price data."""
    date: datetime
    close: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None


@dataclass
class TechnicalAnalysisResult:
    """Domain entity for technical analysis results."""
    symbol: str
    period_days: int
    latest_price: float
    indicators: Dict[str, Any]
    signals: Dict[str, Any]
    dates: List[str]


class TechnicalAnalysisService:
    """Domain service for technical analysis operations.
    
    This service contains pure business logic with no infrastructure dependencies.
    """
    
    def calculate_technical_indicators(
        self,
        prices: List[PriceData],
        period_days: int
    ) -> Dict[str, Any]:
        """Calculate all technical indicators from price data.
        
        Args:
            prices: List of price data points
            period_days: Number of days to analyze
            
        Returns:
            Dictionary containing all calculated indicators
        """
        if not prices:
            raise ValueError("No price data provided for analysis")
        
        if len(prices) < 20:
            raise ValueError("Insufficient price data for technical analysis (minimum 20 data points required)")
        
        # Convert to DataFrame for calculations
        price_df = self._create_price_dataframe(prices)
        
        # Calculate all indicators
        indicators = self._calculate_all_indicators(price_df)
        
        return indicators
    
    def generate_trading_signals(
        self,
        indicators: Dict[str, Any],
        latest_price: float
    ) -> Dict[str, Any]:
        """Generate trading signals based on technical indicators.
        
        Args:
            indicators: Calculated technical indicators
            latest_price: Current price for signal generation
            
        Returns:
            Dictionary containing trading signals
        """
        # Prepare signal data
        signal_data = {
            'rsi': pd.Series(indicators['rsi']),
            'macd': indicators['macd_data'],
            'bollinger': indicators['bollinger_data'],
            'close': pd.Series([latest_price])
        }
        
        # Generate signals using existing logic
        signals = TechnicalIndicators.generate_signals(signal_data)
        
        return signals
    
    def perform_complete_analysis(
        self,
        symbol: str,
        prices: List[PriceData],
        period_days: int
    ) -> TechnicalAnalysisResult:
        """Perform complete technical analysis.
        
        This is the main domain operation that orchestrates the analysis.
        
        Args:
            symbol: Asset symbol
            prices: Historical price data
            period_days: Analysis period
            
        Returns:
            Complete technical analysis result
        """
        # Calculate indicators
        indicators = self.calculate_technical_indicators(prices, period_days)
        
        # Get latest price
        latest_price = prices[-1].close if prices else 0.0
        
        # Generate signals
        signals = self.generate_trading_signals(indicators, latest_price)
        
        # Format dates
        dates = [p.date.strftime('%Y-%m-%d') for p in prices]
        
        # Clean up internal data from indicators for response
        clean_indicators = self._clean_indicators_for_response(indicators)
        
        return TechnicalAnalysisResult(
            symbol=symbol.upper(),
            period_days=period_days,
            latest_price=latest_price,
            indicators=clean_indicators,
            signals=signals,
            dates=dates
        )
    
    def _create_price_dataframe(self, prices: List[PriceData]) -> pd.DataFrame:
        """Convert price data to DataFrame for calculations.
        
        Private method for internal data transformation.
        """
        data = [
            {'date': p.date, 'close': p.close}
            for p in prices
        ]
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        return df
    
    def _calculate_all_indicators(self, price_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators.
        
        Private method that encapsulates indicator calculation logic.
        """
        close_prices = price_df['close']
        
        # Basic moving averages
        indicators = {
            'sma_20': TechnicalIndicators.calculate_sma(close_prices, 20).to_list(),
            'sma_50': TechnicalIndicators.calculate_sma(close_prices, 50).to_list(),
            'ema_20': TechnicalIndicators.calculate_ema(close_prices, 20).to_list(),
            'rsi': TechnicalIndicators.calculate_rsi(close_prices).to_list(),
        }
        
        # Calculate MACD
        macd_data = TechnicalIndicators.calculate_macd(close_prices)
        indicators['macd'] = {
            'line': macd_data['macd'].to_list(),
            'signal': macd_data['signal'].to_list(),
            'histogram': macd_data['histogram'].to_list()
        }
        indicators['macd_data'] = macd_data  # Keep for signal generation
        
        # Calculate Bollinger Bands
        bb_data = TechnicalIndicators.calculate_bollinger_bands(close_prices)
        indicators['bollinger_bands'] = {
            'upper': bb_data['upper'].to_list(),
            'middle': bb_data['middle'].to_list(),
            'lower': bb_data['lower'].to_list(),
            'bandwidth': bb_data['bandwidth'].to_list()
        }
        indicators['bollinger_data'] = bb_data  # Keep for signal generation
        
        return indicators
    
    def _clean_indicators_for_response(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Clean indicators for API response.
        
        Remove internal data structures used for calculations.
        """
        clean = indicators.copy()
        # Remove internal calculation data
        clean.pop('macd_data', None)
        clean.pop('bollinger_data', None)
        return clean