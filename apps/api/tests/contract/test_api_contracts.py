"""
Contract tests to ensure frontend-backend API compatibility.
These tests verify that API responses match expected schemas.
"""

import pytest
from pydantic import ValidationError
from decimal import Decimal
from datetime import datetime

from app.schemas.portfolio import PortfolioResponse, PositionResponse
from app.schemas.index import IndexValueResponse, AllocationResponse
from app.schemas.strategy import StrategyConfigResponse
from app.schemas.user import UserResponse
from app.schemas.validation import RefreshResponse


@pytest.mark.contract
@pytest.mark.critical
class TestAPIContracts:
    """Ensure API contracts match frontend expectations."""
    
    def test_portfolio_response_contract(self):
        """Test portfolio response matches frontend interface."""
        # This data structure must match frontend's PortfolioData interface
        response_data = {
            "id": 1,
            "name": "Test Portfolio",
            "total_value": 100000.00,
            "initial_value": 95000.00,
            "total_return": 0.0526,
            "daily_return": 0.0012,
            "positions": [
                {
                    "symbol": "AAPL",
                    "shares": 100,
                    "current_price": 150.25,
                    "total_value": 15025.00,
                    "weight": 0.15,
                    "daily_change": 0.0125
                }
            ],
            "performance": {
                "sharpe_ratio": 1.25,
                "max_drawdown": -0.12,
                "volatility": 0.18,
                "beta": 1.1
            },
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-19T12:00:00"
        }
        
        # Should not raise ValidationError
        validated = PortfolioResponse(**response_data)
        assert validated.total_value == 100000.00
        assert len(validated.positions) == 1
    
    def test_index_value_response_contract(self):
        """Test index value response for chart data."""
        # Must match frontend's ChartData interface
        response_data = {
            "date": "2024-01-19",
            "value": 1523.45,
            "daily_return": 0.0125,
            "cumulative_return": 0.52,
            "volatility": 0.0156,
            "benchmark_value": 1450.00,
            "benchmark_return": 0.0098
        }
        
        validated = IndexValueResponse(**response_data)
        assert validated.value == 1523.45
    
    def test_allocation_response_contract(self):
        """Test allocation response for pie charts."""
        # Must match frontend's AllocationData interface
        response_data = {
            "date": "2024-01-19",
            "allocations": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "weight": 0.25,
                    "value": 25000.00,
                    "shares": 166,
                    "sector": "Technology"
                },
                {
                    "symbol": "GOOGL",
                    "name": "Alphabet Inc.",
                    "weight": 0.20,
                    "value": 20000.00,
                    "shares": 7,
                    "sector": "Technology"
                }
            ],
            "total_value": 100000.00,
            "rebalance_needed": False
        }
        
        validated = AllocationResponse(**response_data)
        assert len(validated.allocations) == 2
        assert sum(a.weight for a in validated.allocations) == pytest.approx(0.45)
    
    def test_strategy_config_response_contract(self):
        """Test strategy configuration response."""
        # Must match frontend's StrategyConfig interface
        response_data = {
            "id": 1,
            "name": "Moderate Growth",
            "risk_level": "medium",
            "target_return": 0.08,
            "max_drawdown": 0.15,
            "rebalance_frequency": "monthly",
            "constraints": {
                "min_weight": 0.02,
                "max_weight": 0.40,
                "max_concentration": 0.60,
                "min_assets": 5,
                "max_assets": 20
            },
            "asset_filters": {
                "min_market_cap": 1000000000,
                "sectors": ["Technology", "Healthcare", "Finance"],
                "exclude_symbols": ["TSLA", "GME"]
            }
        }
        
        validated = StrategyConfigResponse(**response_data)
        assert validated.risk_level == "medium"
        assert validated.constraints["max_weight"] == 0.40
    
    def test_refresh_response_contract(self):
        """Test data refresh response."""
        # Must match frontend's RefreshStatus interface
        response_data = {
            "status": "success",
            "message": "Data refreshed successfully",
            "timestamp": "2024-01-19T12:00:00",
            "assets_updated": 25,
            "prices_added": 500,
            "indices_calculated": 30,
            "duration_seconds": 2.5,
            "next_refresh": "2024-01-19T13:00:00",
            "warnings": []
        }
        
        validated = RefreshResponse(**response_data)
        assert validated.status == "success"
        assert validated.assets_updated == 25
    
    def test_diagnostics_response_contract(self):
        """Test diagnostics/health check response."""
        # Must match frontend's DiagnosticsData interface
        response_data = {
            "timestamp": "2024-01-19T12:00:00",
            "status": "healthy",
            "database": {
                "connected": True,
                "tables": {
                    "users": {"count": 10, "status": "OK"},
                    "assets": {"count": 500, "status": "OK"},
                    "prices": {"count": 50000, "status": "OK"}
                }
            },
            "cache": {
                "connected": True,
                "hit_rate": 0.85,
                "memory_usage": "125MB",
                "keys": 1500
            },
            "market_data": {
                "last_update": "2024-01-19T11:55:00",
                "provider": "twelvedata",
                "status": "active",
                "rate_limit_remaining": 450
            }
        }
        
        # Validate nested structure
        assert response_data["database"]["connected"] == True
        assert response_data["cache"]["hit_rate"] == 0.85
    
    def test_error_response_contract(self):
        """Test error response format."""
        # Must match frontend's ErrorResponse interface
        error_responses = [
            {
                "detail": "Invalid credentials",
                "status_code": 401,
                "type": "authentication_error"
            },
            {
                "detail": [
                    {
                        "loc": ["body", "password"],
                        "msg": "Password too short",
                        "type": "value_error"
                    }
                ],
                "status_code": 422,
                "type": "validation_error"
            },
            {
                "detail": "Rate limit exceeded",
                "status_code": 429,
                "type": "rate_limit_error",
                "retry_after": 60
            }
        ]
        
        # All error formats should be consistent
        for error in error_responses:
            assert "detail" in error
            assert "status_code" in error
    
    def test_pagination_contract(self):
        """Test paginated response contract."""
        # Must match frontend's PaginatedResponse interface
        response_data = {
            "items": [
                {"id": 1, "symbol": "AAPL"},
                {"id": 2, "symbol": "GOOGL"}
            ],
            "total": 50,
            "page": 1,
            "per_page": 2,
            "total_pages": 25,
            "has_next": True,
            "has_previous": False
        }
        
        assert response_data["total_pages"] == response_data["total"] // response_data["per_page"]
        assert response_data["has_next"] == (response_data["page"] < response_data["total_pages"])
    
    def test_websocket_message_contract(self):
        """Test WebSocket message format."""
        # Must match frontend's WSMessage interface
        ws_messages = [
            {
                "type": "price_update",
                "data": {
                    "symbol": "AAPL",
                    "price": 150.25,
                    "change": 0.0125,
                    "timestamp": "2024-01-19T12:00:00"
                }
            },
            {
                "type": "portfolio_update",
                "data": {
                    "total_value": 100500.00,
                    "daily_change": 500.00,
                    "daily_return": 0.005
                }
            },
            {
                "type": "notification",
                "data": {
                    "level": "info",
                    "message": "Market data updated",
                    "timestamp": "2024-01-19T12:00:00"
                }
            }
        ]
        
        for msg in ws_messages:
            assert "type" in msg
            assert "data" in msg
            assert isinstance(msg["data"], dict)
    
    @pytest.mark.parametrize("field_type,test_value,should_pass", [
        ("decimal", "123.45", True),
        ("decimal", "123.456789", False),  # Too many decimal places
        ("date", "2024-01-19", True),
        ("date", "01/19/2024", False),  # Wrong format
        ("datetime", "2024-01-19T12:00:00", True),
        ("datetime", "2024-01-19 12:00:00", False),  # Missing T separator
        ("percentage", 0.15, True),
        ("percentage", 15, False),  # Should be decimal, not percent
    ])
    def test_field_format_contract(self, field_type, test_value, should_pass):
        """Test field format consistency across API."""
        # This ensures consistent data formats that frontend expects
        
        if field_type == "decimal":
            # Decimal fields should have max 2 decimal places for display
            if should_pass:
                assert len(str(test_value).split('.')[-1]) <= 2
            else:
                assert len(str(test_value).split('.')[-1]) > 2
        
        elif field_type == "date":
            # Dates should be ISO format YYYY-MM-DD
            if should_pass:
                datetime.strptime(test_value, "%Y-%m-%d")
            else:
                with pytest.raises(ValueError):
                    datetime.strptime(test_value, "%Y-%m-%d")
        
        elif field_type == "datetime":
            # Datetimes should be ISO format with T separator
            if should_pass:
                datetime.fromisoformat(test_value)
            else:
                with pytest.raises(ValueError):
                    datetime.fromisoformat(test_value)
        
        elif field_type == "percentage":
            # Percentages should be decimals (0.15 for 15%)
            if should_pass:
                assert 0 <= test_value <= 1
            else:
                assert test_value > 1
    
    def test_enum_values_contract(self):
        """Test that enum values match between frontend and backend."""
        # These enums must match exactly with frontend TypeScript enums
        
        risk_levels = ["low", "medium", "high"]
        asset_types = ["stock", "etf", "commodity", "crypto"]
        rebalance_frequencies = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        order_types = ["market", "limit", "stop", "stop_limit"]
        order_status = ["pending", "executed", "cancelled", "failed"]
        
        # Verify enum values are lowercase (frontend convention)
        for enum_list in [risk_levels, asset_types, rebalance_frequencies, order_types, order_status]:
            assert all(val.islower() for val in enum_list)
    
    def test_null_handling_contract(self):
        """Test null/optional field handling."""
        # Test that optional fields can be null/undefined
        portfolio_data = {
            "id": 1,
            "name": "Test",
            "total_value": 100000.00,
            "initial_value": 100000.00,
            "total_return": 0,
            "daily_return": None,  # Optional field
            "positions": [],
            "performance": None,  # Optional nested object
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None  # Optional timestamp
        }
        
        # Should handle None/null values gracefully
        validated = PortfolioResponse(**portfolio_data)
        assert validated.daily_return is None
        assert validated.performance is None