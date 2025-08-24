"""Technical indicators calculation service for market analysis."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Service for calculating technical analysis indicators."""
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: Series of price data
            period: Number of periods for moving average
            
        Returns:
            Series with SMA values
        """
        return prices.rolling(window=period, min_periods=1).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: Series of price data
            period: Number of periods for moving average
            
        Returns:
            Series with EMA values
        """
        return prices.ewm(span=period, adjust=False, min_periods=1).mean()
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: Series of price data
            period: Number of periods for RSI calculation
            
        Returns:
            Series with RSI values (0-100)
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period, min_periods=1).mean()
        avg_losses = losses.rolling(window=period, min_periods=1).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses.replace(0, 1e-10)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Series of price data
            fast_period: Period for fast EMA
            slow_period: Period for slow EMA
            signal_period: Period for signal line EMA
            
        Returns:
            Dictionary with MACD line, signal line, and histogram
        """
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, 
                                 period: int = 20, 
                                 std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Series of price data
            period: Period for moving average
            std_dev: Number of standard deviations for bands
            
        Returns:
            Dictionary with upper band, middle band (SMA), and lower band
        """
        # Calculate middle band (SMA)
        middle_band = prices.rolling(window=period, min_periods=1).mean()
        
        # Calculate standard deviation
        std = prices.rolling(window=period, min_periods=1).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band,
            'bandwidth': (upper_band - lower_band) / middle_band
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, 
                           low: pd.Series, 
                           close: pd.Series,
                           period: int = 14,
                           smooth_k: int = 3,
                           smooth_d: int = 3) -> Dict[str, pd.Series]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            period: Lookback period
            smooth_k: Smoothing period for %K
            smooth_d: Smoothing period for %D
            
        Returns:
            Dictionary with %K and %D lines
        """
        # Calculate lowest low and highest high
        lowest_low = low.rolling(window=period, min_periods=1).min()
        highest_high = high.rolling(window=period, min_periods=1).max()
        
        # Calculate %K
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low).replace(0, 1))
        
        # Smooth %K
        k_smooth = k_percent.rolling(window=smooth_k, min_periods=1).mean()
        
        # Calculate %D (signal line)
        d_percent = k_smooth.rolling(window=smooth_d, min_periods=1).mean()
        
        return {
            'k': k_smooth,
            'd': d_percent
        }
    
    @staticmethod
    def calculate_atr(high: pd.Series, 
                     low: pd.Series, 
                     close: pd.Series,
                     period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR) for volatility measurement.
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            period: Period for ATR calculation
            
        Returns:
            Series with ATR values
        """
        # Calculate True Range
        high_low = high - low
        high_close = abs(high - close.shift())
        low_close = abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = true_range.rolling(window=period, min_periods=1).mean()
        
        return atr
    
    @staticmethod
    def calculate_obv(prices: pd.Series, volumes: pd.Series) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV).
        
        Args:
            prices: Series of price data
            volumes: Series of volume data
            
        Returns:
            Series with OBV values
        """
        # Calculate price direction
        price_diff = prices.diff()
        
        # Calculate OBV
        obv = pd.Series(index=prices.index, dtype=float)
        obv.iloc[0] = volumes.iloc[0]
        
        for i in range(1, len(prices)):
            if price_diff.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + volumes.iloc[i]
            elif price_diff.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - volumes.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def calculate_vwap(high: pd.Series, 
                      low: pd.Series, 
                      close: pd.Series,
                      volume: pd.Series) -> pd.Series:
        """
        Calculate Volume-Weighted Average Price (VWAP).
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            volume: Series of volume data
            
        Returns:
            Series with VWAP values
        """
        typical_price = (high + low + close) / 3
        cumulative_tpv = (typical_price * volume).cumsum()
        cumulative_volume = volume.cumsum()
        
        vwap = cumulative_tpv / cumulative_volume.replace(0, 1)
        
        return vwap
    
    @staticmethod
    def identify_support_resistance(prices: pd.Series, 
                                   window: int = 20,
                                   min_touches: int = 2) -> Dict[str, List[float]]:
        """
        Identify support and resistance levels.
        
        Args:
            prices: Series of price data
            window: Window size for finding local extrema
            min_touches: Minimum number of touches to confirm level
            
        Returns:
            Dictionary with support and resistance levels
        """
        # Find local maxima and minima
        rolling_max = prices.rolling(window=window, center=True).max()
        rolling_min = prices.rolling(window=window, center=True).min()
        
        # Identify peaks and troughs
        peaks = prices[prices == rolling_max].dropna()
        troughs = prices[prices == rolling_min].dropna()
        
        # Cluster nearby levels
        resistance_levels = []
        support_levels = []
        
        # Simple clustering for resistance
        for peak in peaks.unique():
            touches = len(peaks[abs(peaks - peak) / peak < 0.01])  # Within 1%
            if touches >= min_touches:
                resistance_levels.append(float(peak))
        
        # Simple clustering for support
        for trough in troughs.unique():
            touches = len(troughs[abs(troughs - trough) / trough < 0.01])  # Within 1%
            if touches >= min_touches:
                support_levels.append(float(trough))
        
        return {
            'support': sorted(support_levels),
            'resistance': sorted(resistance_levels)
        }
    
    @staticmethod
    def calculate_all_indicators(price_data: pd.DataFrame) -> Dict[str, any]:
        """
        Calculate all technical indicators for given price data.
        
        Args:
            price_data: DataFrame with columns: open, high, low, close, volume
            
        Returns:
            Dictionary with all calculated indicators
        """
        try:
            close = price_data['close']
            high = price_data.get('high', close)
            low = price_data.get('low', close)
            volume = price_data.get('volume', pd.Series(1, index=close.index))
            
            indicators = {
                'sma_20': TechnicalIndicators.calculate_sma(close, 20),
                'sma_50': TechnicalIndicators.calculate_sma(close, 50),
                'sma_200': TechnicalIndicators.calculate_sma(close, 200),
                'ema_20': TechnicalIndicators.calculate_ema(close, 20),
                'ema_50': TechnicalIndicators.calculate_ema(close, 50),
                'rsi': TechnicalIndicators.calculate_rsi(close),
                'macd': TechnicalIndicators.calculate_macd(close),
                'bollinger': TechnicalIndicators.calculate_bollinger_bands(close),
                'stochastic': TechnicalIndicators.calculate_stochastic(high, low, close),
                'atr': TechnicalIndicators.calculate_atr(high, low, close),
                'obv': TechnicalIndicators.calculate_obv(close, volume),
                'vwap': TechnicalIndicators.calculate_vwap(high, low, close, volume),
                'support_resistance': TechnicalIndicators.identify_support_resistance(close)
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    @staticmethod
    def generate_signals(indicators: Dict) -> Dict[str, str]:
        """
        Generate trading signals based on technical indicators.
        
        Args:
            indicators: Dictionary of calculated indicators
            
        Returns:
            Dictionary with signal interpretations
        """
        signals = {}
        
        try:
            # RSI signals
            if 'rsi' in indicators:
                latest_rsi = indicators['rsi'].iloc[-1]
                if latest_rsi > 70:
                    signals['rsi'] = 'overbought'
                elif latest_rsi < 30:
                    signals['rsi'] = 'oversold'
                else:
                    signals['rsi'] = 'neutral'
            
            # MACD signals
            if 'macd' in indicators:
                macd_hist = indicators['macd']['histogram'].iloc[-1]
                macd_prev = indicators['macd']['histogram'].iloc[-2] if len(indicators['macd']['histogram']) > 1 else 0
                
                if macd_hist > 0 and macd_prev <= 0:
                    signals['macd'] = 'bullish_crossover'
                elif macd_hist < 0 and macd_prev >= 0:
                    signals['macd'] = 'bearish_crossover'
                else:
                    signals['macd'] = 'neutral'
            
            # Bollinger Bands signals
            if 'bollinger' in indicators:
                close_price = indicators.get('close', pd.Series()).iloc[-1] if 'close' in indicators else None
                if close_price:
                    upper = indicators['bollinger']['upper'].iloc[-1]
                    lower = indicators['bollinger']['lower'].iloc[-1]
                    
                    if close_price > upper:
                        signals['bollinger'] = 'overbought'
                    elif close_price < lower:
                        signals['bollinger'] = 'oversold'
                    else:
                        signals['bollinger'] = 'neutral'
            
            # Stochastic signals
            if 'stochastic' in indicators:
                k = indicators['stochastic']['k'].iloc[-1]
                d = indicators['stochastic']['d'].iloc[-1]
                
                if k > 80:
                    signals['stochastic'] = 'overbought'
                elif k < 20:
                    signals['stochastic'] = 'oversold'
                elif k > d:
                    signals['stochastic'] = 'bullish'
                else:
                    signals['stochastic'] = 'bearish'
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
        
        return signals