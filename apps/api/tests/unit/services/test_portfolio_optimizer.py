"""Unit tests for portfolio optimizer module."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.strategy_modules.portfolio_optimizer import PortfolioOptimizer


@pytest.mark.unit
class TestPortfolioOptimizer:
    """Test suite for portfolio optimizer."""

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data."""
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']
        data = {}
        for asset in assets:
            prices = 100 * (1 + np.random.randn(100).cumsum() * 0.01)
            data[asset] = prices
        return pd.DataFrame(data, index=dates)

    @pytest.fixture
    def optimizer(self):
        """Create portfolio optimizer instance."""
        return PortfolioOptimizer()

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer is not None
        assert hasattr(optimizer, 'optimize')

    def test_optimize_portfolio_equal_weights(self, optimizer, sample_prices):
        """Test portfolio optimization with equal weights."""
        result = optimizer.optimize(
            prices=sample_prices,
            method='equal_weight',
            risk_free_rate=0.02
        )
        
        assert 'weights' in result
        assert 'expected_return' in result
        assert 'volatility' in result
        assert 'sharpe_ratio' in result
        
        # Check weights sum to 1
        assert abs(sum(result['weights'].values()) - 1.0) < 0.001
        
        # Check all weights are positive
        assert all(w >= 0 for w in result['weights'].values())

    def test_optimize_portfolio_max_sharpe(self, optimizer, sample_prices):
        """Test maximum Sharpe ratio optimization."""
        result = optimizer.optimize(
            prices=sample_prices,
            method='max_sharpe',
            risk_free_rate=0.02
        )
        
        assert 'weights' in result
        assert result['sharpe_ratio'] >= 0  # Should be non-negative for valid data
        assert abs(sum(result['weights'].values()) - 1.0) < 0.001

    def test_optimize_portfolio_min_variance(self, optimizer, sample_prices):
        """Test minimum variance optimization."""
        result = optimizer.optimize(
            prices=sample_prices,
            method='min_variance',
            risk_free_rate=0.02
        )
        
        assert 'weights' in result
        assert 'volatility' in result
        assert result['volatility'] >= 0  # Volatility should be non-negative

    def test_optimize_with_constraints(self, optimizer, sample_prices):
        """Test optimization with weight constraints."""
        constraints = {
            'min_weight': 0.1,
            'max_weight': 0.4,
            'target_return': 0.10
        }
        
        result = optimizer.optimize(
            prices=sample_prices,
            method='max_sharpe',
            constraints=constraints,
            risk_free_rate=0.02
        )
        
        # Check constraints are satisfied
        for weight in result['weights'].values():
            assert weight >= 0.09  # Allow small numerical error
            assert weight <= 0.41

    def test_optimize_with_sector_constraints(self, optimizer, sample_prices):
        """Test optimization with sector constraints."""
        sector_map = {
            'AAPL': 'Tech',
            'GOOGL': 'Tech',
            'MSFT': 'Tech',
            'AMZN': 'Consumer'
        }
        
        constraints = {
            'sector_limits': {
                'Tech': 0.7,
                'Consumer': 0.5
            }
        }
        
        result = optimizer.optimize(
            prices=sample_prices,
            method='max_sharpe',
            constraints=constraints,
            sector_map=sector_map,
            risk_free_rate=0.02
        )
        
        # Calculate sector weights
        tech_weight = sum(
            result['weights'][asset] 
            for asset, sector in sector_map.items() 
            if sector == 'Tech'
        )
        
        assert tech_weight <= 0.71  # Allow small numerical error

    def test_optimize_empty_prices(self, optimizer):
        """Test optimization with empty price data."""
        empty_prices = pd.DataFrame()
        
        with pytest.raises(ValueError, match="price data"):
            optimizer.optimize(
                prices=empty_prices,
                method='equal_weight'
            )

    def test_optimize_single_asset(self, optimizer):
        """Test optimization with single asset."""
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        single_asset = pd.DataFrame(
            {'AAPL': 100 * (1 + np.random.randn(100).cumsum() * 0.01)},
            index=dates
        )
        
        result = optimizer.optimize(
            prices=single_asset,
            method='equal_weight'
        )
        
        assert result['weights']['AAPL'] == 1.0

    def test_optimize_with_transaction_costs(self, optimizer, sample_prices):
        """Test optimization with transaction costs."""
        result = optimizer.optimize(
            prices=sample_prices,
            method='max_sharpe',
            transaction_cost=0.001,  # 0.1% transaction cost
            risk_free_rate=0.02
        )
        
        assert 'weights' in result
        assert 'net_return' in result
        assert result['net_return'] <= result['expected_return']

    def test_optimize_with_rebalancing_frequency(self, optimizer, sample_prices):
        """Test optimization with different rebalancing frequencies."""
        for frequency in ['daily', 'weekly', 'monthly', 'quarterly']:
            result = optimizer.optimize(
                prices=sample_prices,
                method='equal_weight',
                rebalance_frequency=frequency
            )
            
            assert 'weights' in result
            assert 'turnover' in result
            assert result['turnover'] >= 0

    def test_risk_parity_optimization(self, optimizer, sample_prices):
        """Test risk parity optimization."""
        result = optimizer.optimize(
            prices=sample_prices,
            method='risk_parity'
        )
        
        assert 'weights' in result
        assert 'risk_contributions' in result
        
        # Check that risk contributions are roughly equal
        contributions = list(result['risk_contributions'].values())
        avg_contribution = np.mean(contributions)
        for contrib in contributions:
            assert abs(contrib - avg_contribution) / avg_contribution < 0.3

    def test_optimize_with_invalid_method(self, optimizer, sample_prices):
        """Test optimization with invalid method."""
        with pytest.raises(ValueError, match="method"):
            optimizer.optimize(
                prices=sample_prices,
                method='invalid_method'
            )

    def test_calculate_portfolio_metrics(self, optimizer, sample_prices):
        """Test portfolio metrics calculation."""
        weights = {'AAPL': 0.25, 'GOOGL': 0.25, 'MSFT': 0.25, 'AMZN': 0.25}
        
        metrics = optimizer.calculate_metrics(
            prices=sample_prices,
            weights=weights,
            risk_free_rate=0.02
        )
        
        assert 'expected_return' in metrics
        assert 'volatility' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'calmar_ratio' in metrics

    def test_efficient_frontier_calculation(self, optimizer, sample_prices):
        """Test efficient frontier calculation."""
        frontier = optimizer.calculate_efficient_frontier(
            prices=sample_prices,
            num_portfolios=10
        )
        
        assert len(frontier) == 10
        assert all('return' in p and 'risk' in p for p in frontier)
        
        # Check that frontier is properly ordered
        returns = [p['return'] for p in frontier]
        assert returns == sorted(returns)

    def test_black_litterman_optimization(self, optimizer, sample_prices):
        """Test Black-Litterman optimization."""
        views = {
            'AAPL': 0.15,  # Expected 15% return
            'GOOGL': 0.12  # Expected 12% return
        }
        
        result = optimizer.optimize(
            prices=sample_prices,
            method='black_litterman',
            views=views,
            confidence=0.8
        )
        
        assert 'weights' in result
        assert 'posterior_returns' in result

    def test_optimize_with_esg_constraints(self, optimizer, sample_prices):
        """Test optimization with ESG constraints."""
        esg_scores = {
            'AAPL': 0.8,
            'GOOGL': 0.7,
            'MSFT': 0.9,
            'AMZN': 0.6
        }
        
        result = optimizer.optimize(
            prices=sample_prices,
            method='max_sharpe',
            esg_scores=esg_scores,
            min_esg_score=0.7
        )
        
        # Check that low ESG assets have reduced weights
        assert result['weights']['AMZN'] < 0.25  # Should be underweighted

    def test_monte_carlo_optimization(self, optimizer, sample_prices):
        """Test Monte Carlo optimization."""
        result = optimizer.optimize(
            prices=sample_prices,
            method='monte_carlo',
            num_simulations=1000
        )
        
        assert 'weights' in result
        assert 'confidence_intervals' in result
        assert 'value_at_risk' in result

    def test_optimize_with_correlation_clustering(self, optimizer, sample_prices):
        """Test optimization with correlation clustering."""
        result = optimizer.optimize(
            prices=sample_prices,
            method='hierarchical_risk_parity'
        )
        
        assert 'weights' in result
        assert 'clusters' in result
        assert abs(sum(result['weights'].values()) - 1.0) < 0.001

    def test_backtest_optimization_strategy(self, optimizer, sample_prices):
        """Test backtesting of optimization strategy."""
        backtest = optimizer.backtest(
            prices=sample_prices,
            method='max_sharpe',
            lookback_period=30,
            rebalance_frequency='monthly'
        )
        
        assert 'returns' in backtest
        assert 'cumulative_returns' in backtest
        assert 'sharpe_ratio' in backtest
        assert 'max_drawdown' in backtest
        assert len(backtest['returns']) > 0