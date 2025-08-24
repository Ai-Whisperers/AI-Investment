"""Tests for strategy service."""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.services.strategy import StrategyService


class TestStrategyService:
    """Test suite for strategy service."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def strategy_service(self, mock_db_session):
        """Create a StrategyService instance with mocked dependencies."""
        with patch('app.services.strategy.DataValidator'), \
             patch('app.services.strategy.WeightCalculator'), \
             patch('app.services.strategy.RiskCalculator'), \
             patch('app.services.strategy.PortfolioOptimizer'):
            return StrategyService(mock_db_session)

    def test_init_service(self, mock_db_session):
        """Test service initialization."""
        service = StrategyService(mock_db_session)
        
        assert service.db == mock_db_session
        assert service.validator is not None
        assert service.weight_calc is not None
        assert service.risk_calc is not None
        assert service.optimizer is not None

    @patch('app.services.strategy.StrategyService._load_price_data')
    def test_compute_index_empty_data(self, mock_load_data, strategy_service):
        """Test index computation with empty price data."""
        # Setup mock
        mock_load_data.return_value = pd.DataFrame()
        
        # Execute - should return None due to empty data
        result = strategy_service.compute_index_and_allocations()
        
        # Verify
        assert result is None
        mock_load_data.assert_called_once()

    @patch('app.services.strategy.StrategyService._get_default_config')
    @patch('app.services.strategy.StrategyService._load_price_data')
    def test_compute_index_with_default_config(self, mock_load_data, mock_get_config, strategy_service):
        """Test index computation with default configuration."""
        # Setup mocks
        mock_get_config.return_value = {
            'strategy': 'equal_weight',
            'min_weight': 0.01,
            'max_weight': 0.5
        }
        
        # Create sample price data
        dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
        mock_price_df = pd.DataFrame({
            'AAPL': [100, 101, 102, 103, 104],
            'GOOGL': [200, 202, 204, 206, 208],
            'MSFT': [150, 151, 152, 153, 154]
        }, index=dates)
        mock_load_data.return_value = mock_price_df
        
        # Mock validator
        strategy_service.validator.validate_price_data.return_value = True
        
        # Execute
        with patch.object(strategy_service, '_save_allocations'):
            with patch.object(strategy_service, '_save_index_values'):
                strategy_service.compute_index_and_allocations()
        
        # Verify
        mock_get_config.assert_called_once()
        mock_load_data.assert_called_once()
        strategy_service.validator.validate_price_data.assert_called()

    def test_get_default_config(self, strategy_service):
        """Test getting default configuration."""
        config = strategy_service._get_default_config()
        
        assert 'strategy' in config
        assert 'lookback_days' in config
        assert 'min_weight' in config
        assert 'max_weight' in config
        assert config['min_weight'] >= 0
        assert config['max_weight'] <= 1

    @patch('app.services.strategy.Asset')
    @patch('app.services.strategy.Price')
    def test_load_price_data(self, mock_price_model, mock_asset_model, strategy_service):
        """Test loading price data from database."""
        # Setup mocks
        mock_assets = [
            Mock(symbol='AAPL', id=1),
            Mock(symbol='GOOGL', id=2),
            Mock(symbol='MSFT', id=3)
        ]
        strategy_service.db.query(mock_asset_model).filter.return_value.all.return_value = mock_assets
        
        mock_prices = [
            Mock(asset_id=1, date=datetime(2024, 1, 1), close=100.0),
            Mock(asset_id=1, date=datetime(2024, 1, 2), close=101.0),
            Mock(asset_id=2, date=datetime(2024, 1, 1), close=200.0),
            Mock(asset_id=2, date=datetime(2024, 1, 2), close=202.0),
            Mock(asset_id=3, date=datetime(2024, 1, 1), close=150.0),
            Mock(asset_id=3, date=datetime(2024, 1, 2), close=151.0),
        ]
        strategy_service.db.query(mock_price_model).filter.return_value.all.return_value = mock_prices
        
        # Execute
        result = strategy_service._load_price_data()
        
        # Verify
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert list(result.columns) == ['AAPL', 'GOOGL', 'MSFT']

    def test_calculate_dynamic_weights(self, strategy_service):
        """Test dynamic weight calculation."""
        # Create sample returns data
        returns_df = pd.DataFrame({
            'AAPL': [0.01, 0.02, -0.01, 0.03, 0.01],
            'GOOGL': [0.02, 0.01, 0.02, 0.01, 0.02],
            'MSFT': [-0.01, 0.01, 0.01, 0.02, 0.01]
        })
        
        config = {
            'strategy': 'risk_parity',
            'min_weight': 0.1,
            'max_weight': 0.5
        }
        
        # Mock weight calculator
        strategy_service.weight_calc.calculate_weights.return_value = {
            'AAPL': 0.33,
            'GOOGL': 0.34,
            'MSFT': 0.33
        }
        
        # Execute
        weights = strategy_service._calculate_dynamic_weights(returns_df, config)
        
        # Verify
        assert isinstance(weights, dict)
        assert len(weights) == 3
        assert abs(sum(weights.values()) - 1.0) < 0.01  # Weights sum to 1

    @patch('app.services.strategy.Allocation')
    def test_save_allocations(self, mock_allocation_model, strategy_service):
        """Test saving allocations to database."""
        # Test data
        weights = {
            'AAPL': 0.4,
            'GOOGL': 0.3,
            'MSFT': 0.3
        }
        date = datetime(2024, 1, 15)
        
        # Mock asset query
        mock_assets = {
            'AAPL': Mock(id=1),
            'GOOGL': Mock(id=2),
            'MSFT': Mock(id=3)
        }
        
        def get_asset(symbol):
            return mock_assets.get(symbol)
        
        strategy_service.db.query().filter().first.side_effect = lambda: get_asset(
            strategy_service.db.query.call_args[0][0].symbol
        )
        
        # Execute
        strategy_service._save_allocations(weights, date)
        
        # Verify
        assert strategy_service.db.add.call_count == 3
        assert strategy_service.db.commit.called

    @patch('app.services.strategy.IndexValue')
    def test_save_index_values(self, mock_index_value_model, strategy_service):
        """Test saving index values to database."""
        # Test data
        dates = pd.date_range(start='2024-01-01', periods=3, freq='D')
        index_values = pd.Series([100, 101, 102], index=dates)
        
        # Execute
        strategy_service._save_index_values(index_values)
        
        # Verify
        assert strategy_service.db.add.call_count == 3
        assert strategy_service.db.commit.called

    def test_apply_risk_management(self, strategy_service):
        """Test risk management application."""
        # Test data
        weights = {
            'AAPL': 0.6,  # Over concentrated
            'GOOGL': 0.3,
            'MSFT': 0.1
        }
        
        returns_df = pd.DataFrame({
            'AAPL': [0.01, 0.02, -0.01],
            'GOOGL': [0.02, 0.01, 0.02],
            'MSFT': [-0.01, 0.01, 0.01]
        })
        
        config = {
            'max_weight': 0.5,
            'max_volatility': 0.2
        }
        
        # Mock risk calculator
        strategy_service.risk_calc.apply_constraints.return_value = {
            'AAPL': 0.5,  # Reduced to max
            'GOOGL': 0.35,
            'MSFT': 0.15
        }
        
        # Execute
        adjusted_weights = strategy_service._apply_risk_management(weights, returns_df, config)
        
        # Verify
        assert adjusted_weights['AAPL'] <= config['max_weight']
        assert abs(sum(adjusted_weights.values()) - 1.0) < 0.01

    def test_optimize_with_constraints(self, strategy_service):
        """Test portfolio optimization with constraints."""
        # Test data
        returns_df = pd.DataFrame({
            'AAPL': [0.01, 0.02, -0.01, 0.03],
            'GOOGL': [0.02, 0.01, 0.02, 0.01],
            'MSFT': [-0.01, 0.01, 0.01, 0.02]
        })
        
        config = {
            'optimization_method': 'maximize_sharpe',
            'min_weight': 0.1,
            'max_weight': 0.5
        }
        
        # Mock optimizer
        strategy_service.optimizer.optimize.return_value = {
            'AAPL': 0.4,
            'GOOGL': 0.35,
            'MSFT': 0.25
        }
        
        # Execute
        optimized_weights = strategy_service._optimize_with_constraints(returns_df, config)
        
        # Verify
        assert isinstance(optimized_weights, dict)
        assert all(w >= config['min_weight'] for w in optimized_weights.values())
        assert all(w <= config['max_weight'] for w in optimized_weights.values())