"""
Prediction algorithms for the mathematical engine.
Pure mathematical prediction without business logic interpretation.
"""

from .trend_analysis import (
    linear_trend_prediction,
    polynomial_trend_prediction,
    moving_average_prediction,
    exponential_smoothing_prediction,
    momentum_prediction,
    ensemble_trend_prediction,
    trend_strength,
)

__all__ = [
    "linear_trend_prediction",
    "polynomial_trend_prediction", 
    "moving_average_prediction",
    "exponential_smoothing_prediction",
    "momentum_prediction",
    "ensemble_trend_prediction",
    "trend_strength",
]