"""
Core type definitions for the mathematical engine.
Pure mathematical types without business logic dependencies.
"""

from typing import Union, List, Tuple, NewType, Protocol
import numpy as np
from numpy.typing import NDArray

# Primitive mathematical types
Scalar = Union[int, float]
Vector = List[Scalar]
Matrix = List[List[Scalar]]
Array1D = NDArray[np.float64]
Array2D = NDArray[np.float64]

# Financial data types (pure mathematical representations)
Price = NewType('Price', float)
Return = NewType('Return', float)
Weight = NewType('Weight', float)
Volatility = NewType('Volatility', float)

# Time series types
PriceSeries = List[Price]
ReturnSeries = List[Return]
WeightVector = List[Weight]

# Matrix types for financial operations
CovarianceMatrix = Array2D
CorrelationMatrix = Array2D
ReturnsMatrix = Array2D  # Each row is an asset, each column is a time period

# Prediction types
Prediction = NewType('Prediction', float)
Confidence = NewType('Confidence', float)  # 0.0 to 1.0
PredictionResult = Tuple[Prediction, Confidence]

# Optimization types  
ObjectiveValue = NewType('ObjectiveValue', float)
Constraint = NewType('Constraint', float)
OptimizationResult = Tuple[WeightVector, ObjectiveValue]

# Signal processing types
Signal = List[Scalar]
FilteredSignal = List[Scalar]
Frequency = NewType('Frequency', float)
Amplitude = NewType('Amplitude', float)

# Machine learning types
Features = Array1D
Target = NewType('Target', float)
Targets = Array1D
FeatureMatrix = Array2D
ModelParameters = Array1D

# Time series model types
TimeSeriesData = Array1D
Lag = NewType('Lag', int)
Seasonality = NewType('Seasonality', int)
Trend = Array1D

# Performance metrics types
SharpeRatio = NewType('SharpeRatio', float)
MaxDrawdown = NewType('MaxDrawdown', float) 
Beta = NewType('Beta', float)
Alpha = NewType('Alpha', float)

# Risk metrics types
ValueAtRisk = NewType('ValueAtRisk', float)
ConditionalVaR = NewType('ConditionalVaR', float)
TrackingError = NewType('TrackingError', float)


class MathematicalFunction(Protocol):
    """Protocol for pure mathematical functions."""
    
    def __call__(self, *args: Scalar) -> Scalar:
        """Pure mathematical function signature."""
        ...


class OptimizationFunction(Protocol):
    """Protocol for optimization objective functions."""
    
    def __call__(self, weights: WeightVector) -> ObjectiveValue:
        """Optimization objective function signature."""
        ...


class PredictionModel(Protocol):
    """Protocol for prediction models."""
    
    def predict(self, features: Features) -> PredictionResult:
        """Prediction model signature."""
        ...
    
    def fit(self, X: FeatureMatrix, y: Targets) -> None:
        """Model training signature."""
        ...


# Mathematical constants for financial calculations
class FinancialConstants:
    """Mathematical constants used in financial calculations."""
    
    TRADING_DAYS_PER_YEAR = 252
    TRADING_WEEKS_PER_YEAR = 52
    TRADING_MONTHS_PER_YEAR = 12
    
    # Risk-free rates (as decimals)
    DEFAULT_RISK_FREE_RATE = 0.02  # 2%
    
    # Standard deviation multipliers
    STD_DEV_1 = 1.0
    STD_DEV_2 = 2.0
    STD_DEV_3 = 3.0
    
    # Common confidence levels
    CONFIDENCE_95 = 0.95
    CONFIDENCE_99 = 0.99
    
    # Mathematical tolerances
    EPSILON = 1e-10
    CONVERGENCE_TOLERANCE = 1e-6
    MAX_ITERATIONS = 1000
    
    # Portfolio constraints
    MIN_WEIGHT = 0.0
    MAX_WEIGHT = 1.0
    WEIGHT_SUM_TARGET = 1.0


class ComputationalLimits:
    """Computational limits and safeguards."""
    
    MAX_ARRAY_SIZE = 1_000_000  # Maximum array size for memory safety
    MAX_ITERATIONS = 10_000     # Maximum optimization iterations  
    MIN_SAMPLE_SIZE = 10        # Minimum samples for statistical operations
    MAX_FEATURES = 1000         # Maximum features for ML models
    
    # Numerical stability limits
    MIN_POSITIVE_VALUE = 1e-10
    MAX_VALUE = 1e10
    DIVISION_EPSILON = 1e-12