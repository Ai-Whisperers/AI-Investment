"""Asset schemas for API responses and requests."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class AssetBase(BaseModel):
    """Base asset schema."""
    symbol: str
    name: Optional[str] = None


class AssetResponse(AssetBase):
    """Basic asset response."""
    id: int
    sector: Optional[str] = None
    
    class Config:
        from_attributes = True


class AssetClassificationUpdate(BaseModel):
    """Schema for updating asset classification."""
    sector: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    market_cap_category: Optional[str] = Field(None, pattern="^(micro|small|mid|large|mega)$")
    tags: Optional[List[str]] = None
    esg_score: Optional[float] = Field(None, ge=0, le=100)
    environmental_score: Optional[float] = Field(None, ge=0, le=100)
    social_score: Optional[float] = Field(None, ge=0, le=100)
    governance_score: Optional[float] = Field(None, ge=0, le=100)
    supply_chain_dependencies: Optional[List[str]] = None
    patent_portfolio_size: Optional[int] = Field(None, ge=0)
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = Field(None, ge=0)
    market_cap: Optional[int] = Field(None, ge=0)
    volatility_30d: Optional[float] = Field(None, ge=0)
    volatility_90d: Optional[float] = Field(None, ge=0)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Ensure tags are lowercase and unique."""
        if v:
            return list(set(tag.lower() for tag in v))
        return v


class AssetWithClassification(AssetResponse):
    """Asset with full classification details."""
    industry: Optional[str] = None
    market_cap_category: Optional[str] = None
    tags: Optional[List[str]] = []
    esg_score: Optional[float] = None
    environmental_score: Optional[float] = None
    social_score: Optional[float] = None
    governance_score: Optional[float] = None
    supply_chain_dependencies: Optional[List[str]] = []
    patent_portfolio_size: Optional[int] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    market_cap: Optional[int] = None
    volatility_30d: Optional[float] = None
    volatility_90d: Optional[float] = None
    
    class Config:
        from_attributes = True


class AssetFilterParams(BaseModel):
    """Parameters for filtering assets."""
    sectors: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    market_cap_categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    min_esg_score: Optional[float] = Field(None, ge=0, le=100)
    max_esg_score: Optional[float] = Field(None, ge=0, le=100)
    min_market_cap: Optional[int] = Field(None, ge=0)
    max_market_cap: Optional[int] = Field(None, ge=0)
    min_volatility: Optional[float] = Field(None, ge=0)
    max_volatility: Optional[float] = Field(None, ge=0)
    min_dividend_yield: Optional[float] = Field(None, ge=0)
    has_esg_data: Optional[bool] = None
    has_patents: Optional[bool] = None
    
    @validator('market_cap_categories')
    def validate_categories(cls, v):
        """Validate market cap categories."""
        valid = {'micro', 'small', 'mid', 'large', 'mega'}
        if v:
            invalid = set(v) - valid
            if invalid:
                raise ValueError(f"Invalid categories: {invalid}")
        return v


class SectorAnalysis(BaseModel):
    """Sector analysis response."""
    sector: str
    asset_count: int
    avg_esg_score: Optional[float] = None
    avg_pe_ratio: Optional[float] = None
    avg_dividend_yield: Optional[float] = None
    top_performers: List[str] = []
    
    class Config:
        from_attributes = True


class SupplyChainAnalysis(BaseModel):
    """Supply chain analysis for an asset."""
    symbol: str
    dependencies: List[str]
    dependent_assets: List[str]
    risk_level: str  # low, medium, high
    concentration_risk: Optional[float] = None
    
    class Config:
        from_attributes = True


class AssetScreenerResult(BaseModel):
    """Result from asset screening."""
    assets: List[AssetWithClassification]
    total_count: int
    filters_applied: Dict[str, Any]
    
    class Config:
        from_attributes = True