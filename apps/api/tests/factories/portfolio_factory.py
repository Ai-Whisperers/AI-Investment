"""
Portfolio factory for test data generation.
Single responsibility: Create portfolio and allocation test data.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from .base import BaseFactory
from .asset_factory import AssetFactory


class PortfolioFactory(BaseFactory):
    """Factory for creating portfolio test data."""
    
    @staticmethod
    def create_portfolio_data(
        name: Optional[str] = None,
        total_value: float = 100000.0,
        user_id: int = 1
    ) -> Dict[str, Any]:
        """Create portfolio data for testing."""
        return {
            "name": name or f"Test Portfolio {PortfolioFactory.random_string(4)}",
            "description": "Test portfolio for unit testing",
            "total_value": total_value,
            "user_id": user_id,
            "returns": 0.0
        }
    
    @staticmethod
    def create_allocations(
        symbols: Optional[List[str]] = None,
        weights: Optional[List[float]] = None
    ) -> Dict[str, float]:
        """Create portfolio allocations for testing."""
        if symbols is None:
            symbols = AssetFactory.SYMBOLS[:5]
        
        if weights is None:
            # Generate random weights that sum to 1
            weights = np.random.random(len(symbols))
            weights = weights / weights.sum()
        
        return dict(zip(symbols, weights))
    
    @staticmethod
    def create_portfolio_values(
        initial_value: float = 100000.0,
        days: int = 30,
        daily_return: float = 0.001,
        volatility: float = 0.01
    ) -> pd.Series:
        """Create portfolio value series for testing."""
        dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
        values = [initial_value]
        
        for _ in range(days - 1):
            daily_change = np.random.normal(daily_return, volatility)
            new_value = values[-1] * (1 + daily_change)
            values.append(new_value)
        
        return pd.Series(values, index=dates)