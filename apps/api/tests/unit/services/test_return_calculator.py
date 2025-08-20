"""
Unit tests for ReturnCalculator - Return metrics calculations.
100% coverage required for financial return calculations.
"""

import pytest
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta

from app.services.performance_modules.return_calculator import ReturnCalculator


@pytest.mark.financial
@pytest.mark.unit
@pytest.mark.critical
class TestReturnCalculator:
    """Test return calculation logic - CRITICAL for performance reporting."""
    
    @pytest.fixture
    def calculator(self):
        """Create a ReturnCalculator instance."""
        return ReturnCalculator()
    
    @pytest.fixture
    def sample_prices(self):
        """Create sample price series for testing."""
        dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
        prices = [100.0]
        
        # Generate realistic price movement
        for _ in range(251):
            change = np.random.normal(0.0005, 0.02)  # 0.05% daily return, 2% volatility
            prices.append(prices[-1] * (1 + change))
        
        return pd.Series(prices, index=dates)
    
    @pytest.fixture
    def portfolio_values(self):
        """Create sample portfolio values with cash flows."""
        dates = pd.date_range(start='2024-01-01', periods=12, freq='M')
        values = [100000, 102000, 105000, 103000, 107000, 110000,
                 108000, 112000, 115000, 113000, 118000, 120000]
        return pd.Series(values, index=dates)
    
    def test_calculate_simple_returns(self, calculator):
        """Test simple return calculation."""
        prices = pd.Series([100, 110, 121, 115, 120])
        returns = calculator.calculate_returns(prices.values.tolist())
        
        expected = [0.10, 0.10, -0.0496, 0.0435]  # Approximate values
        np.testing.assert_array_almost_equal(returns, expected, decimal=4)
        
        # Test single period
        single_return = calculator.calculate_simple_return(100, 110)
        assert single_return == 0.10
    
    def test_calculate_log_returns(self, calculator):
        """Test logarithmic return calculation."""
        prices = pd.Series([100, 110, 121, 115, 120])
        log_returns = calculator.calculate_log_returns(prices)
        
        # Log returns should be slightly different from simple returns
        simple_returns = calculator.calculate_returns(prices.values.tolist())
        assert not np.array_equal(log_returns, simple_returns)
        
        # Test properties of log returns
        # Sum of log returns = log of total return
        total_log_return = np.sum(log_returns)
        expected_total = np.log(120 / 100)
        assert total_log_return == pytest.approx(expected_total, rel=1e-4)
    
    def test_calculate_cumulative_returns(self, calculator, sample_prices):
        """Test cumulative return calculation."""
        returns = sample_prices.pct_change().dropna()
        cum_returns = calculator.calculate_cumulative_returns(returns)
        
        # First value should be 0 (no return yet)
        assert cum_returns.iloc[0] == 0
        
        # Last cumulative return should match total return
        total_return = (sample_prices.iloc[-1] / sample_prices.iloc[0]) - 1
        assert cum_returns.iloc[-1] == pytest.approx(total_return, rel=1e-4)
        
        # Cumulative returns should be monotonic if all returns positive
        positive_returns = pd.Series([0.01, 0.02, 0.015, 0.025])
        cum_positive = calculator.calculate_cumulative_returns(positive_returns)
        assert all(cum_positive.diff().dropna() > 0)
    
    def test_calculate_annualized_return(self, calculator):
        """Test annualized return calculation."""
        # Test with known values
        total_return = 0.20  # 20% total return
        
        # 1 year period
        annual_1y = calculator.calculate_annualized_return(total_return, days=365)
        assert annual_1y == pytest.approx(0.20, rel=1e-4)
        
        # 2 year period
        annual_2y = calculator.calculate_annualized_return(total_return, days=730)
        expected_2y = (1.20 ** (365/730)) - 1
        assert annual_2y == pytest.approx(expected_2y, rel=1e-4)
        
        # 6 month period
        annual_6m = calculator.calculate_annualized_return(total_return, days=183)
        expected_6m = (1.20 ** (365/183)) - 1
        assert annual_6m == pytest.approx(expected_6m, rel=1e-4)
    
    def test_calculate_time_weighted_return(self, calculator):
        """Test time-weighted return (TWR) calculation."""
        # Portfolio values and cash flows
        values = [100000, 105000, 115000, 112000, 120000]
        dates = pd.date_range('2024-01-01', periods=5, freq='M')
        
        cash_flows = [
            (dates[2], 5000),   # Deposit after month 2
            (dates[3], -2000)   # Withdrawal after month 3
        ]
        
        twr = calculator.calculate_time_weighted_return(values, dates, cash_flows)
        
        # TWR should account for cash flows
        # Period 1: 105000/100000 = 1.05
        # Period 2: 110000/105000 = 1.0476 (adjusting for deposit)
        # Period 3: 114000/115000 = 0.9913 (adjusting for withdrawal)
        # Period 4: 120000/112000 = 1.0714
        # TWR = product - 1
        
        assert 0.15 <= twr <= 0.25  # Reasonable range
    
    def test_calculate_money_weighted_return(self, calculator):
        """Test money-weighted return (MWR/IRR) calculation."""
        # Cash flows with dates
        cash_flows = [
            (-100000, datetime(2024, 1, 1)),   # Initial investment
            (-20000, datetime(2024, 3, 1)),    # Additional investment
            (5000, datetime(2024, 6, 1)),      # Dividend
            (130000, datetime(2024, 12, 31))   # Final value
        ]
        
        mwr = calculator.calculate_money_weighted_return(cash_flows)
        
        # MWR should be positive for this profitable scenario
        assert 0.05 <= mwr <= 0.15  # Reasonable range for annual return
        
        # Test with loss scenario
        loss_flows = [
            (-100000, datetime(2024, 1, 1)),
            (90000, datetime(2024, 12, 31))
        ]
        
        mwr_loss = calculator.calculate_money_weighted_return(loss_flows)
        assert mwr_loss < 0  # Should be negative
    
    def test_calculate_daily_returns(self, calculator, sample_prices):
        """Test daily return calculation."""
        daily_returns = calculator.calculate_daily_returns(sample_prices)
        
        # Length should be one less than prices
        assert len(daily_returns) == len(sample_prices) - 1
        
        # First return should match manual calculation
        expected_first = (sample_prices.iloc[1] / sample_prices.iloc[0]) - 1
        assert daily_returns.iloc[0] == pytest.approx(expected_first, rel=1e-6)
        
        # Average daily return should be small but positive
        avg_return = daily_returns.mean()
        assert -0.01 <= avg_return <= 0.01
    
    def test_calculate_monthly_returns(self, calculator, sample_prices):
        """Test monthly return calculation."""
        monthly_returns = calculator.calculate_monthly_returns(sample_prices)
        
        # Should have fewer values than daily
        assert len(monthly_returns) < len(sample_prices) / 20
        
        # Monthly returns should be larger in magnitude than daily
        assert monthly_returns.std() > sample_prices.pct_change().std()
    
    def test_calculate_ytd_return(self, calculator):
        """Test year-to-date return calculation."""
        # Create prices spanning multiple years
        dates = pd.date_range('2023-06-01', '2024-06-01', freq='D')
        prices = pd.Series(range(100, 100 + len(dates)), index=dates)
        
        # Calculate YTD for 2024
        ytd_return = calculator.calculate_ytd_return(prices, year=2024)
        
        # Get prices at year boundaries
        start_2024_price = prices[prices.index >= '2024-01-01'].iloc[0]
        latest_2024_price = prices[prices.index.year == 2024].iloc[-1]
        expected_ytd = (latest_2024_price / start_2024_price) - 1
        
        assert ytd_return == pytest.approx(expected_ytd, rel=1e-4)
    
    def test_calculate_rolling_returns(self, calculator, sample_prices):
        """Test rolling return calculation."""
        # Calculate 30-day rolling returns
        rolling_30d = calculator.calculate_rolling_returns(sample_prices, window=30)
        
        # Length should match input (with NaN for initial window)
        assert len(rolling_30d) == len(sample_prices)
        
        # After warm-up period, should have no NaN
        assert not rolling_30d[30:].isna().any()
        
        # Rolling returns should be smoother than daily
        daily_returns = sample_prices.pct_change()
        assert rolling_30d[30:].std() < daily_returns.std()
    
    @pytest.mark.parametrize("period,expected_periods", [
        ('daily', 252),
        ('weekly', 52),
        ('monthly', 12),
        ('quarterly', 4),
        ('yearly', 1)
    ])
    def test_period_returns(self, calculator, period, expected_periods):
        """Test different period return calculations."""
        # Create one year of daily data
        dates = pd.date_range('2024-01-01', periods=365, freq='D')
        prices = pd.Series(range(100, 465), index=dates)  # Linear growth
        
        period_returns = calculator.calculate_period_returns(prices, period=period)
        
        # Check approximate number of periods
        assert abs(len(period_returns) - expected_periods) <= 2
    
    def test_calculate_excess_returns(self, calculator):
        """Test excess return calculation over benchmark."""
        portfolio_returns = pd.Series([0.02, 0.01, -0.01, 0.03, 0.015])
        benchmark_returns = pd.Series([0.015, 0.005, -0.005, 0.02, 0.01])
        
        excess = calculator.calculate_excess_returns(portfolio_returns, benchmark_returns)
        
        # Check excess returns are correct
        expected = portfolio_returns - benchmark_returns
        pd.testing.assert_series_equal(excess, expected)
        
        # Average excess should be positive for outperformance
        assert excess.mean() > 0
    
    def test_calculate_active_return(self, calculator):
        """Test active return (vs benchmark) calculation."""
        portfolio_return = 0.12  # 12% return
        benchmark_return = 0.08  # 8% return
        
        active_return = calculator.calculate_active_return(portfolio_return, benchmark_return)
        assert active_return == 0.04
        
        # Test underperformance
        active_neg = calculator.calculate_active_return(0.05, 0.10)
        assert active_neg == -0.05
    
    def test_calculate_tracking_error(self, calculator):
        """Test tracking error calculation."""
        portfolio_returns = pd.Series([0.02, 0.01, -0.01, 0.03, 0.015, 0.025, -0.005])
        benchmark_returns = pd.Series([0.015, 0.008, -0.008, 0.025, 0.012, 0.022, -0.003])
        
        tracking_error = calculator.calculate_tracking_error(
            portfolio_returns, 
            benchmark_returns,
            annualized=True
        )
        
        # Tracking error should be positive
        assert tracking_error > 0
        
        # Should be reasonable (typically < 10% annually)
        assert tracking_error < 0.10
        
        # Perfect tracking should have zero error
        perfect_tracking = calculator.calculate_tracking_error(
            benchmark_returns,
            benchmark_returns
        )
        assert perfect_tracking == 0
    
    def test_return_distribution_metrics(self, calculator, sample_prices):
        """Test return distribution analysis."""
        returns = sample_prices.pct_change().dropna()
        
        metrics = calculator.analyze_return_distribution(returns)
        
        # Check all metrics are present
        expected_metrics = ['mean', 'median', 'std', 'skew', 'kurtosis', 
                          'min', 'max', 'percentile_5', 'percentile_95']
        
        for metric in expected_metrics:
            assert metric in metrics
            assert not np.isnan(metrics[metric])
        
        # Check relationships
        assert metrics['min'] <= metrics['percentile_5']
        assert metrics['percentile_5'] <= metrics['median']
        assert metrics['median'] <= metrics['percentile_95']
        assert metrics['percentile_95'] <= metrics['max']
    
    def test_compound_return_calculation(self, calculator):
        """Test compound return calculation."""
        # Series of returns
        returns = [0.10, 0.05, -0.03, 0.08, 0.02]
        
        compound = calculator.calculate_compound_return(returns)
        
        # Manual calculation: (1.1 * 1.05 * 0.97 * 1.08 * 1.02) - 1
        expected = 1.1 * 1.05 * 0.97 * 1.08 * 1.02 - 1
        assert compound == pytest.approx(expected, rel=1e-6)
        
        # Test with all positive returns
        positive_returns = [0.05, 0.03, 0.04, 0.02]
        compound_pos = calculator.calculate_compound_return(positive_returns)
        
        # Should be greater than sum (due to compounding)
        assert compound_pos > sum(positive_returns)
    
    def test_handle_edge_cases(self, calculator):
        """Test handling of edge cases."""
        # Empty series
        empty_series = pd.Series([])
        with pytest.raises(ValueError, match="Empty"):
            calculator.calculate_returns([])
        
        # Single value
        single_value = pd.Series([100])
        returns = calculator.calculate_daily_returns(single_value)
        assert len(returns) == 0
        
        # All same values (zero returns)
        constant_prices = pd.Series([100] * 10)
        returns = calculator.calculate_daily_returns(constant_prices)
        assert all(returns == 0)
        
        # Negative prices (should handle or raise error)
        with pytest.raises(ValueError, match="Negative"):
            calculator.calculate_log_returns(pd.Series([100, -50, 75]))