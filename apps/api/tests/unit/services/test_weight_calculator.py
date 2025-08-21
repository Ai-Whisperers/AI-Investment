"""
Unit tests for WeightCalculator - Portfolio weight calculations.
100% coverage required for financial calculations.
"""


import numpy as np
import pandas as pd
import pytest

from app.services.strategy_modules.weight_calculator import WeightCalculator


@pytest.mark.financial
@pytest.mark.unit
class TestWeightCalculator:
    """Test portfolio weight calculation logic."""

    @pytest.fixture
    def calculator(self):
        """Create a WeightCalculator instance."""
        return WeightCalculator()

    @pytest.fixture
    def sample_data(self):
        """Create sample price data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        data = {
            'AAPL': pd.Series(np.random.uniform(140, 160, 30), index=dates),
            'GOOGL': pd.Series(np.random.uniform(2700, 2900, 30), index=dates),
            'MSFT': pd.Series(np.random.uniform(380, 420, 30), index=dates)
        }
        return pd.DataFrame(data)

    def test_calculate_equal_weights(self, calculator):
        """Test equal weight calculation across assets."""
        assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']
        weights = calculator.calculate_equal_weights(assets)

        assert len(weights) == 4
        assert all(w == 0.25 for w in weights.values())
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_calculate_market_cap_weights(self, calculator):
        """Test market cap weighted portfolio calculation."""
        market_caps = {
            'AAPL': 3000000000000,  # $3T
            'MSFT': 2800000000000,  # $2.8T
            'GOOGL': 1700000000000, # $1.7T
            'AMZN': 1600000000000   # $1.6T
        }

        weights = calculator.calculate_market_cap_weights(market_caps)

        # Check weights sum to 1
        assert sum(weights.values()) == pytest.approx(1.0)

        # Check AAPL has highest weight
        assert weights['AAPL'] > weights['MSFT']
        assert weights['AAPL'] > weights['GOOGL']

        # Check proportions
        total_cap = sum(market_caps.values())
        expected_aapl = 3000000000000 / total_cap
        assert weights['AAPL'] == pytest.approx(expected_aapl, rel=1e-4)

    def test_calculate_risk_parity_weights(self, calculator, sample_data):
        """Test risk parity weight calculation."""
        weights = calculator.calculate_risk_parity_weights(sample_data)

        # Check weights sum to 1
        assert sum(weights.values()) == pytest.approx(1.0, rel=1e-2)

        # Check all weights are positive
        assert all(w > 0 for w in weights.values())

        # Check no weight exceeds reasonable bounds
        assert all(0.01 <= w <= 0.8 for w in weights.values())

    def test_calculate_minimum_variance_weights(self, calculator, sample_data):
        """Test minimum variance portfolio calculation."""
        weights = calculator.calculate_minimum_variance_weights(sample_data)

        # Check weights sum to 1
        assert sum(weights.values()) == pytest.approx(1.0, rel=1e-2)

        # Check all weights are non-negative (long-only)
        assert all(w >= 0 for w in weights.values())

    @pytest.mark.parametrize("method,expected_range", [
        ("equal", (0.33, 0.34)),  # 3 assets in sample_data, so ~0.333 each
        ("momentum", (0.0, 0.6)),
        ("volatility", (0.1, 0.5))
    ])
    def test_weight_calculation_methods(self, calculator, sample_data, method, expected_range):
        """Test different weight calculation methods."""
        weights = calculator.calculate_weights(sample_data, method=method)

        assert sum(weights.values()) == pytest.approx(1.0, rel=1e-2)

        for weight in weights.values():
            assert expected_range[0] <= weight <= expected_range[1]

    def test_apply_weight_constraints(self, calculator):
        """Test weight constraint application."""
        initial_weights = {
            'AAPL': 0.6,   # Over max
            'GOOGL': 0.35,
            'MSFT': 0.03,  # Under min
            'AMZN': 0.02   # Under min
        }

        constraints = {
            'min_weight': 0.05,
            'max_weight': 0.40,
            'max_concentration': 0.60
        }

        adjusted = calculator.apply_constraints(initial_weights, constraints)

        # Check constraints are respected (with small tolerance for floating point)
        assert all(w >= 0.05 - 1e-10 for w in adjusted.values())
        assert all(w <= 0.40 + 1e-10 for w in adjusted.values())
        assert sum(adjusted.values()) == pytest.approx(1.0)

    def test_calculate_momentum_weights(self, calculator, sample_data):
        """Test momentum-based weight calculation."""
        # Add trend to data
        for col in sample_data.columns:
            trend = np.linspace(0, 10, len(sample_data))
            if col == 'AAPL':
                sample_data[col] += trend  # Strong uptrend
            elif col == 'GOOGL':
                sample_data[col] -= trend  # Downtrend

        weights = calculator.calculate_momentum_weights(sample_data, lookback=20)

        # AAPL should have highest weight due to momentum
        assert weights['AAPL'] > weights['GOOGL']
        assert weights['AAPL'] > weights['MSFT']
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_calculate_volatility_adjusted_weights(self, calculator):
        """Test inverse volatility weighting."""
        volatilities = {
            'AAPL': 0.25,   # High vol
            'GOOGL': 0.20,  # Medium vol
            'MSFT': 0.15,   # Low vol
            'AMZN': 0.30    # Very high vol
        }

        weights = calculator.calculate_volatility_adjusted_weights(volatilities)

        # Lower volatility should have higher weight
        assert weights['MSFT'] > weights['AAPL']
        assert weights['MSFT'] > weights['AMZN']
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_handle_empty_data(self, calculator):
        """Test handling of empty or invalid data."""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="Empty data"):
            calculator.calculate_weights(empty_df)

    def test_handle_single_asset(self, calculator):
        """Test weight calculation with single asset."""
        single_asset = ['AAPL']
        weights = calculator.calculate_equal_weights(single_asset)

        assert weights['AAPL'] == 1.0
        assert len(weights) == 1

    def test_rebalancing_calculation(self, calculator):
        """Test portfolio rebalancing calculation."""
        current_weights = {
            'AAPL': 0.35,
            'GOOGL': 0.25,
            'MSFT': 0.30,
            'AMZN': 0.10
        }

        target_weights = {
            'AAPL': 0.25,
            'GOOGL': 0.25,
            'MSFT': 0.25,
            'AMZN': 0.25
        }

        trades = calculator.calculate_rebalancing_trades(
            current_weights,
            target_weights,
            portfolio_value=100000
        )

        # Check trades sum to approximately zero (buys = sells)
        total_trades = sum(trades.values())
        assert abs(total_trades) < 100  # Small tolerance for rounding

        # Check AAPL needs to sell (current > target)
        assert trades['AAPL'] < 0

        # Check AMZN needs to buy (current < target)
        assert trades['AMZN'] > 0

    def test_weight_precision(self, calculator):
        """Test weight calculation precision and rounding."""
        assets = ['A', 'B', 'C']
        weights = calculator.calculate_equal_weights(assets, precision=4)

        # Check weights sum to 1
        assert sum(weights.values()) == pytest.approx(1.0, rel=1e-4)

        # Check each weight is approximately 1/3
        for w in weights.values():
            assert w == pytest.approx(0.3333, abs=0.001)

    @pytest.mark.parametrize("total_value,num_assets,min_position", [
        (10000, 10, 100),
        (100000, 50, 500),
        (1000000, 100, 1000)
    ])
    def test_position_sizing(self, calculator, total_value, num_assets, min_position):
        """Test position sizing with minimum thresholds."""
        assets = [f"ASSET{i}" for i in range(num_assets)]
        weights = calculator.calculate_equal_weights(assets)

        positions = calculator.calculate_position_sizes(
            weights,
            total_value,
            min_position_size=min_position
        )

        # Check all positions meet minimum size
        for position in positions.values():
            assert position >= min_position or position == 0

        # Check total allocation is close to total value
        total_allocated = sum(positions.values())
        assert total_allocated <= total_value
        assert total_allocated >= total_value * 0.95  # At least 95% allocated
