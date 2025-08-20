"""
Test adapters for converting between different data types.
Helps tests work with different return types without modifying business logic.
Single responsibility: Data type conversion for tests.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Union


class TestDataAdapter:
    """Adapter for converting between test and implementation data types."""
    
    @staticmethod
    def dict_to_series(data: Dict[str, float]) -> pd.Series:
        """Convert dictionary to pandas Series."""
        return pd.Series(data)
    
    @staticmethod
    def series_to_dict(series: pd.Series) -> Dict[str, float]:
        """Convert pandas Series to dictionary."""
        return series.to_dict()
    
    @staticmethod
    def array_to_series(array: np.ndarray, index=None) -> pd.Series:
        """Convert numpy array to pandas Series."""
        return pd.Series(array, index=index)
    
    @staticmethod
    def series_to_array(series: pd.Series) -> np.ndarray:
        """Convert pandas Series to numpy array."""
        return series.values
    
    @staticmethod
    def list_to_array(data: List[float]) -> np.ndarray:
        """Convert list to numpy array."""
        return np.array(data)
    
    @staticmethod
    def array_to_list(array: np.ndarray) -> List[float]:
        """Convert numpy array to list."""
        return array.tolist()
    
    @staticmethod
    def normalize_weights(weights: Union[Dict[str, float], pd.Series]) -> Dict[str, float]:
        """Normalize weights to sum to 1.0 and return as dictionary."""
        if isinstance(weights, pd.Series):
            weights = weights.to_dict()
        
        total = sum(weights.values())
        if total > 0:
            return {k: v/total for k, v in weights.items()}
        return weights
    
    @staticmethod
    def create_return_series(returns: Union[List[float], np.ndarray], periods: int = 252) -> pd.Series:
        """Create a properly indexed return series for testing."""
        dates = pd.date_range(end=pd.Timestamp.now(), periods=periods, freq='D')
        
        if isinstance(returns, list):
            returns = np.array(returns)
        
        # Ensure we have enough data
        if len(returns) < periods:
            # Pad with zeros or repeat pattern
            repeats = (periods // len(returns)) + 1
            returns = np.tile(returns, repeats)[:periods]
        elif len(returns) > periods:
            returns = returns[:periods]
        
        return pd.Series(returns, index=dates)