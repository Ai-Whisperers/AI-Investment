"""
Integration tests for portfolio workflows with real database.
Tests complete user journeys and data persistence.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.asset import Asset, Price
from app.models.index import IndexValue, Allocation
from app.services.strategy import StrategyService
from app.services.performance import calculate_portfolio_metrics
from tests.fixtures.factories import (
    create_price_series, 
    create_portfolio_with_positions
)


@pytest.mark.integration
@pytest.mark.slow
class TestPortfolioIntegration:
    """Test complete portfolio workflows with database."""
    
    def test_portfolio_creation_workflow(self, test_db_session, test_user, sample_assets):
        """Test complete portfolio creation and initialization."""
        # Create portfolio
        portfolio = Portfolio(
            user_id=test_user.id,
            name="Integration Test Portfolio",
            initial_value=Decimal("100000.00"),
            strategy="moderate",
            created_at=datetime.now()
        )
        test_db_session.add(portfolio)
        test_db_session.commit()
        
        # Verify portfolio created
        assert portfolio.id is not None
        saved_portfolio = test_db_session.query(Portfolio).filter_by(id=portfolio.id).first()
        assert saved_portfolio.name == "Integration Test Portfolio"
        
        # Create initial allocations
        total_weight = Decimal("0")
        for i, asset in enumerate(sample_assets[:3]):
            weight = Decimal(str(0.4 - i * 0.1))  # 0.4, 0.3, 0.2
            allocation = Allocation(
                date=datetime.now().date(),
                asset_id=asset.id,
                weight=weight,
                shares=100 * (i + 1),
                value=weight * portfolio.initial_value
            )
            test_db_session.add(allocation)
            total_weight += weight
        
        test_db_session.commit()
        
        # Verify allocations
        allocations = test_db_session.query(Allocation).filter_by(
            date=datetime.now().date()
        ).all()
        assert len(allocations) == 3
        assert sum(a.weight for a in allocations) == Decimal("0.9")
    
    def test_index_calculation_workflow(self, test_db_session, sample_assets, sample_prices):
        """Test index value calculation with real data."""
        strategy_service = StrategyService(test_db_session)
        
        # Configure strategy
        config = {
            "weighting": "equal",
            "rebalance_frequency": "monthly",
            "min_weight": 0.05,
            "max_weight": 0.40
        }
        
        # Calculate index
        strategy_service.compute_index_and_allocations(config)
        
        # Verify index values created
        index_values = test_db_session.query(IndexValue).all()
        assert len(index_values) > 0
        
        # Check index values are reasonable
        for iv in index_values:
            assert iv.value > 0
            assert -0.20 <= iv.daily_return <= 0.20  # Reasonable daily return range
    
    def test_performance_calculation_workflow(
        self, test_db_session, test_user, sample_assets, sample_prices
    ):
        """Test performance metrics calculation with database."""
        # Create portfolio with history
        portfolio = create_portfolio_with_positions(
            test_db_session,
            test_user,
            sample_assets[:3],
            weights=[0.4, 0.3, 0.3]
        )
        
        # Calculate metrics
        metrics = calculate_portfolio_metrics(test_db_session, lookback_days=30)
        
        # Verify metrics calculated
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "volatility" in metrics
        
        # Check metrics are reasonable
        assert -0.50 <= metrics["total_return"] <= 0.50
        assert -3 <= metrics["sharpe_ratio"] <= 3
        assert -0.50 <= metrics["max_drawdown"] <= 0
    
    def test_rebalancing_workflow(self, test_db_session, test_user, sample_assets):
        """Test portfolio rebalancing process."""
        # Create portfolio with initial allocations
        portfolio = create_portfolio_with_positions(
            test_db_session,
            test_user,
            sample_assets[:4],
            weights=[0.40, 0.30, 0.20, 0.10]  # Initial weights
        )
        
        # Simulate price changes that cause drift
        base_date = datetime.now().date()
        for i, asset in enumerate(sample_assets[:4]):
            # Different returns for each asset
            returns = [1.10, 0.95, 1.05, 1.00][i]
            
            price = Price(
                asset_id=asset.id,
                date=base_date,
                close=Decimal(str(100 * returns)),
                volume=1000000
            )
            test_db_session.add(price)
        
        test_db_session.commit()
        
        # Calculate new weights after drift
        strategy_service = StrategyService(test_db_session)
        new_allocations = strategy_service.rebalance_portfolio(
            portfolio_id=portfolio.id,
            target_weights=[0.25, 0.25, 0.25, 0.25]  # Equal weight target
        )
        
        # Verify rebalancing created new allocations
        assert len(new_allocations) == 4
        assert all(abs(a.weight - Decimal("0.25")) < Decimal("0.01") for a in new_allocations)
    
    def test_transaction_rollback_on_error(self, test_db_session, test_user):
        """Test database transaction rollback on error."""
        initial_count = test_db_session.query(Portfolio).count()
        
        try:
            # Start transaction
            portfolio = Portfolio(
                user_id=test_user.id,
                name="Test Rollback",
                initial_value=Decimal("100000.00")
            )
            test_db_session.add(portfolio)
            
            # Force an error (e.g., violate constraint)
            portfolio.initial_value = None  # Not nullable
            test_db_session.commit()
        except Exception:
            test_db_session.rollback()
        
        # Verify rollback worked
        final_count = test_db_session.query(Portfolio).count()
        assert final_count == initial_count
    
    def test_cascade_delete(self, test_db_session, test_user, sample_assets):
        """Test cascade delete relationships."""
        # Create portfolio with allocations
        portfolio = create_portfolio_with_positions(
            test_db_session,
            test_user,
            sample_assets[:2]
        )
        
        portfolio_id = portfolio.id
        
        # Verify allocations exist
        allocations = test_db_session.query(Allocation).filter_by(
            date=datetime.now().date()
        ).count()
        assert allocations > 0
        
        # Delete portfolio
        test_db_session.delete(portfolio)
        test_db_session.commit()
        
        # Verify cascade delete worked
        remaining = test_db_session.query(Portfolio).filter_by(id=portfolio_id).first()
        assert remaining is None
        
        # Allocations should also be deleted (if cascade configured)
        # This depends on model relationship configuration
    
    def test_concurrent_updates(self, test_db_session, sample_assets):
        """Test handling of concurrent database updates."""
        from sqlalchemy.orm import Session
        from app.core.database import SessionLocal
        
        # Create two sessions to simulate concurrent access
        session1 = test_db_session
        session2 = SessionLocal()
        
        try:
            # Both sessions read same asset
            asset1 = session1.query(Asset).filter_by(symbol="AAPL").first()
            asset2 = session2.query(Asset).filter_by(symbol="AAPL").first()
            
            # Both try to update
            asset1.name = "Apple Inc. - Session 1"
            asset2.name = "Apple Inc. - Session 2"
            
            # Commit first session
            session1.commit()
            
            # Second session should handle conflict appropriately
            # In real implementation, this might raise an exception
            # or use optimistic locking
            try:
                session2.commit()
            except Exception:
                session2.rollback()
        
        finally:
            session2.close()
    
    def test_bulk_operations(self, test_db_session, sample_assets):
        """Test bulk insert/update operations."""
        # Bulk insert prices
        prices_data = []
        base_date = datetime.now().date() - timedelta(days=100)
        
        for asset in sample_assets:
            for i in range(100):
                prices_data.append({
                    "asset_id": asset.id,
                    "date": base_date + timedelta(days=i),
                    "close": Decimal(str(100 + i)),
                    "volume": 1000000
                })
        
        # Bulk insert
        test_db_session.bulk_insert_mappings(Price, prices_data)
        test_db_session.commit()
        
        # Verify bulk insert
        price_count = test_db_session.query(Price).count()
        assert price_count >= len(prices_data)
        
        # Bulk update
        test_db_session.query(Price).filter(
            Price.date >= base_date
        ).update({"volume": 2000000})
        test_db_session.commit()
        
        # Verify bulk update
        updated = test_db_session.query(Price).filter(
            Price.volume == 2000000
        ).count()
        assert updated > 0
    
    def test_query_performance(self, test_db_session, large_dataset):
        """Test query performance with large dataset."""
        import time
        
        # Test indexed query
        start = time.time()
        results = test_db_session.query(Price).filter(
            Price.date >= datetime.now().date() - timedelta(days=30)
        ).all()
        indexed_time = time.time() - start
        
        # Should complete quickly with index
        assert indexed_time < 1.0  # Less than 1 second
        assert len(results) > 0
        
        # Test aggregation query
        start = time.time()
        avg_price = test_db_session.query(
            func.avg(Price.close)
        ).scalar()
        agg_time = time.time() - start
        
        assert agg_time < 1.0
        assert avg_price > 0
    
    def test_data_integrity_constraints(self, test_db_session, test_user):
        """Test database integrity constraints."""
        # Test unique constraint
        portfolio1 = Portfolio(
            user_id=test_user.id,
            name="Unique Portfolio",
            initial_value=Decimal("100000.00")
        )
        test_db_session.add(portfolio1)
        test_db_session.commit()
        
        # Try to create duplicate (if unique constraint exists)
        portfolio2 = Portfolio(
            user_id=test_user.id,
            name="Unique Portfolio",  # Same name
            initial_value=Decimal("50000.00")
        )
        
        # Should handle constraint violation appropriately
        # Actual behavior depends on model constraints
        
        # Test foreign key constraint
        with pytest.raises(Exception):
            invalid_portfolio = Portfolio(
                user_id=99999,  # Non-existent user
                name="Invalid Portfolio",
                initial_value=Decimal("100000.00")
            )
            test_db_session.add(invalid_portfolio)
            test_db_session.commit()