"""
Integration tests for Portfolio functionality.
Tests complete portfolio workflows including calculations and optimization.
"""

import pytest

from app.models.portfolio import Portfolio
from app.models.user import User
from tests.factories import UserFactory


@pytest.mark.integration
class TestPortfolioIntegration:
    """Test portfolio integration workflows."""

    def test_complete_portfolio_creation_workflow(self, test_db_session):
        """Test complete portfolio creation workflow."""
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
        portfolio_data = {
            "name": "Integration Test Portfolio",
            "description": "A portfolio created through integration test",
            "strategy_config": {
                "strategy_type": "balanced",
                "risk_tolerance": "moderate"
            }
        }

        portfolio = Portfolio(
            user_id=user.id,
            name=portfolio_data["name"],
            description=portfolio_data["description"],
            strategy_config=portfolio_data["strategy_config"],
            total_value=10000.0
        )

        test_db_session.add(portfolio)
        test_db_session.commit()
        test_db_session.refresh(portfolio)

        # Verify portfolio was created correctly
        assert portfolio.id is not None
        assert portfolio.user_id == user.id
        assert portfolio.name == portfolio_data["name"]
        assert portfolio.strategy_config["strategy_type"] == "balanced"

    def test_multi_user_portfolio_isolation(self, test_db_session):
        """Test that portfolios are properly isolated between users."""
        # Create two users
        user1_data = UserFactory.create_user_data()
        user1 = User(
            email=user1_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )

        user2_data = UserFactory.create_user_data()
        user2 = User(
            email=user2_data["email"],
            password_hash="hashed_password",
            is_google_user=False
        )

        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        # Create portfolios for each user
        portfolio1 = Portfolio(
            user_id=user1.id,
            name="User 1 Portfolio",
            total_value=25000.0
        )

        portfolio2 = Portfolio(
            user_id=user2.id,
            name="User 2 Portfolio",
            total_value=50000.0
        )

        test_db_session.add_all([portfolio1, portfolio2])
        test_db_session.commit()

        # Verify portfolio isolation
        user1_portfolios = test_db_session.query(Portfolio).filter(
            Portfolio.user_id == user1.id
        ).all()

        user2_portfolios = test_db_session.query(Portfolio).filter(
            Portfolio.user_id == user2.id
        ).all()

        assert len(user1_portfolios) == 1
        assert len(user2_portfolios) == 1
        assert user1_portfolios[0].name == "User 1 Portfolio"
        assert user2_portfolios[0].name == "User 2 Portfolio"
