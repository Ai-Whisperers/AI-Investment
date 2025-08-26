"""SQLAlchemy implementation of the Portfolio repository."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from .interfaces import IPortfolioRepository
from ..models import Portfolio, Allocation

logger = logging.getLogger(__name__)


class SQLPortfolioRepository(IPortfolioRepository):
    """SQLAlchemy implementation of portfolio repository."""
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio by ID.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio model or None if not found
        """
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    def get_by_user(self, user_id: int) -> List[Portfolio]:
        """Get all portfolios for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of portfolio models
        """
        return self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    
    def create(self, user_id: int, name: str, **kwargs) -> Portfolio:
        """Create a new portfolio.
        
        Args:
            user_id: User ID
            name: Portfolio name
            **kwargs: Additional attributes
            
        Returns:
            Created portfolio model
        """
        try:
            portfolio = Portfolio(
                user_id=user_id,
                name=name,
                **kwargs
            )
            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)
            return portfolio
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create portfolio: {e}")
            raise
    
    def update(self, portfolio_id: int, **kwargs) -> Optional[Portfolio]:
        """Update portfolio attributes.
        
        Args:
            portfolio_id: Portfolio ID
            **kwargs: Attributes to update
            
        Returns:
            Updated portfolio model or None if not found
        """
        portfolio = self.get_by_id(portfolio_id)
        if not portfolio:
            return None
        
        # Update only provided attributes
        for key, value in kwargs.items():
            if hasattr(portfolio, key):
                setattr(portfolio, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(portfolio)
            return portfolio
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update portfolio {portfolio_id}: {e}")
            raise
    
    def delete(self, portfolio_id: int) -> bool:
        """Delete a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            True if deleted, False if not found
        """
        portfolio = self.get_by_id(portfolio_id)
        if not portfolio:
            return False
        
        try:
            # Cascade delete should handle allocations
            self.db.delete(portfolio)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete portfolio {portfolio_id}: {e}")
            raise
    
    def add_asset(self, portfolio_id: int, asset_id: int, weight: float) -> bool:
        """Add an asset to portfolio with specified weight.
        
        Args:
            portfolio_id: Portfolio ID
            asset_id: Asset ID
            weight: Allocation weight (0-1)
            
        Returns:
            True if added successfully
        """
        try:
            # Check if allocation already exists
            existing = self.db.query(Allocation).filter(
                Allocation.portfolio_id == portfolio_id,
                Allocation.asset_id == asset_id
            ).first()
            
            if existing:
                # Update existing allocation
                existing.weight = weight
            else:
                # Create new allocation
                allocation = Allocation(
                    portfolio_id=portfolio_id,
                    asset_id=asset_id,
                    weight=weight
                )
                self.db.add(allocation)
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add asset to portfolio: {e}")
            raise
    
    def remove_asset(self, portfolio_id: int, asset_id: int) -> bool:
        """Remove an asset from portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            asset_id: Asset ID
            
        Returns:
            True if removed, False if not found
        """
        try:
            deleted = self.db.query(Allocation).filter(
                Allocation.portfolio_id == portfolio_id,
                Allocation.asset_id == asset_id
            ).delete()
            
            self.db.commit()
            return deleted > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove asset from portfolio: {e}")
            raise
    
    def get_allocations(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Get all asset allocations for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            List of allocation dictionaries
        """
        allocations = self.db.query(Allocation).filter(
            Allocation.portfolio_id == portfolio_id
        ).all()
        
        return [
            {
                'asset_id': alloc.asset_id,
                'weight': alloc.weight,
                'created_at': alloc.created_at,
                'updated_at': alloc.updated_at
            }
            for alloc in allocations
        ]