"""
Custom assertions for financial calculations testing.
Single responsibility: Test assertions with appropriate tolerances.
"""


import numpy as np
import pandas as pd


class FinancialAssertions:
    """Custom assertions for financial calculations."""

    DEFAULT_TOLERANCE = 1e-4  # 0.01% tolerance for financial calculations

    @staticmethod
    def assert_returns_equal(
        actual: float | np.ndarray | pd.Series,
        expected: float | np.ndarray | pd.Series,
        tolerance: float = DEFAULT_TOLERANCE,
        message: str = ""
    ) -> None:
        """Assert that returns are equal within tolerance."""
        if isinstance(actual, pd.Series):
            actual = actual.values
        if isinstance(expected, pd.Series):
            expected = expected.values

        np.testing.assert_allclose(
            actual, expected, rtol=tolerance,
            err_msg=f"Returns not equal within tolerance. {message}"
        )

    @staticmethod
    def assert_weights_valid(
        weights: dict[str, float] | pd.Series,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        sum_tolerance: float = 0.001
    ) -> None:
        """Assert that portfolio weights are valid."""
        if isinstance(weights, dict):
            weights = pd.Series(weights)

        # Check sum equals 1
        weight_sum = weights.sum()
        assert abs(weight_sum - 1.0) < sum_tolerance, \
            f"Weights sum to {weight_sum}, not 1.0"

        # Check individual weight constraints
        assert (weights >= min_weight).all(), \
            f"Some weights below minimum {min_weight}"
        assert (weights <= max_weight).all(), \
            f"Some weights above maximum {max_weight}"

    @staticmethod
    def assert_sharpe_ratio_valid(
        sharpe: float,
        min_expected: float = -3.0,
        max_expected: float = 3.0
    ) -> None:
        """Assert that Sharpe ratio is within reasonable bounds."""
        assert min_expected <= sharpe <= max_expected, \
            f"Sharpe ratio {sharpe} outside reasonable range [{min_expected}, {max_expected}]"

    @staticmethod
    def assert_volatility_valid(
        volatility: float,
        annualized: bool = True
    ) -> None:
        """Assert that volatility is within reasonable bounds."""
        max_vol = 1.0 if annualized else 0.1  # 100% annual or 10% daily
        assert 0 <= volatility <= max_vol, \
            f"Volatility {volatility} outside valid range [0, {max_vol}]"

    @staticmethod
    def assert_correlation_valid(correlation: float) -> None:
        """Assert that correlation is within [-1, 1]."""
        assert -1.0 <= correlation <= 1.0, \
            f"Correlation {correlation} outside valid range [-1, 1]"
