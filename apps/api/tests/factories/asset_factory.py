"""
Asset factory for test data generation.
Single responsibility: Create asset and price test data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .base import BaseFactory


class AssetFactory(BaseFactory):
    """Factory for creating asset test data."""
    
    SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM"]
    SECTORS = ["Technology", "Finance", "Healthcare", "Energy", "Consumer"]
    
    @staticmethod
    def create_asset_data(
        symbol: Optional[str] = None,
        name: Optional[str] = None,
        sector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create asset data for testing."""
        symbol = symbol or np.random.choice(AssetFactory.SYMBOLS)
        return {
            "symbol": symbol,
            "name": name or f"{symbol} Inc.",
            "sector": sector or np.random.choice(AssetFactory.SECTORS)
        }
    
    @staticmethod
    def create_price_series(
        start_price: float = 100.0,
        days: int = 252,
        volatility: float = 0.02,
        trend: float = 0.0005
    ) -> pd.Series:
        """Create realistic price series for testing."""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        prices = [start_price]
        
        for _ in range(days - 1):
            daily_return = np.random.normal(trend, volatility)
            new_price = prices[-1] * (1 + daily_return)
            prices.append(max(new_price, 1.0))  # Ensure positive prices
        
        return pd.Series(prices, index=dates)
    
    @staticmethod
    def create_returns_series(
        days: int = 252,
        mean_return: float = 0.0005,
        volatility: float = 0.02
    ) -> pd.Series:
        """Create returns series for testing."""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        returns = np.random.normal(mean_return, volatility, days)
        return pd.Series(returns, index=dates)