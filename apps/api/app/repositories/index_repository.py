"""
Repository for index-related operations.
Abstracts database access for index data, allocations, and simulations.
"""

import logging
from datetime import date
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..models.asset import Asset, Price
from ..models.index import Allocation, IndexValue

logger = logging.getLogger(__name__)


class IndexRepository:
    """Repository for index and allocation data operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_latest_allocation_date(self) -> Optional[date]:
        """Get the latest allocation date."""
        try:
            return self.db.query(func.max(Allocation.date)).scalar()
        except Exception as e:
            logger.error(f"Error getting latest allocation date: {e}")
            return None
    
    def get_current_allocations(self) -> List[Tuple[Allocation, Asset]]:
        """Get current allocations with asset information."""
        try:
            latest_date = self.get_latest_allocation_date()
            if not latest_date:
                return []
            
            return (
                self.db.query(Allocation, Asset)
                .join(Asset, Allocation.asset_id == Asset.id)
                .filter(Allocation.date == latest_date)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting current allocations: {e}")
            return []
    
    def get_index_history(self, limit: Optional[int] = None) -> List[IndexValue]:
        """Get index history ordered by date."""
        try:
            query = self.db.query(IndexValue).order_by(IndexValue.date.asc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting index history: {e}")
            return []
    
    def get_index_history_range(
        self, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[IndexValue]:
        """Get index history within date range."""
        try:
            query = self.db.query(IndexValue).order_by(IndexValue.date.asc())
            
            if start_date:
                query = query.filter(IndexValue.date >= start_date)
            if end_date:
                query = query.filter(IndexValue.date <= end_date)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting index history range: {e}")
            return []
    
    def get_asset_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get asset by symbol."""
        try:
            return (
                self.db.query(Asset)
                .filter(Asset.symbol == symbol)
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting asset {symbol}: {e}")
            return None
    
    def get_asset_prices_since_date(
        self, 
        asset_id: int, 
        since_date: date
    ) -> List[Price]:
        """Get asset prices since a specific date."""
        try:
            return (
                self.db.query(Price)
                .filter(
                    Price.asset_id == asset_id,
                    Price.date >= since_date
                )
                .order_by(Price.date.asc())
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting prices for asset {asset_id}: {e}")
            return []
    
    def get_index_value_at_date(self, target_date: date) -> Optional[IndexValue]:
        """Get index value at a specific date."""
        try:
            return (
                self.db.query(IndexValue)
                .filter(IndexValue.date == target_date)
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting index value at {target_date}: {e}")
            return None
    
    def get_index_value_near_date(self, target_date: date) -> Optional[IndexValue]:
        """Get index value closest to a specific date."""
        try:
            # Try exact date first
            exact = self.get_index_value_at_date(target_date)
            if exact:
                return exact
            
            # Find closest date before target
            return (
                self.db.query(IndexValue)
                .filter(IndexValue.date <= target_date)
                .order_by(IndexValue.date.desc())
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting index value near {target_date}: {e}")
            return None
    
    def get_allocations_at_date(self, target_date: date) -> List[Tuple[Allocation, Asset]]:
        """Get allocations with assets at a specific date."""
        try:
            return (
                self.db.query(Allocation, Asset)
                .join(Asset, Allocation.asset_id == Asset.id)
                .filter(Allocation.date == target_date)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting allocations at {target_date}: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            total_values = self.db.query(func.count()).select_from(IndexValue).scalar()
            total_allocations = self.db.query(func.count()).select_from(Allocation).scalar()
            
            latest_value = (
                self.db.query(IndexValue)
                .order_by(IndexValue.date.desc())
                .first()
            )
            
            earliest_value = (
                self.db.query(IndexValue)
                .order_by(IndexValue.date.asc())
                .first()
            )
            
            return {
                "total_index_values": total_values,
                "total_allocations": total_allocations,
                "latest_date": latest_value.date if latest_value else None,
                "latest_value": latest_value.value if latest_value else None,
                "earliest_date": earliest_value.date if earliest_value else None,
                "date_range_days": (
                    (latest_value.date - earliest_value.date).days
                    if latest_value and earliest_value
                    else 0
                )
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}