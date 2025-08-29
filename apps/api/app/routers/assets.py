"""
Asset classification and filtering endpoints.
Refactored to use repository pattern - no direct database access.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import User
from ..repositories.asset_repository_enhanced import EnhancedAssetRepository
from ..utils.token_dep import get_current_user
from ..schemas.asset import (
    AssetResponse,
    AssetClassificationUpdate,
    AssetFilterParams,
    AssetWithClassification
)

router = APIRouter()


@router.get("/", response_model=List[AssetWithClassification])
def get_assets(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    market_cap_category: Optional[str] = Query(None, description="Filter by market cap category"),
    min_esg_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum ESG score"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    min_market_cap: Optional[int] = Query(None, description="Minimum market cap"),
    max_volatility: Optional[float] = Query(None, description="Maximum 30-day volatility"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assets with advanced filtering capabilities."""
    # Use repository instead of direct DB access
    repo = EnhancedAssetRepository(db)
    
    assets = repo.get_filtered_assets(
        sector=sector,
        industry=industry,
        market_cap_category=market_cap_category,
        min_esg_score=min_esg_score,
        tags=tags,
        min_market_cap=min_market_cap,
        max_volatility=max_volatility,
        limit=limit,
        offset=offset
    )
    
    return assets


@router.get("/sectors", response_model=List[Dict[str, Any]])
def get_sectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of available sectors with asset counts."""
    # Use repository for data access
    repo = EnhancedAssetRepository(db)
    return repo.get_sectors_with_stats()


@router.get("/industries/{sector}", response_model=List[Dict[str, Any]])
def get_industries_by_sector(
    sector: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get industries within a specific sector."""
    # Use repository for data access
    repo = EnhancedAssetRepository(db)
    industries = repo.get_industries_by_sector(sector)
    
    if not industries:
        raise HTTPException(
            status_code=404,
            detail=f"No industries found for sector: {sector}"
        )
    
    return industries


@router.get("/market-cap-distribution", response_model=List[Dict[str, Any]])
def get_market_cap_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get distribution of assets by market cap category."""
    # Use repository for data access
    repo = EnhancedAssetRepository(db)
    return repo.get_market_cap_distribution()


@router.get("/portfolio-themes/{theme}")
def get_portfolio_theme(
    theme: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assets matching a specific portfolio theme."""
    # Use repository for data access
    repo = EnhancedAssetRepository(db)
    assets = repo.get_portfolio_theme_assets(theme, limit)
    
    if not assets:
        raise HTTPException(
            status_code=404,
            detail=f"No assets found for theme: {theme}"
        )
    
    return {
        "theme": theme,
        "count": len(assets),
        "assets": [
            {
                "symbol": asset.symbol,
                "name": asset.name,
                "sector": asset.sector,
                "industry": asset.industry,
                "market_cap": asset.market_cap,
                "esg_score": asset.esg_score,
                "tags": asset.tags
            }
            for asset in assets
        ]
    }


@router.get("/tags", response_model=List[str])
def get_all_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all unique tags across all assets."""
    # Use repository for data access
    repo = EnhancedAssetRepository(db)
    return repo.get_all_tags()


@router.get("/{symbol}", response_model=AssetWithClassification)
def get_asset_by_symbol(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information for a specific asset."""
    # Use repository for data access
    repo = EnhancedAssetRepository(db)
    asset = repo.get_by_symbol(symbol)
    
    if not asset:
        raise HTTPException(
            status_code=404,
            detail=f"Asset not found: {symbol}"
        )
    
    return asset


@router.put("/{asset_id}/classification")
def update_asset_classification(
    asset_id: int,
    classification: AssetClassificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update classification data for an asset."""
    # Use repository for data access
    repo = EnhancedAssetRepository(db)
    
    # Convert classification to dict for repository
    updates = classification.dict(exclude_unset=True)
    
    asset = repo.update_classification(asset_id, updates)
    
    if not asset:
        raise HTTPException(
            status_code=404,
            detail=f"Asset not found: {asset_id}"
        )
    
    return {
        "message": "Asset classification updated successfully",
        "asset": {
            "id": asset.id,
            "symbol": asset.symbol,
            "name": asset.name,
            "sector": asset.sector,
            "industry": asset.industry,
            "market_cap_category": asset.market_cap_category,
            "esg_score": asset.esg_score,
            "tags": asset.tags
        }
    }


@router.post("/filter/advanced", response_model=List[AssetWithClassification])
def filter_assets_advanced(
    filters: AssetFilterParams,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advanced asset filtering with multiple criteria."""
    # Use repository for data access
    repo = EnhancedAssetRepository(db)
    
    # Extract filter parameters from the request model
    assets = repo.get_filtered_assets(
        sector=filters.sector,
        industry=filters.industry,
        market_cap_category=filters.market_cap_category,
        min_esg_score=filters.min_esg_score,
        tags=filters.tags,
        min_market_cap=filters.min_market_cap,
        max_volatility=filters.max_volatility,
        limit=filters.limit or 100,
        offset=filters.offset or 0
    )
    
    return assets