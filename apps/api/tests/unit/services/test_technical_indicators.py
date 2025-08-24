"""Tests for technical indicators service."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.services.technical_indicators import TechnicalIndicators


class TestTechnicalIndicators:
    """Test suite for technical indicators calculations."""
    
    @pytest.fixture
    def sample_prices(self):
        """Generate sample price data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = pd.Series(
            100 + np.cumsum(np.random.randn(100) * 2),
            index=dates
        )
        prices = prices.abs()  # Ensure positive prices
        return prices
    
    @pytest.fixture
    def ohlcv_data(self):
        """Generate sample OHLCV data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        close = pd.Series(100 + np.cumsum(np.random.randn(50) * 2), index=dates).abs()
        
        data = pd.DataFrame({
            'open': close * (1 + np.random.randn(50) * 0.01),
            'high': close * (1 + np.abs(np.random.randn(50) * 0.02)),
            'low': close * (1 - np.abs(np.random.randn(50) * 0.02)),
            'close': close,
            'volume': np.random.randint(1000000, 5000000, 50)
        }, index=dates)
        
        return data
    
    def test_calculate_sma(self, sample_prices):
        """Test Simple Moving Average calculation."""
        sma = TechnicalIndicators.calculate_sma(sample_prices, period=20)
        
        assert len(sma) == len(sample_prices)
        assert not sma.isna().all()
        # SMA should be smoother than prices
        assert sma.std() < sample_prices.std()
        # Check manual calculation for a known point
        assert abs(sma.iloc[25] - sample_prices.iloc[6:26].mean()) < 0.01
    
    def test_calculate_ema(self, sample_prices):
        """Test Exponential Moving Average calculation."""
        ema = TechnicalIndicators.calculate_ema(sample_prices, period=20)
        
        assert len(ema) == len(sample_prices)
        assert not ema.isna().all()
        # EMA should react faster than SMA
        sma = TechnicalIndicators.calculate_sma(sample_prices, period=20)
        # Last value should be closer to recent price for EMA
        price_diff_ema = abs(sample_prices.iloc[-1] - ema.iloc[-1])
        price_diff_sma = abs(sample_prices.iloc[-1] - sma.iloc[-1])
        assert price_diff_ema <= price_diff_sma + 0.1  # Allow small tolerance
    
    def test_calculate_rsi(self, sample_prices):
        """Test RSI calculation."""
        rsi = TechnicalIndicators.calculate_rsi(sample_prices, period=14)
        
        assert len(rsi) == len(sample_prices)
        assert not rsi.isna().all()
        # RSI should be between 0 and 100
        assert (rsi >= 0).all() and (rsi <= 100).all()
        # Check for reasonable values
        assert rsi.mean() > 20 and rsi.mean() < 80
    
    def test_calculate_rsi_extremes(self):
        """Test RSI with extreme price movements."""
        # All prices increasing - should give high RSI
        increasing_prices = pd.Series(range(1, 21))
        rsi_high = TechnicalIndicators.calculate_rsi(increasing_prices, period=14)
        assert rsi_high.iloc[-1] > 70  # Should be overbought
        
        # All prices decreasing - should give low RSI
        decreasing_prices = pd.Series(range(20, 0, -1))
        rsi_low = TechnicalIndicators.calculate_rsi(decreasing_prices, period=14)
        assert rsi_low.iloc[-1] < 30  # Should be oversold
    
    def test_calculate_macd(self, sample_prices):
        """Test MACD calculation."""
        macd = TechnicalIndicators.calculate_macd(sample_prices)
        
        assert 'macd' in macd
        assert 'signal' in macd
        assert 'histogram' in macd
        
        assert len(macd['macd']) == len(sample_prices)
        assert len(macd['signal']) == len(sample_prices)
        assert len(macd['histogram']) == len(sample_prices)
        
        # Histogram should be the difference between MACD and signal
        hist_check = macd['macd'] - macd['signal']
        assert np.allclose(macd['histogram'], hist_check, rtol=1e-10)
    
    def test_calculate_bollinger_bands(self, sample_prices):
        """Test Bollinger Bands calculation."""
        bb = TechnicalIndicators.calculate_bollinger_bands(sample_prices, period=20, std_dev=2)
        
        assert 'upper' in bb
        assert 'middle' in bb
        assert 'lower' in bb
        assert 'bandwidth' in bb
        
        assert len(bb['upper']) == len(sample_prices)
        assert len(bb['middle']) == len(sample_prices)
        assert len(bb['lower']) == len(sample_prices)
        
        # Upper band should be above middle, lower band below
        assert (bb['upper'] >= bb['middle']).all()
        assert (bb['middle'] >= bb['lower']).all()
        
        # Middle band should be SMA
        sma = TechnicalIndicators.calculate_sma(sample_prices, period=20)
        assert np.allclose(bb['middle'], sma, rtol=1e-10)
    
    def test_calculate_stochastic(self, ohlcv_data):
        """Test Stochastic Oscillator calculation."""
        stoch = TechnicalIndicators.calculate_stochastic(
            ohlcv_data['high'],
            ohlcv_data['low'],
            ohlcv_data['close']
        )
        
        assert 'k' in stoch
        assert 'd' in stoch
        
        assert len(stoch['k']) == len(ohlcv_data)
        assert len(stoch['d']) == len(ohlcv_data)
        
        # Stochastic values should be between 0 and 100
        assert (stoch['k'] >= 0).all() and (stoch['k'] <= 100).all()
        assert (stoch['d'] >= 0).all() and (stoch['d'] <= 100).all()
    
    def test_calculate_atr(self, ohlcv_data):
        """Test Average True Range calculation."""
        atr = TechnicalIndicators.calculate_atr(
            ohlcv_data['high'],
            ohlcv_data['low'],
            ohlcv_data['close'],
            period=14
        )
        
        assert len(atr) == len(ohlcv_data)
        assert not atr.isna().all()
        # ATR should be positive
        assert (atr > 0).all()
        # ATR should be less than the price range
        assert (atr < ohlcv_data['high'].max() - ohlcv_data['low'].min()).all()
    
    def test_calculate_obv(self, ohlcv_data):
        """Test On-Balance Volume calculation."""
        obv = TechnicalIndicators.calculate_obv(
            ohlcv_data['close'],
            ohlcv_data['volume']
        )
        
        assert len(obv) == len(ohlcv_data)
        assert not obv.isna().any()
        # OBV should change when price changes
        price_changes = ohlcv_data['close'].diff()
        obv_changes = obv.diff()
        # When price goes up, OBV should increase
        assert ((price_changes > 0) & (obv_changes > 0)).any()
    
    def test_calculate_vwap(self, ohlcv_data):
        """Test VWAP calculation."""
        vwap = TechnicalIndicators.calculate_vwap(
            ohlcv_data['high'],
            ohlcv_data['low'],
            ohlcv_data['close'],
            ohlcv_data['volume']
        )
        
        assert len(vwap) == len(ohlcv_data)
        assert not vwap.isna().any()
        # VWAP should be within the price range
        assert (vwap >= ohlcv_data['low'].min()).all()
        assert (vwap <= ohlcv_data['high'].max()).all()
    
    def test_identify_support_resistance(self, sample_prices):
        """Test support and resistance level identification."""
        levels = TechnicalIndicators.identify_support_resistance(
            sample_prices,
            window=10,
            min_touches=2
        )
        
        assert 'support' in levels
        assert 'resistance' in levels
        assert isinstance(levels['support'], list)
        assert isinstance(levels['resistance'], list)
        
        # Support levels should be below current price (mostly)
        current_price = sample_prices.iloc[-1]
        if levels['support']:
            assert min(levels['support']) < current_price * 1.1
        
        # Resistance levels should be above current price (mostly)
        if levels['resistance']:
            assert max(levels['resistance']) > current_price * 0.9
    
    def test_calculate_all_indicators(self, ohlcv_data):
        """Test calculation of all indicators at once."""
        indicators = TechnicalIndicators.calculate_all_indicators(ohlcv_data)
        
        assert isinstance(indicators, dict)
        assert 'sma_20' in indicators
        assert 'sma_50' in indicators
        assert 'sma_200' in indicators
        assert 'ema_20' in indicators
        assert 'ema_50' in indicators
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'bollinger' in indicators
        assert 'stochastic' in indicators
        assert 'atr' in indicators
        assert 'obv' in indicators
        assert 'vwap' in indicators
        assert 'support_resistance' in indicators
    
    def test_generate_signals(self, sample_prices):
        """Test signal generation from indicators."""
        # Create indicators
        rsi = TechnicalIndicators.calculate_rsi(sample_prices)
        macd = TechnicalIndicators.calculate_macd(sample_prices)
        bollinger = TechnicalIndicators.calculate_bollinger_bands(sample_prices)
        stochastic = TechnicalIndicators.calculate_stochastic(
            sample_prices, sample_prices, sample_prices
        )
        
        indicators = {
            'rsi': rsi,
            'macd': macd,
            'bollinger': bollinger,
            'stochastic': stochastic,
            'close': sample_prices
        }
        
        signals = TechnicalIndicators.generate_signals(indicators)
        
        assert isinstance(signals, dict)
        assert 'rsi' in signals
        assert 'macd' in signals
        assert 'bollinger' in signals
        assert 'stochastic' in signals
        
        # Check signal values are valid
        assert signals['rsi'] in ['overbought', 'oversold', 'neutral']
        assert signals['macd'] in ['bullish_crossover', 'bearish_crossover', 'neutral']
        assert signals['bollinger'] in ['overbought', 'oversold', 'neutral']
        assert signals['stochastic'] in ['overbought', 'oversold', 'bullish', 'bearish']
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty series
        empty_series = pd.Series([])
        sma = TechnicalIndicators.calculate_sma(empty_series, period=20)
        assert len(sma) == 0
        
        # Single value
        single_value = pd.Series([100])
        ema = TechnicalIndicators.calculate_ema(single_value, period=20)
        assert len(ema) == 1
        assert ema.iloc[0] == 100
        
        # All same values
        same_values = pd.Series([100] * 50)
        rsi = TechnicalIndicators.calculate_rsi(same_values, period=14)
        # RSI should be around 50 for no change
        assert 40 < rsi.iloc[-1] < 60