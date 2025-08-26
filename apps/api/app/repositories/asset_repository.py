"""SQLAlchemy implementation of the Asset repository."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from .interfaces import IAssetRepository
from ..models import Asset

logger = logging.getLogger(__name__)


class SQLAssetRepository(IAssetRepository):
    """SQLAlchemy implementation of asset repository."""
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, asset_id: int) -> Optional[Asset]:
        """Get asset by ID.
        
        Args:
            asset_id: Asset ID
            
        Returns:
            Asset model or None if not found
        """
        return self.db.query(Asset).filter(Asset.id == asset_id).first()
    
    def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get asset by symbol.
        
        Args:
            symbol: Asset symbol (e.g., 'AAPL')
            
        Returns:
            Asset model or None if not found
        """
        return self.db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Asset]:
        """Get all assets with optional pagination.
        
        Args:
            limit: Maximum number of assets to return
            offset: Number of assets to skip
            
        Returns:
            List of asset models
        """
        query = self.db.query(Asset)
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_by_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type.
        
        Args:
            asset_type: Asset type (stock, etf, commodity)
            
        Returns:
            List of asset models
        """
        return self.db.query(Asset).filter(Asset.asset_type == asset_type.lower()).all()
    
    def create(self, symbol: str, name: str, asset_type: str, **kwargs) -> Asset:
        """Create a new asset.
        
        Args:
            symbol: Asset symbol
            name: Asset name
            asset_type: Asset type
            **kwargs: Additional attributes
            
        Returns:
            Created asset model
        """
        try:
            asset = Asset(
                symbol=symbol.upper(),
                name=name,
                asset_type=asset_type.lower(),
                **kwargs
            )
            self.db.add(asset)
            self.db.commit()
            self.db.refresh(asset)
            return asset
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create asset: {e}")
            raise
    
    def update(self, asset_id: int, **kwargs) -> Optional[Asset]:
        """Update asset attributes.
        
        Args:
            asset_id: Asset ID
            **kwargs: Attributes to update
            
        Returns:
            Updated asset model or None if not found
        """
        asset = self.get_by_id(asset_id)
        if not asset:
            return None
        
        # Update only provided attributes
        for key, value in kwargs.items():
            if hasattr(asset, key):
                setattr(asset, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(asset)
            return asset
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update asset {asset_id}: {e}")
            raise
    
    def search(self, query: str) -> List[Asset]:
        """Search assets by symbol or name.
        
        Args:
            query: Search query
            
        Returns:
            List of matching asset models
        """
        search_term = f"%{query}%"
        return self.db.query(Asset).filter(
            or_(
                Asset.symbol.ilike(search_term),
                Asset.name.ilike(search_term)
            )
        ).all()