"""Asset classification and filtering endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..core.database import get_db
from ..models import Asset, User
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
    query = db.query(Asset)
    
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
    assets = query.offset(offset).limit(limit).all()
    
    return assets


@router.get("/sectors", response_model=List[Dict[str, Any]])
def get_sectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of available sectors with asset counts."""
    sectors = db.query(
        Asset.sector,
        func.count(Asset.id).label('count'),
        func.avg(Asset.esg_score).label('avg_esg_score')
    ).filter(
        Asset.sector.isnot(None)
    ).group_by(Asset.sector).all()
    
    return [
        {
            "sector": s.sector,
            "asset_count": s.count,
            "avg_esg_score": round(s.avg_esg_score, 2) if s.avg_esg_score else None
        }
        for s in sectors
    ]


@router.get("/industries", response_model=List[Dict[str, Any]])
def get_industries(
    sector: Optional[str] = Query(None, description="Filter industries by sector"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of available industries with asset counts."""
    query = db.query(
        Asset.industry,
        Asset.sector,
        func.count(Asset.id).label('count')
    ).filter(Asset.industry.isnot(None))
    
    if sector:
        query = query.filter(Asset.sector == sector)
    
    industries = query.group_by(Asset.industry, Asset.sector).all()
    
    return [
        {
            "industry": i.industry,
            "sector": i.sector,
            "asset_count": i.count
        }
        for i in industries
    ]


@router.get("/tags", response_model=List[str])
def get_available_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all unique tags across assets."""
    # This would require a more complex query to extract unique tags from JSON
    # For now, return predefined tags
    return [
        "ai", "renewable", "biotech", "fintech", "blockchain",
        "cloud", "semiconductor", "electric_vehicle", "gaming",
        "healthcare", "cybersecurity", "5g", "quantum_computing",
        "automation", "metaverse", "sustainable", "dividend_aristocrat"
    ]


@router.get("/{symbol}", response_model=AssetWithClassification)
def get_asset_details(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific asset."""
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    return asset


@router.put("/{symbol}/classification", response_model=AssetWithClassification)
def update_asset_classification(
    symbol: str,
    classification: AssetClassificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update classification information for an asset (admin only)."""
    # In production, add admin check here
    
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    # Update fields if provided
    update_data = classification.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    db.commit()
    db.refresh(asset)
    
    return asset


@router.get("/screener/esg", response_model=List[AssetWithClassification])
def screen_esg_assets(
    min_score: float = Query(70, ge=0, le=100, description="Minimum ESG score"),
    sectors: Optional[List[str]] = Query(None, description="Sectors to include"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Screen for high ESG score assets."""
    query = db.query(Asset).filter(
        Asset.esg_score >= min_score
    )
    
    if sectors:
        query = query.filter(Asset.sector.in_(sectors))
    
    assets = query.order_by(Asset.esg_score.desc()).limit(limit).all()
    
    return assets


@router.get("/screener/low-volatility", response_model=List[AssetWithClassification])
def screen_low_volatility(
    max_volatility: float = Query(0.2, description="Maximum 30-day volatility"),
    min_market_cap: Optional[int] = Query(None, description="Minimum market cap"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Screen for low volatility assets."""
    query = db.query(Asset).filter(
        Asset.volatility_30d <= max_volatility
    )
    
    if min_market_cap:
        query = query.filter(Asset.market_cap >= min_market_cap)
    
    assets = query.order_by(Asset.volatility_30d.asc()).limit(limit).all()
    
    return assets


@router.get("/screener/dividend", response_model=List[AssetWithClassification])
def screen_dividend_stocks(
    min_yield: float = Query(2.0, description="Minimum dividend yield %"),
    sectors: Optional[List[str]] = Query(None, description="Sectors to include"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Screen for high dividend yield stocks."""
    query = db.query(Asset).filter(
        Asset.dividend_yield >= min_yield
    )
    
    if sectors:
        query = query.filter(Asset.sector.in_(sectors))
    
    assets = query.order_by(Asset.dividend_yield.desc()).limit(limit).all()
    
    return assets


@router.get("/supply-chain/{symbol}", response_model=Dict[str, Any])
def get_supply_chain_analysis(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get supply chain dependencies and risk analysis for an asset."""
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    # Analyze supply chain dependencies
    dependencies = asset.supply_chain_dependencies or []
    
    # Find other assets with similar dependencies
    related_assets = []
    if dependencies:
        for dep in dependencies:
            related = db.query(Asset).filter(
                func.json_contains(Asset.supply_chain_dependencies, f'"{dep}"')
            ).filter(Asset.id != asset.id).limit(5).all()
            related_assets.extend([a.symbol for a in related])
    
    return {
        "symbol": asset.symbol,
        "dependencies": dependencies,
        "related_assets": list(set(related_assets)),
        "risk_level": "high" if len(dependencies) > 5 else "medium" if len(dependencies) > 2 else "low"
    }


@router.post("/bulk-classify")
def bulk_classify_assets(
    classifications: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update classification for multiple assets (admin only)."""
    # In production, add admin check here
    
    updated = 0
    errors = []
    
    for item in classifications:
        symbol = item.get("symbol")
        if not symbol:
            errors.append({"error": "Missing symbol in classification"})
            continue
        
        asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        if not asset:
            errors.append({"symbol": symbol, "error": "Asset not found"})
            continue
        
        # Update fields
        for field, value in item.items():
            if field != "symbol" and hasattr(asset, field):
                setattr(asset, field, value)
        
        updated += 1
    
    db.commit()
    
    return {
        "updated": updated,
        "errors": errors,
        "success": len(errors) == 0
    }