"""Tests for performance service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.performance import (
    calculate_portfolio_metrics,
    get_rolling_metrics,
    PerformanceCalculator,
    TRADING_DAYS_PER_YEAR,
    RISK_FREE_RATE
)


class TestPerformanceService:
    """Test suite for performance service."""

    @patch('app.services.performance.PerformanceTracker')
    def test_calculate_portfolio_metrics_success(self, mock_tracker_class):
        """Test successful portfolio metrics calculation."""
        # Setup mock
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        mock_metrics = {
            'total_return': 0.15,
            'annualized_return': 0.12,
            'volatility': 0.18,
            'sharpe_ratio': 0.67,
            'max_drawdown': -0.08
        }
        mock_tracker.calculate_comprehensive_metrics.return_value = mock_metrics
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Execute
        result = calculate_portfolio_metrics(mock_db, lookback_days=30)
        
        # Verify
        assert result == mock_metrics
        mock_tracker_class.assert_called_once_with(mock_db)
        mock_tracker.calculate_comprehensive_metrics.assert_called_once_with(30)
        mock_tracker.save_metrics_to_database.assert_called_once_with(mock_metrics)

    @patch('app.services.performance.PerformanceTracker')
    def test_calculate_portfolio_metrics_no_lookback(self, mock_tracker_class):
        """Test portfolio metrics calculation without lookback days."""
        # Setup mock
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        mock_metrics = {
            'total_return': 0.25,
            'annualized_return': 0.20
        }
        mock_tracker.calculate_comprehensive_metrics.return_value = mock_metrics
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Execute
        result = calculate_portfolio_metrics(mock_db, lookback_days=None)
        
        # Verify
        assert result == mock_metrics
        mock_tracker.calculate_comprehensive_metrics.assert_called_once_with(None)
        mock_tracker.save_metrics_to_database.assert_called_once_with(mock_metrics)

    @patch('app.services.performance.PerformanceTracker')
    def test_calculate_portfolio_metrics_no_data(self, mock_tracker_class):
        """Test portfolio metrics calculation with no data."""
        # Setup mock
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.calculate_comprehensive_metrics.return_value = None
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Execute
        result = calculate_portfolio_metrics(mock_db, lookback_days=30)
        
        # Verify
        assert result is None
        mock_tracker.save_metrics_to_database.assert_not_called()

    @patch('app.services.performance.PerformanceTracker')
    def test_get_rolling_metrics_default_window(self, mock_tracker_class):
        """Test rolling metrics with default window."""
        # Setup mock
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        mock_rolling_data = [
            {'date': '2024-01-01', 'return': 0.01},
            {'date': '2024-01-02', 'return': 0.02}
        ]
        mock_tracker.get_rolling_metrics.return_value = mock_rolling_data
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Execute
        result = get_rolling_metrics(mock_db)
        
        # Verify
        assert result == mock_rolling_data
        mock_tracker_class.assert_called_once_with(mock_db)
        mock_tracker.get_rolling_metrics.assert_called_once_with(30)

    @patch('app.services.performance.PerformanceTracker')
    def test_get_rolling_metrics_custom_window(self, mock_tracker_class):
        """Test rolling metrics with custom window."""
        # Setup mock
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        mock_rolling_data = [
            {'date': '2024-01-01', 'return': 0.03},
            {'date': '2024-01-02', 'return': 0.04}
        ]
        mock_tracker.get_rolling_metrics.return_value = mock_rolling_data
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Execute
        result = get_rolling_metrics(mock_db, window=60)
        
        # Verify
        assert result == mock_rolling_data
        mock_tracker.get_rolling_metrics.assert_called_once_with(60)

    @patch('app.services.performance.PerformanceTracker')
    def test_get_rolling_metrics_empty_result(self, mock_tracker_class):
        """Test rolling metrics with empty result."""
        # Setup mock
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.get_rolling_metrics.return_value = []
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Execute
        result = get_rolling_metrics(mock_db, window=7)
        
        # Verify
        assert result == []
        mock_tracker.get_rolling_metrics.assert_called_once_with(7)

    def test_constants_exported(self):
        """Test that constants are properly exported."""
        assert TRADING_DAYS_PER_YEAR == 252
        assert RISK_FREE_RATE == 0.05

    def test_performance_calculator_exported(self):
        """Test that PerformanceCalculator is exported."""
        assert PerformanceCalculator is not None