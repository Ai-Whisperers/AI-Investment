"""
Waardhaven Mathematical Engine - Core Module
Pure mathematical operations for investment intelligence.
"""

from .types import (
    # Basic types
    Scalar, Vector, Matrix, Array1D, Array2D,
    
    # Financial types
    Price, Return, Weight, Volatility,
    PriceSeries, ReturnSeries, WeightVector,
    
    # Matrix types
    CovarianceMatrix, CorrelationMatrix, ReturnsMatrix,
    
    # Prediction types
    Prediction, Confidence, PredictionResult,
    
    # Optimization types
    ObjectiveValue, Constraint, OptimizationResult,
    
    # Performance metrics
    SharpeRatio, MaxDrawdown, Beta, Alpha,
    
    # Risk metrics
    ValueAtRisk, ConditionalVaR, TrackingError,
    
    # Constants
    FinancialConstants, ComputationalLimits,
    
    # Protocols
    MathematicalFunction, OptimizationFunction, PredictionModel,
)

__version__ = "0.1.0"
__author__ = "Waardhaven AI"
__description__ = "Pure mathematical engine for investment intelligence"

# Export all core types and constants
__all__ = [
    "Scalar", "Vector", "Matrix", "Array1D", "Array2D",
    "Price", "Return", "Weight", "Volatility",
    "PriceSeries", "ReturnSeries", "WeightVector",
    "CovarianceMatrix", "CorrelationMatrix", "ReturnsMatrix",
    "Prediction", "Confidence", "PredictionResult",
    "ObjectiveValue", "Constraint", "OptimizationResult",
    "SharpeRatio", "MaxDrawdown", "Beta", "Alpha",
    "ValueAtRisk", "ConditionalVaR", "TrackingError",
    "FinancialConstants", "ComputationalLimits",
    "MathematicalFunction", "OptimizationFunction", "PredictionModel",
]