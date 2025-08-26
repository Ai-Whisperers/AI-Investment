"""SQLAlchemy implementation of the Price repository."""

from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
import logging

from .interfaces import IPriceRepository
from ..models import Price, Asset

logger = logging.getLogger(__name__)


class SQLPriceRepository(IPriceRepository):
    """SQLAlchemy implementation of price repository."""
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_latest(self, asset_id: int) -> Optional[Price]:
        """Get latest price for an asset.
        
        Args:
            asset_id: Asset ID
            
        Returns:
            Latest price model or None if not found
        """
        return (
            self.db.query(Price)
            .filter(Price.asset_id == asset_id)
            .order_by(Price.date.desc())
            .first()
        )
    
    def get_history(
        self, 
        asset_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Price]:
        """Get price history for an asset with pagination support.
        
        Args:
            asset_id: Asset ID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of price models
        """
        query = self.db.query(Price).filter(Price.asset_id == asset_id)
        
        if start_date:
            query = query.filter(Price.date >= start_date)
        
        if end_date:
            query = query.filter(Price.date <= end_date)
        
        query = query.order_by(Price.date.asc())
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_history_by_symbol(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Price]:
        """Get price history by asset symbol with pagination support.
        
        Uses eager loading to avoid N+1 queries.
        
        Args:
            symbol: Asset symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of price models with asset loaded
        """
        query = (
            self.db.query(Price)
            .join(Asset)
            .options(joinedload(Price.asset))  # Eager load asset to avoid N+1
            .filter(Asset.symbol == symbol.upper())
        )
        
        if start_date:
            query = query.filter(Price.date >= start_date)
        
        if end_date:
            query = query.filter(Price.date <= end_date)
        
        query = query.order_by(Price.date.asc())
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def create_batch(self, prices: List[Dict[str, Any]]) -> int:
        """Create multiple price records.
        
        Args:
            prices: List of price data dictionaries
            
        Returns:
            Count of created records
        """
        try:
            price_models = [Price(**price_data) for price_data in prices]
            self.db.bulk_save_objects(price_models)
            self.db.commit()
            return len(price_models)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create batch prices: {e}")
            raise
    
    def delete_old(self, before_date: date) -> int:
        """Delete prices older than specified date.
        
        Args:
            before_date: Delete prices before this date
            
        Returns:
            Count of deleted records
        """
        try:
            deleted_count = (
                self.db.query(Price)
                .filter(Price.date < before_date)
                .delete()
            )
            self.db.commit()
            return deleted_count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete old prices: {e}")
            raise
    
    def get_price_range(self, asset_id: int) -> Dict[str, Any]:
        """Get min, max, avg price for an asset.
        
        Args:
            asset_id: Asset ID
            
        Returns:
            Dictionary with min, max, avg, count statistics
        """
        result = self.db.query(
            func.min(Price.close).label('min_price'),
            func.max(Price.close).label('max_price'),
            func.avg(Price.close).label('avg_price'),
            func.count(Price.id).label('count')
        ).filter(Price.asset_id == asset_id).first()
        
        return {
            'min_price': result.min_price,
            'max_price': result.max_price,
            'avg_price': float(result.avg_price) if result.avg_price else None,
            'count': result.count
        }