"""
Enhanced asset repository with advanced filtering capabilities.
Extends basic repository to support complex queries needed by assets router.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

from ..models import Asset

logger = logging.getLogger(__name__)


class EnhancedAssetRepository:
    """Enhanced repository for asset operations with filtering."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db
    
    def get_filtered_assets(
        self,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        market_cap_category: Optional[str] = None,
        min_esg_score: Optional[float] = None,
        tags: Optional[List[str]] = None,
        min_market_cap: Optional[int] = None,
        max_volatility: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Asset]:
        """
        Get assets with advanced filtering.
        
        Args:
            sector: Filter by sector
            industry: Filter by industry
            market_cap_category: Filter by market cap category
            min_esg_score: Minimum ESG score
            tags: Filter by tags
            min_market_cap: Minimum market cap
            max_volatility: Maximum 30-day volatility
            limit: Maximum number of results
            offset: Skip this many results
            
        Returns:
            List of filtered assets
        """
        query = self.db.query(Asset)
        
        # Apply filters
        if sector:
            query = query.filter(Asset.sector == sector)
        
        if industry:
            query = query.filter(Asset.industry == industry)
        
        if market_cap_category:
            query = query.filter(Asset.market_cap_category == market_cap_category)
        
        if min_esg_score is not None:
            query = query.filter(Asset.esg_score >= min_esg_score)
        
        if tags:
            # Filter assets that have any of the specified tags
            tag_filters = []
            for tag in tags:
                tag_filters.append(func.json_contains(Asset.tags, f'"{tag}"'))
            query = query.filter(or_(*tag_filters))
        
        if min_market_cap is not None:
            query = query.filter(Asset.market_cap >= min_market_cap)
        
        if max_volatility is not None:
            query = query.filter(Asset.volatility_30d <= max_volatility)
        
        # Apply pagination
        return query.offset(offset).limit(limit).all()
    
    def get_sectors_with_stats(self) -> List[Dict[str, Any]]:
        """
        Get list of sectors with statistics.
        
        Returns:
            List of sectors with count and average ESG score
        """
        results = self.db.query(
            Asset.sector,
            func.count(Asset.id).label('count'),
            func.avg(Asset.esg_score).label('avg_esg_score')
        ).filter(
            Asset.sector.isnot(None)
        ).group_by(
            Asset.sector
        ).all()
        
        return [
            {
                'sector': result.sector,
                'count': result.count,
                'avg_esg_score': float(result.avg_esg_score) if result.avg_esg_score else None
            }
            for result in results
        ]
    
    def get_industries_by_sector(self, sector: str) -> List[Dict[str, Any]]:
        """
        Get industries within a sector with statistics.
        
        Args:
            sector: Sector to filter by
            
        Returns:
            List of industries with count
        """
        results = self.db.query(
            Asset.industry,
            func.count(Asset.id).label('count')
        ).filter(
            Asset.sector == sector,
            Asset.industry.isnot(None)
        ).group_by(
            Asset.industry
        ).all()
        
        return [
            {
                'industry': result.industry,
                'count': result.count
            }
            for result in results
        ]
    
    def get_market_cap_distribution(self) -> List[Dict[str, Any]]:
        """
        Get distribution of assets by market cap category.
        
        Returns:
            List of market cap categories with counts
        """
        results = self.db.query(
            Asset.market_cap_category,
            func.count(Asset.id).label('count'),
            func.sum(Asset.market_cap).label('total_market_cap')
        ).filter(
            Asset.market_cap_category.isnot(None)
        ).group_by(
            Asset.market_cap_category
        ).all()
        
        return [
            {
                'category': result.market_cap_category,
                'count': result.count,
                'total_market_cap': float(result.total_market_cap) if result.total_market_cap else None
            }
            for result in results
        ]
    
    def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        """
        Get asset by symbol.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Asset or None if not found
        """
        return self.db.query(Asset).filter(
            Asset.symbol == symbol.upper()
        ).first()
    
    def get_by_id(self, asset_id: int) -> Optional[Asset]:
        """
        Get asset by ID.
        
        Args:
            asset_id: Asset ID
            
        Returns:
            Asset or None if not found
        """
        return self.db.query(Asset).filter(Asset.id == asset_id).first()
    
    def get_portfolio_theme_assets(
        self, 
        theme: str,
        limit: int = 20
    ) -> List[Asset]:
        """
        Get assets matching a portfolio theme.
        
        Args:
            theme: Portfolio theme (e.g., 'ai', 'renewable', 'healthcare')
            limit: Maximum number of assets
            
        Returns:
            List of assets matching the theme
        """
        # Theme-based filtering logic
        theme_filters = {
            'ai': ['Artificial Intelligence', 'Machine Learning', 'AI', 'Robotics'],
            'renewable': ['Solar', 'Wind', 'Clean Energy', 'Renewable'],
            'healthcare': ['Biotechnology', 'Pharmaceuticals', 'Healthcare'],
            'fintech': ['Financial Technology', 'Digital Payments', 'Blockchain'],
            'evs': ['Electric Vehicles', 'Battery', 'Charging Infrastructure']
        }
        
        tags_to_search = theme_filters.get(theme.lower(), [theme])
        
        query = self.db.query(Asset)
        
        # Search in tags and industry
        tag_conditions = []
        for tag in tags_to_search:
            tag_conditions.append(func.json_contains(Asset.tags, f'"{tag}"'))
            tag_conditions.append(Asset.industry.contains(tag))
        
        if tag_conditions:
            query = query.filter(or_(*tag_conditions))
        
        return query.limit(limit).all()
    
    def update_classification(
        self,
        asset_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Asset]:
        """
        Update asset classification data.
        
        Args:
            asset_id: Asset ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated asset or None if not found
        """
        asset = self.get_by_id(asset_id)
        if not asset:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'sector', 'industry', 'market_cap_category',
            'esg_score', 'tags', 'market_cap', 'volatility_30d'
        ]
        
        for field, value in updates.items():
            if field in allowed_fields and hasattr(asset, field):
                setattr(asset, field, value)
        
        self.db.commit()
        self.db.refresh(asset)
        return asset
    
    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags across all assets.
        
        Returns:
            List of unique tags
        """
        # This is a simplified implementation
        # In production, you might want to cache this or use a separate tags table
        assets = self.db.query(Asset.tags).filter(Asset.tags.isnot(None)).all()
        
        all_tags = set()
        for asset in assets:
            if asset.tags:
                all_tags.update(asset.tags)
        
        return sorted(list(all_tags))