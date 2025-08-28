"""
Advanced return calculations including time-weighted and money-weighted returns.
Handles cash flows, IRR calculations, and distribution analysis.
"""

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AdvancedReturnCalculator:
    """Calculate advanced return metrics including cash flow adjustments."""

    @staticmethod
    def calculate_time_weighted_return(
        values: list[float],
        dates: pd.DatetimeIndex,
        cash_flows: list[tuple[pd.Timestamp, float]]
    ) -> float:
        """
        Calculate time-weighted return accounting for cash flows.
        Segments periods by cash flows and compounds sub-period returns.

        Args:
            values: Portfolio values at each date
            dates: Dates corresponding to values
            cash_flows: List of (date, amount) tuples for cash flows

        Returns:
            Time-weighted return as decimal
        """
        if len(values) < 2:
            return 0.0

        # Create DataFrame for easier manipulation
        df = pd.DataFrame({'value': values}, index=dates)

        # If no cash flows, simple return
        if not cash_flows:
            return (values[-1] / values[0]) - 1

        # Sort cash flows by date
        sorted_cf = sorted(cash_flows, key=lambda x: x[0])

        # Segment periods by cash flows
        segments = []
        start_idx = 0

        for cf_date, _cf_amount in sorted_cf:
            # Find the index closest to cash flow date
            cf_idx = df.index.get_indexer([cf_date], method='nearest')[0]

            if cf_idx > start_idx:
                # Calculate return for this segment
                segment_return = (
                    df.iloc[cf_idx]['value'] / df.iloc[start_idx]['value']
                ) - 1
                segments.append(1 + segment_return)
                start_idx = cf_idx

        # Final segment from last cash flow to end
        if start_idx < len(df) - 1:
            final_return = (
                df.iloc[-1]['value'] / df.iloc[start_idx]['value']
            ) - 1
            segments.append(1 + final_return)

        # Compound all segment returns
        if not segments:
            return (values[-1] / values[0]) - 1

        twr = np.prod(segments) - 1
        return float(twr)

    @staticmethod
    def calculate_money_weighted_return(
        cash_flows: list[tuple[float, datetime]]
    ) -> float:
        """
        Calculate money-weighted return (IRR) using numerical optimization.

        Args:
            cash_flows: List of (amount, date) tuples

        Returns:
            IRR as decimal annual rate
        """
        if len(cash_flows) < 2:
            return 0.0

        try:
            from scipy.optimize import minimize_scalar
        except ImportError:
            logger.warning("scipy not available, using simplified IRR calculation")
            return AdvancedReturnCalculator._simple_irr_fallback(cash_flows)

        # Sort cash flows by date
        sorted_cf = sorted(cash_flows, key=lambda x: x[1])

        # Get the first date as reference
        first_date = sorted_cf[0][1]

        # Convert cash flows to (amount, years_from_start) format
        cf_values = []
        cf_times = []
        for amount, date in sorted_cf:
            years_from_start = (date - first_date).days / 365.0
            cf_values.append(amount)
            cf_times.append(years_from_start)

        # Define NPV function
        def npv(rate):
            """Calculate NPV at given rate."""
            total = 0
            for amount, t in zip(cf_values, cf_times, strict=False):
                if t == 0:
                    total += amount
                else:
                    total += amount / ((1 + rate) ** t)
            return total

        # Define objective function (squared NPV for minimization)
        def objective(rate):
            """Objective function to minimize (squared NPV)."""
            return npv(rate) ** 2

        # Try to find IRR using optimization
        # Search between -99% and 300% annual return
        result = minimize_scalar(
            objective, 
            bounds=(-0.99, 3.0), 
            method='bounded'
        )

        if result.success and abs(npv(result.x)) < 0.01:
            return float(result.x)

        # If optimization fails, try different initial guesses
        for guess in [0.0, 0.1, -0.1, 0.5, -0.5]:
            result = minimize_scalar(
                objective,
                bounds=(guess - 0.5, guess + 0.5),
                method='bounded'
            )
            if result.success and abs(npv(result.x)) < 0.01:
                return float(result.x)

        # Fallback to simple approximation if optimization fails
        logger.warning("IRR optimization failed, using approximation")
        return AdvancedReturnCalculator._simple_irr_fallback(cash_flows)

    @staticmethod
    def _simple_irr_fallback(
        cash_flows: list[tuple[float, datetime]]
    ) -> float:
        """
        Simple IRR approximation when scipy is not available.

        Args:
            cash_flows: List of (amount, date) tuples

        Returns:
            Approximate IRR as decimal
        """
        total_invested = sum(cf[0] for cf in cash_flows if cf[0] < 0)
        total_returned = sum(cf[0] for cf in cash_flows if cf[0] > 0)

        if total_invested == 0:
            return 0.0

        simple_return = (total_returned / abs(total_invested)) - 1
        
        if len(cash_flows) < 2:
            return simple_return
            
        first_date = min(cf[1] for cf in cash_flows)
        last_date = max(cf[1] for cf in cash_flows)
        years = (last_date - first_date).days / 365.0

        if years <= 0:
            return simple_return

        return (1 + simple_return) ** (1 / years) - 1

    @staticmethod
    def calculate_return_distribution_metrics(
        returns: np.ndarray
    ) -> dict[str, float]:
        """
        Calculate return distribution metrics.

        Args:
            returns: Array of returns

        Returns:
            Dictionary with distribution metrics
        """
        if len(returns) == 0:
            return {
                'mean': 0.0,
                'std': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0,
                'min': 0.0,
                'max': 0.0
            }

        try:
            from scipy import stats
            
            return {
                'mean': float(np.mean(returns)),
                'std': float(np.std(returns)),
                'skewness': float(stats.skew(returns)),
                'kurtosis': float(stats.kurtosis(returns)),
                'min': float(np.min(returns)),
                'max': float(np.max(returns))
            }
        except ImportError:
            # Fallback without scipy
            return {
                'mean': float(np.mean(returns)),
                'std': float(np.std(returns)),
                'skewness': 0.0,  # Requires scipy
                'kurtosis': 0.0,  # Requires scipy
                'min': float(np.min(returns)),
                'max': float(np.max(returns))
            }

    @staticmethod
    def analyze_return_distribution(
        returns: pd.Series
    ) -> dict[str, float]:
        """
        Analyze return distribution metrics.

        Args:
            returns: Series of returns

        Returns:
            Dictionary with distribution metrics
        """
        if len(returns) == 0:
            return {
                'mean': 0.0,
                'median': 0.0,
                'std': 0.0,
                'skew': 0.0,
                'kurtosis': 0.0,
                'min': 0.0,
                'max': 0.0,
                'percentile_5': 0.0,
                'percentile_95': 0.0
            }

        try:
            from scipy import stats
            
            return {
                'mean': float(returns.mean()),
                'median': float(returns.median()),
                'std': float(returns.std()),
                'skew': float(stats.skew(returns)),
                'kurtosis': float(stats.kurtosis(returns)),
                'min': float(returns.min()),
                'max': float(returns.max()),
                'percentile_5': float(returns.quantile(0.05)),
                'percentile_95': float(returns.quantile(0.95))
            }
        except ImportError:
            # Fallback without scipy
            return {
                'mean': float(returns.mean()),
                'median': float(returns.median()),
                'std': float(returns.std()),
                'skew': 0.0,  # Requires scipy
                'kurtosis': 0.0,  # Requires scipy
                'min': float(returns.min()),
                'max': float(returns.max()),
                'percentile_5': float(returns.quantile(0.05)),
                'percentile_95': float(returns.quantile(0.95))
            }