"""
Pure mathematical validation functions.
Input validation without business logic dependencies.
"""

import numpy as np
from typing import List, Union
from .types import (
    Scalar, PriceSeries, ReturnSeries, WeightVector,
    ComputationalLimits, FinancialConstants
)


def validate_price_series(prices: PriceSeries) -> bool:
    """
    Validate price series for mathematical operations.
    
    Args:
        prices: List of price values
        
    Returns:
        True if valid for mathematical operations
    """
    if not prices or not isinstance(prices, list):
        return False
    
    if len(prices) < 2:
        return False
    
    if len(prices) > ComputationalLimits.MAX_ARRAY_SIZE:
        return False
    
    # Check all prices are positive numbers
    try:
        for price in prices:
            if not isinstance(price, (int, float)):
                return False
            if price <= 0:
                return False
            if not np.isfinite(price):
                return False
            if price > ComputationalLimits.MAX_VALUE:
                return False
    except (TypeError, ValueError):
        return False
    
    return True


def validate_return_series(returns: ReturnSeries) -> bool:
    """
    Validate return series for mathematical operations.
    
    Args:
        returns: List of return values
        
    Returns:
        True if valid for calculations
    """
    if not returns or not isinstance(returns, list):
        return False
    
    if len(returns) < ComputationalLimits.MIN_SAMPLE_SIZE:
        return False
    
    if len(returns) > ComputationalLimits.MAX_ARRAY_SIZE:
        return False
    
    # Check all returns are finite numbers
    try:
        for ret in returns:
            if not isinstance(ret, (int, float)):
                return False
            if not np.isfinite(ret):
                return False
            # Sanity check: returns shouldn't be extreme
            if abs(ret) > 10.0:  # 1000% return in one period is unrealistic
                return False
    except (TypeError, ValueError):
        return False
    
    return True


def validate_weights(weights: WeightVector, tolerance: float = 0.01) -> bool:
    """
    Validate portfolio weights for mathematical operations.
    
    Args:
        weights: Portfolio weights
        tolerance: Acceptable deviation from sum=1.0
        
    Returns:
        True if weights are valid
    """
    if not weights or not isinstance(weights, list):
        return False
    
    if len(weights) == 0 or len(weights) > 1000:  # Reasonable portfolio size
        return False
    
    try:
        # Check all weights are non-negative numbers
        for weight in weights:
            if not isinstance(weight, (int, float)):
                return False
            if weight < 0:
                return False
            if not np.isfinite(weight):
                return False
        
        # Check weights sum to approximately 1.0
        weight_sum = sum(weights)
        if abs(weight_sum - 1.0) > tolerance:
            return False
            
    except (TypeError, ValueError):
        return False
    
    return True


def validate_scalar(value: Scalar, min_val: float = None, max_val: float = None) -> bool:
    """
    Validate scalar value for mathematical operations.
    
    Args:
        value: Scalar value to validate
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
        
    Returns:
        True if valid scalar
    """
    if not isinstance(value, (int, float)):
        return False
    
    if not np.isfinite(value):
        return False
    
    if min_val is not None and value < min_val:
        return False
    
    if max_val is not None and value > max_val:
        return False
    
    return True


def validate_matrix(matrix: List[List[float]]) -> bool:
    """
    Validate matrix for mathematical operations.
    
    Args:
        matrix: 2D matrix as list of lists
        
    Returns:
        True if valid matrix
    """
    if not matrix or not isinstance(matrix, list):
        return False
    
    if len(matrix) == 0:
        return False
    
    # Check all rows have same length
    row_length = len(matrix[0])
    if row_length == 0:
        return False
    
    try:
        for row in matrix:
            if not isinstance(row, list):
                return False
            if len(row) != row_length:
                return False
            
            for value in row:
                if not isinstance(value, (int, float)):
                    return False
                if not np.isfinite(value):
                    return False
                    
    except (TypeError, ValueError):
        return False
    
    return True


def validate_covariance_matrix(matrix: List[List[float]]) -> bool:
    """
    Validate covariance matrix for portfolio optimization.
    
    Args:
        matrix: Covariance matrix
        
    Returns:
        True if valid covariance matrix
    """
    if not validate_matrix(matrix):
        return False
    
    # Must be square matrix
    n_rows = len(matrix)
    n_cols = len(matrix[0])
    
    if n_rows != n_cols:
        return False
    
    try:
        matrix_array = np.array(matrix)
        
        # Must be symmetric (within tolerance)
        if not np.allclose(matrix_array, matrix_array.T, rtol=1e-10):
            return False
        
        # Must be positive semi-definite
        eigenvalues = np.linalg.eigvals(matrix_array)
        if np.any(eigenvalues < -1e-10):  # Allow small numerical errors
            return False
            
    except (np.linalg.LinAlgError, ValueError):
        return False
    
    return True


def sanitize_price_series(prices: List[Union[int, float, str]]) -> PriceSeries:
    """
    Sanitize and clean price series for mathematical operations.
    Handles common data quality issues.
    
    Args:
        prices: Raw price data (may contain strings, nulls, etc.)
        
    Returns:
        Clean price series ready for calculations
    """
    clean_prices = []
    
    for price in prices:
        try:
            # Convert to float
            if isinstance(price, str):
                if price.strip() == "" or price.lower() in ['null', 'nan', 'none']:
                    continue
                price_val = float(price.strip())
            elif price is None:
                continue
            else:
                price_val = float(price)
            
            # Validate range
            if price_val <= 0:
                continue
            if price_val > ComputationalLimits.MAX_VALUE:
                continue
            if not np.isfinite(price_val):
                continue
            
            clean_prices.append(price_val)
            
        except (ValueError, TypeError):
            continue  # Skip invalid values
    
    return clean_prices


def sanitize_weights(weights: List[Union[int, float]], 
                    normalize: bool = True) -> WeightVector:
    """
    Sanitize and normalize portfolio weights.
    
    Args:
        weights: Raw weight values
        normalize: Whether to normalize to sum=1.0
        
    Returns:
        Clean, normalized weights
    """
    clean_weights = []
    
    for weight in weights:
        try:
            weight_val = float(weight)
            
            # Ensure non-negative
            weight_val = max(0.0, weight_val)
            
            # Cap at maximum
            weight_val = min(1.0, weight_val)
            
            if np.isfinite(weight_val):
                clean_weights.append(weight_val)
            else:
                clean_weights.append(0.0)
                
        except (ValueError, TypeError):
            clean_weights.append(0.0)
    
    if not clean_weights:
        return []
    
    # Normalize to sum to 1.0 if requested
    if normalize:
        weight_sum = sum(clean_weights)
        if weight_sum > 0:
            clean_weights = [w / weight_sum for w in clean_weights]
        else:
            # Equal weights if all were zero
            equal_weight = 1.0 / len(clean_weights)
            clean_weights = [equal_weight] * len(clean_weights)
    
    return clean_weights


def check_numerical_stability(value: float) -> bool:
    """
    Check if a numerical value is stable for calculations.
    
    Args:
        value: Numerical value to check
        
    Returns:
        True if numerically stable
    """
    if not np.isfinite(value):
        return False
    
    if abs(value) < ComputationalLimits.MIN_POSITIVE_VALUE:
        return False
    
    if abs(value) > ComputationalLimits.MAX_VALUE:
        return False
    
    return True