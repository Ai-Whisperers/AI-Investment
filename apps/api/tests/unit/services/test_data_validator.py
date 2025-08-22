"""Unit tests for data validator module."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.strategy_modules.data_validator import DataValidator


@pytest.mark.unit
class TestDataValidator:
    """Test suite for data validator."""

    @pytest.fixture
    def validator(self):
        """Create data validator instance."""
        return DataValidator()

    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing."""
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        return pd.DataFrame({
            'AAPL': 100 + np.random.randn(100).cumsum(),
            'GOOGL': 200 + np.random.randn(100).cumsum(),
            'MSFT': 150 + np.random.randn(100).cumsum()
        }, index=dates)

    @pytest.fixture
    def sample_volume_data(self):
        """Create sample volume data for testing."""
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        return pd.DataFrame({
            'AAPL': np.random.randint(1000000, 10000000, 100),
            'GOOGL': np.random.randint(500000, 5000000, 100),
            'MSFT': np.random.randint(2000000, 8000000, 100)
        }, index=dates)

    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator is not None
        assert hasattr(validator, 'validate_prices')
        assert hasattr(validator, 'validate_returns')

    def test_validate_prices_valid_data(self, validator, sample_price_data):
        """Test price validation with valid data."""
        result = validator.validate_prices(sample_price_data)
        
        assert result['is_valid'] is True
        assert 'errors' in result
        assert len(result['errors']) == 0
        assert 'warnings' in result

    def test_validate_prices_with_nulls(self, validator, sample_price_data):
        """Test price validation with null values."""
        # Introduce null values
        data_with_nulls = sample_price_data.copy()
        data_with_nulls.iloc[10:15, 0] = np.nan
        
        result = validator.validate_prices(data_with_nulls)
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert any('null' in error.lower() for error in result['errors'])

    def test_validate_prices_with_negative_values(self, validator):
        """Test price validation with negative values."""
        dates = pd.date_range(end=datetime.now(), periods=10, freq='D')
        invalid_data = pd.DataFrame({
            'AAPL': [100, 101, 99, -5, 98, 97, 96, 95, 94, 93]
        }, index=dates)
        
        result = validator.validate_prices(invalid_data)
        
        assert result['is_valid'] is False
        assert any('negative' in error.lower() for error in result['errors'])

    def test_validate_prices_with_outliers(self, validator, sample_price_data):
        """Test price validation with outliers."""
        # Introduce outlier
        data_with_outlier = sample_price_data.copy()
        data_with_outlier.iloc[50, 0] = data_with_outlier.iloc[49, 0] * 100
        
        result = validator.validate_prices(
            data_with_outlier, 
            check_outliers=True,
            outlier_threshold=3
        )
        
        assert 'warnings' in result
        assert any('outlier' in warning.lower() for warning in result['warnings'])

    def test_validate_returns_valid_data(self, validator, sample_price_data):
        """Test return validation with valid data."""
        returns = sample_price_data.pct_change().dropna()
        result = validator.validate_returns(returns)
        
        assert result['is_valid'] is True
        assert 'statistics' in result
        assert 'mean' in result['statistics']
        assert 'std' in result['statistics']
        assert 'skew' in result['statistics']
        assert 'kurtosis' in result['statistics']

    def test_validate_returns_extreme_values(self, validator):
        """Test return validation with extreme values."""
        dates = pd.date_range(end=datetime.now(), periods=10, freq='D')
        extreme_returns = pd.DataFrame({
            'AAPL': [0.01, 0.02, -0.01, 10.0, 0.01, -0.02, 0.01, 0.02, -0.01, 0.01]
        }, index=dates)
        
        result = validator.validate_returns(extreme_returns)
        
        assert result['is_valid'] is False
        assert any('extreme' in error.lower() for error in result['errors'])

    def test_validate_volume_data(self, validator, sample_volume_data):
        """Test volume data validation."""
        result = validator.validate_volume(sample_volume_data)
        
        assert result['is_valid'] is True
        assert 'average_volume' in result
        assert all(vol > 0 for vol in result['average_volume'].values())

    def test_validate_volume_with_zero_values(self, validator, sample_volume_data):
        """Test volume validation with zero values."""
        data_with_zeros = sample_volume_data.copy()
        data_with_zeros.iloc[20:25, 1] = 0
        
        result = validator.validate_volume(data_with_zeros)
        
        assert 'warnings' in result
        assert any('zero volume' in warning.lower() for warning in result['warnings'])

    def test_validate_market_cap_data(self, validator):
        """Test market cap validation."""
        market_caps = {
            'AAPL': 3e12,   # 3 trillion
            'GOOGL': 2e12,  # 2 trillion
            'MSFT': 2.5e12, # 2.5 trillion
            'PENNY': 1e6    # 1 million (penny stock)
        }
        
        result = validator.validate_market_caps(market_caps)
        
        assert result['is_valid'] is True
        assert 'classifications' in result
        assert result['classifications']['AAPL'] == 'mega_cap'
        assert result['classifications']['PENNY'] == 'micro_cap'

    def test_validate_correlation_matrix(self, validator, sample_price_data):
        """Test correlation matrix validation."""
        returns = sample_price_data.pct_change().dropna()
        corr_matrix = returns.corr()
        
        result = validator.validate_correlation(corr_matrix)
        
        assert result['is_valid'] is True
        assert 'is_positive_definite' in result
        assert 'condition_number' in result
        assert result['is_positive_definite'] is True

    def test_validate_correlation_invalid_matrix(self, validator):
        """Test correlation validation with invalid matrix."""
        # Create invalid correlation matrix (not symmetric)
        invalid_corr = pd.DataFrame([
            [1.0, 0.5, 0.3],
            [0.6, 1.0, 0.4],  # Not symmetric
            [0.3, 0.4, 1.0]
        ])
        
        result = validator.validate_correlation(invalid_corr)
        
        assert result['is_valid'] is False
        assert any('symmetric' in error.lower() for error in result['errors'])

    def test_validate_date_range(self, validator, sample_price_data):
        """Test date range validation."""
        result = validator.validate_date_range(
            sample_price_data.index,
            min_days=30,
            max_gap_days=5
        )
        
        assert result['is_valid'] is True
        assert 'total_days' in result
        assert 'trading_days' in result
        assert 'gaps' in result

    def test_validate_date_range_with_gaps(self, validator):
        """Test date range validation with gaps."""
        dates = pd.date_range(start='2024-01-01', end='2024-01-15', freq='D')
        # Remove some dates to create gaps
        dates = dates.delete([5, 6, 7, 8, 9])  # 5-day gap
        
        result = validator.validate_date_range(
            dates,
            min_days=10,
            max_gap_days=3
        )
        
        assert result['is_valid'] is False
        assert len(result['gaps']) > 0
        assert any(gap['days'] > 3 for gap in result['gaps'])

    def test_validate_asset_universe(self, validator):
        """Test asset universe validation."""
        assets = ['AAPL', 'GOOGL', 'MSFT', 'BTC-USD', 'INVALID']
        
        result = validator.validate_asset_universe(
            assets,
            allowed_types=['stock', 'etf', 'crypto']
        )
        
        assert 'valid_assets' in result
        assert 'invalid_assets' in result
        assert 'INVALID' in result['invalid_assets']

    def test_validate_portfolio_weights(self, validator):
        """Test portfolio weights validation."""
        weights = {
            'AAPL': 0.3,
            'GOOGL': 0.3,
            'MSFT': 0.4
        }
        
        result = validator.validate_weights(weights)
        
        assert result['is_valid'] is True
        assert abs(result['sum'] - 1.0) < 0.001
        assert all(result['individual_checks'][asset]['is_valid'] 
                  for asset in weights)

    def test_validate_weights_invalid_sum(self, validator):
        """Test weight validation with invalid sum."""
        weights = {
            'AAPL': 0.3,
            'GOOGL': 0.3,
            'MSFT': 0.3  # Sum = 0.9
        }
        
        result = validator.validate_weights(weights, tolerance=0.01)
        
        assert result['is_valid'] is False
        assert abs(result['sum'] - 1.0) > 0.01

    def test_validate_weights_negative_values(self, validator):
        """Test weight validation with negative values."""
        weights = {
            'AAPL': 0.5,
            'GOOGL': 0.7,
            'MSFT': -0.2  # Short position
        }
        
        result = validator.validate_weights(weights, allow_short=False)
        
        assert result['is_valid'] is False
        assert not result['individual_checks']['MSFT']['is_valid']

    def test_validate_strategy_parameters(self, validator):
        """Test strategy parameter validation."""
        params = {
            'lookback_period': 30,
            'rebalance_frequency': 'monthly',
            'risk_target': 0.15,
            'max_leverage': 1.5
        }
        
        result = validator.validate_strategy_params(params)
        
        assert result['is_valid'] is True
        assert all(check['is_valid'] 
                  for check in result['parameter_checks'].values())

    def test_validate_strategy_invalid_params(self, validator):
        """Test strategy validation with invalid parameters."""
        params = {
            'lookback_period': -10,  # Invalid negative period
            'rebalance_frequency': 'invalid',
            'risk_target': 2.0,  # Unrealistic risk target
            'max_leverage': 10  # Excessive leverage
        }
        
        result = validator.validate_strategy_params(params)
        
        assert result['is_valid'] is False
        assert not result['parameter_checks']['lookback_period']['is_valid']
        assert not result['parameter_checks']['rebalance_frequency']['is_valid']

    def test_validate_benchmark_alignment(self, validator, sample_price_data):
        """Test benchmark alignment validation."""
        benchmark = sample_price_data.mean(axis=1)  # Simple benchmark
        
        result = validator.validate_benchmark_alignment(
            sample_price_data,
            benchmark
        )
        
        assert result['is_valid'] is True
        assert 'date_alignment' in result
        assert 'correlation_stats' in result

    def test_detect_data_quality_issues(self, validator, sample_price_data):
        """Test comprehensive data quality detection."""
        # Introduce various issues
        problematic_data = sample_price_data.copy()
        problematic_data.iloc[10, 0] = np.nan  # Null value
        problematic_data.iloc[20, 1] = problematic_data.iloc[19, 1] * 10  # Spike
        problematic_data.iloc[30:35, 2] = problematic_data.iloc[30, 2]  # Stale data
        
        result = validator.detect_quality_issues(problematic_data)
        
        assert 'null_values' in result
        assert 'outliers' in result
        assert 'stale_data' in result
        assert result['overall_quality_score'] < 1.0

    def test_validate_liquidity_metrics(self, validator, sample_price_data, sample_volume_data):
        """Test liquidity metrics validation."""
        result = validator.validate_liquidity(
            prices=sample_price_data,
            volumes=sample_volume_data,
            min_daily_volume=100000,
            min_dollar_volume=1000000
        )
        
        assert 'is_liquid' in result
        assert 'liquidity_scores' in result
        assert all(asset in result['liquidity_scores'] 
                  for asset in sample_price_data.columns)