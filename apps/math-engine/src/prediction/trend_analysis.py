"""
Pure mathematical trend analysis and prediction algorithms.
Designed for WebAssembly compilation and high-performance execution.
"""

import numpy as np
from typing import List, Tuple, Optional
from ..core.types import (
    PriceSeries, ReturnSeries, Prediction, Confidence, 
    PredictionResult, Scalar, Array1D, FinancialConstants
)


def linear_trend_prediction(prices: PriceSeries, 
                          prediction_periods: int = 1) -> List[PredictionResult]:
    """
    Predict future prices using linear trend analysis.
    Pure mathematical implementation - no business logic.
    
    Args:
        prices: Historical price series
        prediction_periods: Number of periods to predict
        
    Returns:
        List of (prediction, confidence) tuples
    """
    if len(prices) < 3:
        return [(Prediction(prices[-1] if prices else 0.0), Confidence(0.0))] * prediction_periods
    
    try:
        # Convert to numpy array for vectorized operations
        prices_array = np.array(prices, dtype=np.float64)
        x = np.arange(len(prices_array))
        
        # Linear regression: y = ax + b
        slope, intercept = np.polyfit(x, prices_array, 1)
        
        # Calculate R-squared for confidence
        fitted_values = slope * x + intercept
        ss_res = np.sum((prices_array - fitted_values) ** 2)
        ss_tot = np.sum((prices_array - np.mean(prices_array)) ** 2)
        
        if ss_tot == 0:
            r_squared = 0.0
        else:
            r_squared = 1.0 - (ss_res / ss_tot)
        
        confidence = Confidence(max(0.0, min(1.0, r_squared)))
        
        # Predict future values
        predictions = []
        for i in range(1, prediction_periods + 1):
            future_x = len(prices_array) - 1 + i
            predicted_price = slope * future_x + intercept
            predictions.append((Prediction(predicted_price), confidence))
        
        return predictions
        
    except Exception:
        # Fallback: return last price with zero confidence
        last_price = prices[-1] if prices else 0.0
        return [(Prediction(last_price), Confidence(0.0))] * prediction_periods


def polynomial_trend_prediction(prices: PriceSeries, 
                               degree: int = 2,
                               prediction_periods: int = 1) -> List[PredictionResult]:
    """
    Predict using polynomial trend fitting.
    Higher degree polynomials for non-linear trends.
    """
    if len(prices) < degree + 1:
        return linear_trend_prediction(prices, prediction_periods)
    
    try:
        prices_array = np.array(prices, dtype=np.float64)
        x = np.arange(len(prices_array))
        
        # Polynomial fitting
        coefficients = np.polyfit(x, prices_array, degree)
        polynomial = np.poly1d(coefficients)
        
        # Calculate R-squared
        fitted_values = polynomial(x)
        ss_res = np.sum((prices_array - fitted_values) ** 2)
        ss_tot = np.sum((prices_array - np.mean(prices_array)) ** 2)
        
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        confidence = Confidence(max(0.0, min(1.0, r_squared)))
        
        # Predict future values
        predictions = []
        for i in range(1, prediction_periods + 1):
            future_x = len(prices_array) - 1 + i
            predicted_price = polynomial(future_x)
            predictions.append((Prediction(predicted_price), confidence))
        
        return predictions
        
    except Exception:
        return linear_trend_prediction(prices, prediction_periods)


def moving_average_prediction(prices: PriceSeries,
                            window: int = 20,
                            prediction_periods: int = 1) -> List[PredictionResult]:
    """
    Predict using moving average trend.
    Simple but robust prediction method.
    """
    if len(prices) < window:
        return [(Prediction(np.mean(prices) if prices else 0.0), Confidence(0.1))] * prediction_periods
    
    try:
        # Calculate moving average
        prices_array = np.array(prices, dtype=np.float64)
        moving_avg = np.mean(prices_array[-window:])
        
        # Calculate confidence based on price stability around MA
        recent_prices = prices_array[-window:]
        deviations = np.abs(recent_prices - moving_avg)
        relative_stability = 1.0 - np.mean(deviations) / moving_avg
        confidence = Confidence(max(0.0, min(1.0, relative_stability)))
        
        # Predict future as continuation of moving average
        predictions = [(Prediction(moving_avg), confidence)] * prediction_periods
        return predictions
        
    except Exception:
        last_price = prices[-1] if prices else 0.0
        return [(Prediction(last_price), Confidence(0.0))] * prediction_periods


