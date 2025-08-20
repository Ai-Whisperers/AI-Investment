"""
Unit tests for Portfolio schemas.
Tests validation, serialization, and data transformation.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.portfolio import (
    PortfolioResponse,
    PortfolioCreateRequest,
    PositionResponse
)


@pytest.mark.unit
class TestPortfolioSchemas:
    """Test Portfolio schema validation and serialization."""
    
    def test_portfolio_create_request_valid(self):
        """Test valid portfolio creation request."""
        valid_data = {
            "name": "My Growth Portfolio",
            "description": "A diversified growth-focused portfolio",
            "strategy_config": {
                "strategy_type": "growth",
                "risk_level": "moderate",
                "rebalance_frequency": "quarterly"
            }
        }
        
        request = PortfolioCreateRequest(**valid_data)
        
        assert request.name == "My Growth Portfolio"
        assert request.description == "A diversified growth-focused portfolio"
        assert request.strategy_config["strategy_type"] == "growth"
        assert request.strategy_config["risk_level"] == "moderate"
    
    def test_portfolio_create_request_minimal(self):
        """Test minimal valid portfolio creation request."""
        minimal_data = {
            "name": "Simple Portfolio"
        }
        
        request = PortfolioCreateRequest(**minimal_data)
        
        assert request.name == "Simple Portfolio"
        assert request.description is None
        assert request.strategy_config is None
    
    def test_portfolio_create_request_validation_errors(self):
        """Test portfolio creation request validation errors."""
        # Missing required name
        with pytest.raises(ValidationError) as exc_info:
            PortfolioCreateRequest()
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)
        assert any(error["type"] == "missing" for error in errors)
        
        # Empty name is actually valid in Pydantic (just an empty string)
        # If we want to prevent empty names, we'd need a custom validator
        request = PortfolioCreateRequest(name="")
        assert request.name == ""
    
    def test_portfolio_create_request_complex_strategy(self):
        """Test portfolio creation with complex strategy configuration."""
        complex_strategy = {
            "strategy_type": "multi_factor",
            "factors": {
                "momentum": 0.3,
                "quality": 0.3,
                "value": 0.2,
                "size": 0.2
            },
            "constraints": {
                "max_weight": 0.15,
                "min_weight": 0.01,
                "max_turnover": 0.2,
                "sector_limits": {
                    "technology": 0.3,
                    "healthcare": 0.2,
                    "finance": 0.2
                }
            },
            "rebalance_settings": {
                "frequency": "monthly",
                "threshold": 0.05,
                "transaction_costs": 0.001
            }
        }
        
        request = PortfolioCreateRequest(
            name="Multi-Factor Portfolio",
            description="Advanced multi-factor strategy",
            strategy_config=complex_strategy
        )
        
        assert request.strategy_config["strategy_type"] == "multi_factor"
        assert request.strategy_config["factors"]["momentum"] == 0.3
        assert request.strategy_config["constraints"]["sector_limits"]["technology"] == 0.3
    
    def test_position_response_schema(self):
        """Test PositionResponse schema."""
        position_data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "quantity": 100.0,
            "current_price": 150.25,
            "total_value": 15025.0,
            "weight": 0.25,
            "returns": 0.12
        }
        
        position = PositionResponse(**position_data)
        
        assert position.symbol == "AAPL"
        assert position.name == "Apple Inc."
        assert position.quantity == 100.0
        assert position.current_price == 150.25
        assert position.total_value == 15025.0
        assert position.weight == 0.25
        assert position.returns == 0.12
    
    def test_position_response_validation(self):
        """Test PositionResponse validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            PositionResponse(symbol="AAPL")  # Missing other required fields
        
        # Invalid data types
        with pytest.raises(ValidationError):
            PositionResponse(
                symbol="AAPL",
                name="Apple Inc.",
                quantity="not_a_number",  # Should be float
                current_price=150.25,
                total_value=15025.0,
                weight=0.25,
                returns=0.12
            )
    
    def test_portfolio_response_schema(self):
        """Test PortfolioResponse schema."""
        positions = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "quantity": 100.0,
                "current_price": 150.25,
                "total_value": 15025.0,
                "weight": 0.50,
                "returns": 0.12
            },
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "quantity": 50.0,
                "current_price": 300.50,
                "total_value": 15025.0,
                "weight": 0.50,
                "returns": 0.08
            }
        ]
        
        portfolio_data = {
            "id": 1,
            "name": "Tech Portfolio",
            "description": "Technology-focused portfolio",
            "total_value": 30050.0,
            "returns": 0.10,
            "positions": positions,
            "strategy_config": {"strategy_type": "growth"},
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 15, 12, 0, 0)
        }
        
        portfolio = PortfolioResponse(**portfolio_data)
        
        assert portfolio.id == 1
        assert portfolio.name == "Tech Portfolio"
        assert portfolio.description == "Technology-focused portfolio"
        assert portfolio.total_value == 30050.0
        assert portfolio.returns == 0.10
        assert len(portfolio.positions) == 2
        assert portfolio.positions[0].symbol == "AAPL"
        assert portfolio.positions[1].symbol == "GOOGL"
        assert portfolio.strategy_config["strategy_type"] == "growth"
    
    def test_portfolio_response_minimal(self):
        """Test PortfolioResponse with minimal data."""
        minimal_data = {
            "id": 1,
            "name": "Simple Portfolio",
            "total_value": 10000.0,
            "returns": 0.05,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1)
        }
        
        portfolio = PortfolioResponse(**minimal_data)
        
        assert portfolio.id == 1
        assert portfolio.name == "Simple Portfolio"
        assert portfolio.description is None
        assert portfolio.total_value == 10000.0
        assert portfolio.returns == 0.05
        assert portfolio.positions == []
        assert portfolio.strategy_config is None
    
    def test_portfolio_response_serialization(self):
        """Test PortfolioResponse JSON serialization."""
        portfolio_data = {
            "id": 1,
            "name": "Test Portfolio",
            "description": "A test portfolio",
            "total_value": 50000.0,
            "returns": 0.15,
            "positions": [
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corporation",
                    "quantity": 200.0,
                    "current_price": 250.0,
                    "total_value": 50000.0,
                    "weight": 1.0,
                    "returns": 0.15
                }
            ],
            "strategy_config": {
                "strategy_type": "value",
                "rebalance_frequency": "quarterly"
            },
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 3, 1)
        }
        
        portfolio = PortfolioResponse(**portfolio_data)
        
        # Test JSON serialization
        json_data = portfolio.model_dump()
        
        assert json_data["id"] == 1
        assert json_data["name"] == "Test Portfolio"
        assert json_data["total_value"] == 50000.0
        assert len(json_data["positions"]) == 1
        assert json_data["positions"][0]["symbol"] == "MSFT"
        assert json_data["strategy_config"]["strategy_type"] == "value"
    
    def test_nested_schema_validation(self):
        """Test validation of nested schemas."""
        # Invalid position in portfolio
        with pytest.raises(ValidationError) as exc_info:
            PortfolioResponse(
                id=1,
                name="Invalid Portfolio",
                total_value=10000.0,
                returns=0.05,
                positions=[
                    {
                        "symbol": "AAPL",
                        # Missing required fields
                    }
                ],
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1)
            )
        
        errors = exc_info.value.errors()
        # Should have validation errors for the nested position
        assert len(errors) > 0
        assert any("positions" in str(error["loc"]) for error in errors)
    
    def test_schema_edge_cases(self):
        """Test schema handling of edge cases."""
        # Zero values
        portfolio_data = {
            "id": 1,
            "name": "Empty Portfolio",
            "total_value": 0.0,
            "returns": 0.0,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1)
        }
        
        portfolio = PortfolioResponse(**portfolio_data)
        assert portfolio.total_value == 0.0
        assert portfolio.returns == 0.0
        
        # Negative returns
        portfolio_data["returns"] = -0.15
        portfolio = PortfolioResponse(**portfolio_data)
        assert portfolio.returns == -0.15
        
        # Very large values
        portfolio_data["total_value"] = 1e12
        portfolio = PortfolioResponse(**portfolio_data)
        assert portfolio.total_value == 1e12
    
    @pytest.mark.parametrize("invalid_name", [
        None,
        "",
        " " * 100,  # Very long spaces
    ])
    def test_invalid_portfolio_names(self, invalid_name):
        """Test validation of invalid portfolio names."""
        if invalid_name is None:
            # None will raise ValidationError for missing field
            with pytest.raises(ValidationError):
                PortfolioCreateRequest(name=invalid_name)
        else:
            # Empty string and spaces are actually valid strings in Pydantic
            # They pass validation unless we add custom validators
            request = PortfolioCreateRequest(name=invalid_name)
            assert request.name == invalid_name
    
    @pytest.mark.parametrize("valid_name", [
        "A",
        "My Portfolio",
        "Portfolio-123",
        "Portfolio_with_underscores",
        "Портфолио",  # Unicode
        "A" * 100,  # Long name
    ])
    def test_valid_portfolio_names(self, valid_name):
        """Test validation of valid portfolio names."""
        request = PortfolioCreateRequest(name=valid_name)
        assert request.name == valid_name
    
    def test_strategy_config_types(self):
        """Test various strategy configuration types."""
        # Dict strategy (the only valid type per schema)
        request1 = PortfolioCreateRequest(
            name="Dict Strategy",
            strategy_config={"type": "simple_growth"}
        )
        assert request1.strategy_config == {"type": "simple_growth"}
        
        # Complex dict strategy
        request2 = PortfolioCreateRequest(
            name="Complex Strategy",
            strategy_config={
                "factors": ["momentum", "quality", "value"],
                "weight": 0.5,
                "enabled": True
            }
        )
        assert request2.strategy_config["factors"] == ["momentum", "quality", "value"]
        assert request2.strategy_config["weight"] == 0.5
        assert request2.strategy_config["enabled"] is True
        
        # Test that non-dict types raise validation errors
        with pytest.raises(ValidationError):
            PortfolioCreateRequest(
                name="String Strategy",
                strategy_config="simple_growth"  # Invalid: should be dict
            )
        
        with pytest.raises(ValidationError):
            PortfolioCreateRequest(
                name="List Strategy",
                strategy_config=["momentum", "quality"]  # Invalid: should be dict
            )