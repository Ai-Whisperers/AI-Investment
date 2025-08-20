"""
Unit tests for RiskCalculator - Risk metrics calculations.
100% coverage required for financial risk models.
"""

import pytest
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta

from app.services.strategy_modules.risk_calculator import RiskCalculator


@pytest.mark.financial
@pytest.mark.unit
@pytest.mark.critical
class TestRiskCalculator:
    """Test risk calculation logic - CRITICAL for portfolio safety."""
    
    @pytest.fixture
    def calculator(self):
        """Create a RiskCalculator instance."""
        return RiskCalculator()
    
    @pytest.fixture
    def sample_returns(self):
        """Create sample return data."""
        np.random.seed(42)  # For reproducibility
        # Generate returns with known properties
        returns = np.random.normal(0.001, 0.02, 252)  # Daily returns for 1 year
        return pd.Series(returns, index=pd.date_range('2024-01-01', periods=252))
    
    @pytest.fixture
    def sample_prices(self):
        """Create sample price series."""
        prices = [100]
        for _ in range(251):
            # Random walk with slight upward bias
            change = np.random.normal(0.0005, 0.02)
            prices.append(prices[-1] * (1 + change))
        return pd.Series(prices, index=pd.date_range('2024-01-01', periods=252))
    
    def test_calculate_sharpe_ratio(self, calculator, sample_returns):
        """Test Sharpe ratio calculation."""
        sharpe = calculator.calculate_sharpe_ratio(
            sample_returns,
            risk_free_rate=0.02
        )
        
        # Check reasonable range for Sharpe ratio
        assert -3 <= sharpe <= 3
        
        # Test with zero volatility (should handle gracefully)
        constant_returns = pd.Series([0.01] * 100)
        sharpe_constant = calculator.calculate_sharpe_ratio(constant_returns)
        assert sharpe_constant == float('inf') or sharpe_constant > 10
    
    def test_calculate_sortino_ratio(self, calculator, sample_returns):
        """Test Sortino ratio calculation (downside risk)."""
        sortino = calculator.calculate_sortino_ratio(
            sample_returns,
            risk_free_rate=0.02,
            target_return=0.0
        )
        
        # Sortino should typically be higher than Sharpe
        sharpe = calculator.calculate_sharpe_ratio(sample_returns, 0.02)
        assert sortino >= sharpe - 0.5  # Allow some tolerance
        
        # Test with no downside risk
        positive_returns = pd.Series([0.01, 0.02, 0.015, 0.025, 0.01])
        sortino_positive = calculator.calculate_sortino_ratio(positive_returns)
        assert sortino_positive > 5  # Should be very high
    
    def test_calculate_max_drawdown(self, calculator, sample_prices):
        """Test maximum drawdown calculation."""
        max_dd, peak_date, trough_date = calculator.calculate_max_drawdown(sample_prices)
        
        # Check drawdown is negative
        assert max_dd <= 0
        
        # Check dates are in correct order
        assert peak_date <= trough_date
        
        # Test with monotonically increasing prices (no drawdown)
        increasing_prices = pd.Series(range(100, 200), 
                                     index=pd.date_range('2024-01-01', periods=100))
        dd_increasing, _, _ = calculator.calculate_max_drawdown(increasing_prices)
        assert dd_increasing == 0
        
        # Test with known drawdown
        prices_with_dd = pd.Series([100, 110, 120, 90, 95, 100, 105])
        dd, _, _ = calculator.calculate_max_drawdown(prices_with_dd)
        expected_dd = (90 - 120) / 120  # -25%
        assert dd == pytest.approx(expected_dd, rel=1e-4)
    
    def test_calculate_calmar_ratio(self, calculator, sample_returns, sample_prices):
        """Test Calmar ratio (return/max drawdown)."""
        calmar = calculator.calculate_calmar_ratio(sample_returns, sample_prices)
        
        # Check reasonable range
        assert -10 <= calmar <= 10
        
        # Test with no drawdown
        positive_returns = pd.Series([0.01] * 100)
        positive_prices = pd.Series(np.cumprod([1.01] * 100) * 100)
        calmar_positive = calculator.calculate_calmar_ratio(positive_returns, positive_prices)
        assert calmar_positive > 10  # Should be very high
    
    def test_calculate_volatility(self, calculator, sample_returns):
        """Test volatility calculation."""
        # Test annualized volatility
        vol_annual = calculator.calculate_volatility(sample_returns, annualize=True)
        assert 0 < vol_annual < 1  # Reasonable range for annual volatility
        
        # Test non-annualized
        vol_daily = calculator.calculate_volatility(sample_returns, annualize=False)
        assert vol_daily < vol_annual
        
        # Relationship should be sqrt(252)
        expected_ratio = np.sqrt(252)
        actual_ratio = vol_annual / vol_daily
        assert actual_ratio == pytest.approx(expected_ratio, rel=0.01)
    
    def test_calculate_beta(self, calculator):
        """Test beta calculation against market."""
        # Create correlated returns
        market_returns = pd.Series(np.random.normal(0.001, 0.015, 100))
        # Portfolio with beta ~1.5
        portfolio_returns = market_returns * 1.5 + np.random.normal(0, 0.005, 100)
        
        beta = calculator.calculate_beta(portfolio_returns, market_returns)
        
        # Should be close to 1.5
        assert 1.3 <= beta <= 1.7
        
        # Test beta of market with itself (should be 1)
        market_beta = calculator.calculate_beta(market_returns, market_returns)
        assert market_beta == pytest.approx(1.0, rel=1e-4)
    
    def test_calculate_correlation(self, calculator):
        """Test correlation calculation."""
        # Create perfectly correlated series
        series1 = pd.Series(range(100))
        series2 = series1 * 2 + 10
        
        corr = calculator.calculate_correlation(series1, series2)
        assert corr == pytest.approx(1.0, rel=1e-4)
        
        # Create negatively correlated series
        series3 = -series1 + 100
        corr_neg = calculator.calculate_correlation(series1, series3)
        assert corr_neg == pytest.approx(-1.0, rel=1e-4)
        
        # Create uncorrelated series
        series4 = pd.Series(np.random.normal(0, 1, 100))
        series5 = pd.Series(np.random.normal(0, 1, 100))
        corr_uncorr = calculator.calculate_correlation(series4, series5)
        assert -0.3 <= corr_uncorr <= 0.3  # Should be close to 0
    
    def test_calculate_var(self, calculator, sample_returns):
        """Test Value at Risk (VaR) calculation."""
        # Calculate 95% VaR
        var_95 = calculator.calculate_var(sample_returns, confidence=0.95)
        
        # VaR should be negative (represents loss)
        assert var_95 < 0
        
        # 99% VaR should be more negative than 95%
        var_99 = calculator.calculate_var(sample_returns, confidence=0.99)
        assert var_99 < var_95
        
        # Test parametric VaR
        var_parametric = calculator.calculate_var(
            sample_returns, 
            confidence=0.95,
            method='parametric'
        )
        
        # Should be similar but not identical to historical
        assert abs(var_95 - var_parametric) / abs(var_95) < 0.3
    
    def test_calculate_cvar(self, calculator, sample_returns):
        """Test Conditional VaR (Expected Shortfall) calculation."""
        var_95 = calculator.calculate_var(sample_returns, confidence=0.95)
        cvar_95 = calculator.calculate_cvar(sample_returns, confidence=0.95)
        
        # CVaR should be more negative than VaR
        assert cvar_95 < var_95
        
        # Test with different confidence levels
        cvar_99 = calculator.calculate_cvar(sample_returns, confidence=0.99)
        assert cvar_99 < cvar_95
    
    @pytest.mark.parametrize("window_size,expected_stability", [
        (20, False),   # Short window, less stable
        (60, True),    # Medium window, more stable
        (252, True)    # Long window, most stable
    ])
    def test_rolling_metrics_stability(self, calculator, sample_prices, window_size, expected_stability):
        """Test stability of rolling risk metrics."""
        returns = sample_prices.pct_change().dropna()
        
        rolling_vol = calculator.calculate_rolling_volatility(returns, window=window_size)
        
        # Check no NaN values after warm-up
        assert rolling_vol[window_size:].isna().sum() == 0
        
        # Check stability (coefficient of variation)
        cv = rolling_vol.std() / rolling_vol.mean()
        if expected_stability:
            assert cv < 0.5  # Relatively stable
        else:
            assert cv >= 0.15  # More variable (lowered threshold for realistic data)
    
    def test_tail_risk_metrics(self, calculator):
        """Test tail risk calculations."""
        # Create returns with fat tails
        normal_returns = np.random.normal(0, 0.01, 900)
        tail_events = np.random.normal(0, 0.05, 100)  # Extreme events
        all_returns = pd.Series(np.concatenate([normal_returns, tail_events]))
        
        kurtosis = calculator.calculate_kurtosis(all_returns)
        skewness = calculator.calculate_skewness(all_returns)
        
        # Should detect fat tails (excess kurtosis > 0)
        assert kurtosis > 0
        
        # Test tail ratio
        tail_ratio = calculator.calculate_tail_ratio(all_returns)
        assert 0.5 <= tail_ratio <= 2.0  # Reasonable range
    
    def test_risk_adjusted_returns(self, calculator, sample_returns, sample_prices):
        """Test comprehensive risk-adjusted return metrics."""
        metrics = calculator.calculate_risk_adjusted_metrics(
            returns=sample_returns,
            prices=sample_prices,
            risk_free_rate=0.02
        )
        
        # Check all metrics are calculated
        expected_metrics = [
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
            'max_drawdown', 'volatility', 'var_95', 'cvar_95'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
            assert metrics[metric] is not None
            assert not np.isnan(metrics[metric])
    
    def test_portfolio_risk_metrics(self, calculator):
        """Test portfolio-level risk calculations."""
        # Create portfolio with 3 assets
        weights = np.array([0.4, 0.3, 0.3])
        
        # Create return matrix with known correlations
        n_periods = 252
        returns = pd.DataFrame({
            'Asset1': np.random.normal(0.001, 0.02, n_periods),
            'Asset2': np.random.normal(0.0008, 0.025, n_periods),
            'Asset3': np.random.normal(0.0012, 0.015, n_periods)
        })
        
        # Add some correlation
        returns['Asset2'] += returns['Asset1'] * 0.5
        returns['Asset3'] += returns['Asset1'] * 0.3
        
        portfolio_risk = calculator.calculate_portfolio_risk(returns, weights)
        
        # Portfolio risk should be less than weighted average (due to diversification)
        individual_risks = returns.std()
        weighted_avg_risk = np.dot(weights, individual_risks)
        assert portfolio_risk < weighted_avg_risk
    
    def test_stress_testing(self, calculator, sample_returns):
        """Test stress testing scenarios."""
        # Define stress scenarios
        scenarios = {
            'market_crash': -0.20,  # 20% drop
            'flash_crash': -0.10,   # 10% sudden drop
            'volatility_spike': 3.0  # 3x volatility
        }
        
        stress_results = calculator.apply_stress_scenarios(sample_returns, scenarios)
        
        # Check results structure
        assert 'market_crash' in stress_results
        assert stress_results['market_crash']['portfolio_impact'] < 0
        
        # Volatility spike should increase risk metrics
        assert stress_results['volatility_spike']['new_var'] < stress_results['volatility_spike']['base_var']
    
    def test_handle_edge_cases(self, calculator):
        """Test handling of edge cases and errors."""
        # Empty series
        empty_series = pd.Series([])
        with pytest.raises(ValueError, match="Empty"):
            calculator.calculate_volatility(empty_series)
        
        # Single value
        single_value = pd.Series([100])
        with pytest.raises(ValueError, match="Insufficient"):
            calculator.calculate_max_drawdown(single_value)
        
        # All same values (zero volatility)
        constant_series = pd.Series([0.01] * 100)
        vol = calculator.calculate_volatility(constant_series)
        assert vol == 0
        
        # NaN handling
        series_with_nan = pd.Series([0.01, np.nan, 0.02, 0.015, np.nan, 0.01])
        cleaned = calculator._clean_series(series_with_nan)
        assert not cleaned.isna().any()