def exponential_smoothing_prediction(prices: PriceSeries,
                                   alpha: float = 0.3,
                                   prediction_periods: int = 1) -> List[PredictionResult]:
    """
    Predict using exponential smoothing.
    Adaptive to recent price movements.
    
    Args:
        prices: Historical prices
        alpha: Smoothing parameter (0 < alpha < 1)
        prediction_periods: Periods to forecast
    """
    if not prices:
        return [(Prediction(0.0), Confidence(0.0))] * prediction_periods
    
    if len(prices) == 1:
        return [(Prediction(prices[0]), Confidence(0.1))] * prediction_periods
    
    try:
        # Exponential smoothing calculation
        smoothed = prices[0]
        for price in prices[1:]:
            smoothed = alpha * price + (1 - alpha) * smoothed
        
        # Calculate prediction confidence based on recent trend stability
        recent_prices = prices[-min(20, len(prices)):]
        recent_volatility = np.std(recent_prices) / np.mean(recent_prices) if recent_prices else 1.0
        confidence = Confidence(max(0.1, 1.0 - recent_volatility))
        
        # Predict future (exponential smoothing assumes trend continuation)
        predictions = [(Prediction(smoothed), confidence)] * prediction_periods
        return predictions
        
    except Exception:
        return [(Prediction(prices[-1]), Confidence(0.0))] * prediction_periods


def momentum_prediction(prices: PriceSeries,
                       lookback: int = 10,
                       prediction_periods: int = 1) -> List[PredictionResult]:
    """
    Predict based on price momentum.
    Mathematical momentum without interpretation.
    """
    if len(prices) < lookback + 1:
        return [(Prediction(prices[-1] if prices else 0.0), Confidence(0.0))] * prediction_periods
    
    try:
        # Calculate momentum as rate of price change
        recent_prices = np.array(prices[-lookback:], dtype=np.float64)
        x = np.arange(len(recent_prices))
        
        # Linear regression on recent prices to get momentum
        slope, intercept = np.polyfit(x, recent_prices, 1)
        
        # Calculate confidence based on linearity of recent trend
        fitted = slope * x + intercept
        r_squared = 1.0 - np.sum((recent_prices - fitted) ** 2) / np.sum((recent_prices - np.mean(recent_prices)) ** 2)
        confidence = Confidence(max(0.0, min(1.0, r_squared)))
        
        # Predict by extrapolating momentum
        predictions = []
        last_x = len(recent_prices) - 1
        for i in range(1, prediction_periods + 1):
            future_x = last_x + i
            predicted_price = slope * future_x + intercept
            predictions.append((Prediction(max(0.0, predicted_price)), confidence))
        
        return predictions
        
    except Exception:
        return [(Prediction(prices[-1]), Confidence(0.0))] * prediction_periods


def ensemble_trend_prediction(prices: PriceSeries,
                             prediction_periods: int = 1) -> List[PredictionResult]:
    """
    Ensemble prediction combining multiple trend analysis methods.
    Provides robust predictions by averaging different approaches.
    """
    if not prices:
        return [(Prediction(0.0), Confidence(0.0))] * prediction_periods
    
    # Get predictions from different methods
    methods = [
        linear_trend_prediction(prices, prediction_periods),
        polynomial_trend_prediction(prices, 2, prediction_periods),
        moving_average_prediction(prices, min(20, len(prices)//2), prediction_periods),
        exponential_smoothing_prediction(prices, 0.3, prediction_periods),
        momentum_prediction(prices, min(10, len(prices)//2), prediction_periods)
    ]
    
    # Remove failed methods (empty results)
    valid_methods = [method for method in methods if method]
    
    if not valid_methods:
        return [(Prediction(prices[-1]), Confidence(0.0))] * prediction_periods
    
    # Ensemble averaging
    ensemble_predictions = []
    for period in range(prediction_periods):
        predictions = [method[period][0] for method in valid_methods]
        confidences = [method[period][1] for method in valid_methods]
        
        # Weighted average by confidence
        total_weight = sum(confidences)
        if total_weight > 0:
            weighted_prediction = sum(p * c for p, c in zip(predictions, confidences)) / total_weight
            avg_confidence = np.mean(confidences)
        else:
            weighted_prediction = np.mean(predictions)
            avg_confidence = 0.1
        
        ensemble_predictions.append((Prediction(weighted_prediction), Confidence(avg_confidence)))
    
    return ensemble_predictions


def trend_strength(prices: PriceSeries, window: int = 20) -> float:
    """
    Calculate mathematical trend strength.
    Returns value between 0 (no trend) and 1 (strong trend).
    """
    if len(prices) < window:
        return 0.0
    
    try:
        recent_prices = np.array(prices[-window:])
        x = np.arange(len(recent_prices))
        
        # Calculate trend line
        slope, _ = np.polyfit(x, recent_prices, 1)
        fitted = slope * x + np.mean(recent_prices)
        
        # Calculate R-squared as trend strength
        ss_res = np.sum((recent_prices - fitted) ** 2)
        ss_tot = np.sum((recent_prices - np.mean(recent_prices)) ** 2)
        
        if ss_tot == 0:
            return 0.0
        
        r_squared = 1.0 - (ss_res / ss_tot)
        return max(0.0, min(1.0, r_squared))
        
    except Exception:
        return 0.0