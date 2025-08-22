"""Unit tests for strategy endpoints."""

import pytest
from unittest.mock import Mock, patch
from fastapi import status

from app.models import User, Portfolio


@pytest.mark.unit
class TestStrategyEndpoints:
    """Test suite for strategy API endpoints."""

    def test_get_available_strategies(self, client, auth_headers):
        """Test getting list of available strategies."""
        response = client.get(
            "/api/v1/strategy/available",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all('id' in s and 'name' in s for s in data)

    def test_get_strategy_details(self, client, auth_headers):
        """Test getting strategy details."""
        response = client.get(
            "/api/v1/strategy/momentum",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'id' in data
        assert 'name' in data
        assert 'description' in data
        assert 'parameters' in data

    def test_get_strategy_not_found(self, client, auth_headers):
        """Test getting non-existent strategy."""
        response = client.get(
            "/api/v1/strategy/nonexistent",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_validate_strategy_config(self, client, auth_headers):
        """Test strategy configuration validation."""
        config = {
            "strategy_type": "momentum",
            "parameters": {
                "lookback_period": 30,
                "rebalance_frequency": "monthly"
            }
        }
        
        response = client.post(
            "/api/v1/strategy/validate",
            json=config,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_valid'] is True

    def test_validate_invalid_strategy_config(self, client, auth_headers):
        """Test invalid strategy configuration."""
        config = {
            "strategy_type": "momentum",
            "parameters": {
                "lookback_period": -10,  # Invalid negative period
                "rebalance_frequency": "invalid"
            }
        }
        
        response = client.post(
            "/api/v1/strategy/validate",
            json=config,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_apply_strategy_to_portfolio(self, client, auth_headers, test_user, test_db_session):
        """Test applying strategy to portfolio."""
        # Create a portfolio
        portfolio = Portfolio(
            name="Test Portfolio",
            user_id=test_user.id,
            initial_cash=10000
        )
        test_db_session.add(portfolio)
        test_db_session.commit()
        
        strategy_config = {
            "strategy_type": "equal_weight",
            "parameters": {}
        }
        
        response = client.post(
            f"/api/v1/strategy/apply/{portfolio.id}",
            json=strategy_config,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'portfolio_id' in data
        assert 'strategy_applied' in data

    def test_apply_strategy_unauthorized(self, client):
        """Test applying strategy without auth."""
        response = client.post(
            "/api/v1/strategy/apply/1",
            json={"strategy_type": "momentum"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_strategy_performance(self, client, auth_headers):
        """Test getting strategy performance metrics."""
        response = client.get(
            "/api/v1/strategy/performance/momentum",
            headers=auth_headers,
            params={"period": "1Y"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'returns' in data
        assert 'sharpe_ratio' in data
        assert 'max_drawdown' in data

    def test_compare_strategies(self, client, auth_headers):
        """Test comparing multiple strategies."""
        response = client.post(
            "/api/v1/strategy/compare",
            json={
                "strategies": ["momentum", "mean_reversion", "equal_weight"],
                "period": "1Y"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'comparison' in data
        assert len(data['comparison']) == 3

    def test_backtest_strategy(self, client, auth_headers):
        """Test strategy backtesting."""
        backtest_config = {
            "strategy_type": "momentum",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "initial_capital": 100000,
            "parameters": {
                "lookback_period": 30
            }
        }
        
        response = client.post(
            "/api/v1/strategy/backtest",
            json=backtest_config,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'total_return' in data
        assert 'sharpe_ratio' in data
        assert 'max_drawdown' in data
        assert 'trades' in data

    def test_optimize_strategy_parameters(self, client, auth_headers):
        """Test strategy parameter optimization."""
        optimization_config = {
            "strategy_type": "momentum",
            "objective": "sharpe_ratio",
            "parameter_ranges": {
                "lookback_period": [20, 60],
                "threshold": [0.01, 0.05]
            }
        }
        
        response = client.post(
            "/api/v1/strategy/optimize",
            json=optimization_config,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'optimal_parameters' in data
        assert 'performance_metrics' in data

    def test_get_strategy_signals(self, client, auth_headers):
        """Test getting current strategy signals."""
        response = client.get(
            "/api/v1/strategy/signals/momentum",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'signals' in data
        assert 'timestamp' in data
        assert isinstance(data['signals'], list)

    def test_create_custom_strategy(self, client, auth_headers):
        """Test creating custom strategy."""
        custom_strategy = {
            "name": "My Custom Strategy",
            "description": "A custom momentum strategy",
            "base_strategy": "momentum",
            "parameters": {
                "lookback_period": 45,
                "rebalance_frequency": "weekly"
            }
        }
        
        response = client.post(
            "/api/v1/strategy/custom",
            json=custom_strategy,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert 'id' in data
        assert data['name'] == custom_strategy['name']

    def test_delete_custom_strategy(self, client, auth_headers):
        """Test deleting custom strategy."""
        # First create a custom strategy
        create_response = client.post(
            "/api/v1/strategy/custom",
            json={
                "name": "To Delete",
                "base_strategy": "momentum"
            },
            headers=auth_headers
        )
        strategy_id = create_response.json()['id']
        
        # Then delete it
        response = client.delete(
            f"/api/v1/strategy/custom/{strategy_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_strategy_risk_metrics(self, client, auth_headers):
        """Test getting strategy risk metrics."""
        response = client.get(
            "/api/v1/strategy/risk/momentum",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'var' in data  # Value at Risk
        assert 'cvar' in data  # Conditional VaR
        assert 'beta' in data
        assert 'correlation' in data