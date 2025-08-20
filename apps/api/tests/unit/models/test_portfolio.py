"""
Unit tests for Portfolio model.
Tests database operations and model validation.
"""

import pytest
from datetime import datetime
from app.models.portfolio import Portfolio
from app.models.user import User
from tests.factories import UserFactory, PortfolioFactory


@pytest.mark.unit
class TestPortfolioModel:
    """Test Portfolio model functionality."""
    
    def test_portfolio_creation(self, test_db_session):
        """Test basic portfolio creation."""
        # Create a user first
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Create portfolio
        portfolio_data = PortfolioFactory.create_portfolio_data()
        portfolio = Portfolio(
            user_id=user.id,
            name=portfolio_data["name"],
            description=portfolio_data["description"],
            total_value=portfolio_data["total_value"],
            strategy_config=portfolio_data["strategy_config"]
        )
        
        test_db_session.add(portfolio)
        test_db_session.commit()
        test_db_session.refresh(portfolio)
        
        # Verify portfolio was created correctly
        assert portfolio.id is not None
        assert portfolio.user_id == user.id
        assert portfolio.name == portfolio_data["name"]
        assert portfolio.description == portfolio_data["description"]
        assert portfolio.total_value == portfolio_data["total_value"]
        assert portfolio.returns == 0.0  # Default value
        assert portfolio.strategy_config == portfolio_data["strategy_config"]
        assert portfolio.created_at is not None
        assert portfolio.updated_at is not None
    
    def test_portfolio_user_relationship(self, test_db_session):
        """Test relationship between Portfolio and User."""
        # Create user
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Create portfolio
        portfolio = Portfolio(
            user_id=user.id,
            name="Test Portfolio",
            description="A test portfolio",
            total_value=10000.0
        )
        test_db_session.add(portfolio)
        test_db_session.commit()
        test_db_session.refresh(portfolio)
        
        # Test relationship
        assert portfolio.user == user
        assert user.portfolios == [portfolio]
    
    def test_portfolio_default_values(self, test_db_session):
        """Test portfolio default values."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Create minimal portfolio
        portfolio = Portfolio(
            user_id=user.id,
            name="Minimal Portfolio"
        )
        test_db_session.add(portfolio)
        test_db_session.commit()
        test_db_session.refresh(portfolio)
        
        # Check defaults
        assert portfolio.description is None
        assert portfolio.total_value == 0.0
        assert portfolio.returns == 0.0
        assert portfolio.strategy_config is None
        assert isinstance(portfolio.created_at, datetime)
        assert isinstance(portfolio.updated_at, datetime)
    
    def test_portfolio_json_strategy_config(self, test_db_session):
        """Test JSON strategy configuration storage."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Complex strategy configuration
        complex_config = {
            "strategy_type": "momentum",
            "rebalance_frequency": "monthly",
            "risk_tolerance": "moderate",
            "constraints": {
                "max_weight_per_asset": 0.25,
                "min_weight_per_asset": 0.01,
                "max_sectors": 10
            },
            "filters": ["market_cap > 1B", "volume > 1M"],
            "weights": {
                "momentum": 0.4,
                "quality": 0.3,
                "value": 0.3
            }
        }
        
        portfolio = Portfolio(
            user_id=user.id,
            name="Complex Strategy Portfolio",
            strategy_config=complex_config
        )
        
        test_db_session.add(portfolio)
        test_db_session.commit()
        test_db_session.refresh(portfolio)
        
        # Verify JSON serialization/deserialization
        assert portfolio.strategy_config == complex_config
        assert portfolio.strategy_config["strategy_type"] == "momentum"
        assert portfolio.strategy_config["constraints"]["max_weight_per_asset"] == 0.25
    
    def test_portfolio_updates(self, test_db_session):
        """Test portfolio update functionality."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Create portfolio
        portfolio = Portfolio(
            user_id=user.id,
            name="Original Name",
            total_value=5000.0,
            returns=0.0
        )
        test_db_session.add(portfolio)
        test_db_session.commit()
        test_db_session.refresh(portfolio)
        
        original_updated_at = portfolio.updated_at
        
        # Update portfolio
        import time
        time.sleep(0.01)  # Ensure timestamp difference
        
        portfolio.name = "Updated Name"
        portfolio.total_value = 5500.0
        portfolio.returns = 0.1
        
        test_db_session.commit()
        test_db_session.refresh(portfolio)
        
        # Verify updates
        assert portfolio.name == "Updated Name"
        assert portfolio.total_value == 5500.0
        assert portfolio.returns == 0.1
        assert portfolio.updated_at > original_updated_at
    
    def test_multiple_portfolios_per_user(self, test_db_session):
        """Test that a user can have multiple portfolios."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Create multiple portfolios
        portfolios = []
        for i in range(3):
            portfolio = Portfolio(
                user_id=user.id,
                name=f"Portfolio {i+1}",
                description=f"Description for portfolio {i+1}",
                total_value=float((i+1) * 10000)
            )
            portfolios.append(portfolio)
            test_db_session.add(portfolio)
        
        test_db_session.commit()
        
        # Refresh portfolios
        for portfolio in portfolios:
            test_db_session.refresh(portfolio)
        
        # Verify all portfolios belong to user
        user_portfolios = test_db_session.query(Portfolio).filter(
            Portfolio.user_id == user.id
        ).all()
        
        assert len(user_portfolios) == 3
        assert all(p.user_id == user.id for p in user_portfolios)
        assert sorted([p.name for p in user_portfolios]) == [
            "Portfolio 1", "Portfolio 2", "Portfolio 3"
        ]
    
    def test_portfolio_cascade_delete(self, test_db_session):
        """Test portfolio deletion behavior."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Create portfolio
        portfolio = Portfolio(
            user_id=user.id,
            name="Test Portfolio",
            total_value=10000.0
        )
        test_db_session.add(portfolio)
        test_db_session.commit()
        test_db_session.refresh(portfolio)
        
        portfolio_id = portfolio.id
        
        # Delete portfolio
        test_db_session.delete(portfolio)
        test_db_session.commit()
        
        # Verify portfolio is deleted
        deleted_portfolio = test_db_session.query(Portfolio).filter(
            Portfolio.id == portfolio_id
        ).first()
        assert deleted_portfolio is None
        
        # Verify user still exists
        remaining_user = test_db_session.query(User).filter(
            User.id == user.id
        ).first()
        assert remaining_user is not None
    
    def test_portfolio_validation_constraints(self, test_db_session):
        """Test portfolio model constraints and validation."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Test required fields
        with pytest.raises(Exception):  # Should raise IntegrityError
            portfolio = Portfolio(
                # Missing user_id and name
                description="Invalid portfolio"
            )
            test_db_session.add(portfolio)
            test_db_session.commit()
        
        test_db_session.rollback()
        
        # Test invalid user_id
        with pytest.raises(Exception):  # Should raise IntegrityError
            portfolio = Portfolio(
                user_id=99999,  # Non-existent user
                name="Invalid User Portfolio"
            )
            test_db_session.add(portfolio)
            test_db_session.commit()
    
    def test_portfolio_query_performance(self, test_db_session):
        """Test portfolio query performance with multiple records."""
        # Create user
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Create many portfolios
        portfolios = []
        for i in range(100):
            portfolio = Portfolio(
                user_id=user.id,
                name=f"Performance Portfolio {i}",
                total_value=float(i * 1000),
                returns=float(i * 0.01)
            )
            portfolios.append(portfolio)
        
        test_db_session.add_all(portfolios)
        test_db_session.commit()
        
        # Test efficient queries
        import time
        
        # Query by user_id (should be indexed)
        start_time = time.time()
        user_portfolios = test_db_session.query(Portfolio).filter(
            Portfolio.user_id == user.id
        ).all()
        query_time = time.time() - start_time
        
        assert len(user_portfolios) == 100
        assert query_time < 0.1  # Should be fast with proper indexing
        
        # Query by id (primary key)
        start_time = time.time()
        first_portfolio = test_db_session.query(Portfolio).filter(
            Portfolio.id == portfolios[0].id
        ).first()
        query_time = time.time() - start_time
        
        assert first_portfolio is not None
        assert query_time < 0.01  # Primary key lookup should be very fast