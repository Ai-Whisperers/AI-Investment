"""Portfolio schemas for API responses."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class PositionResponse(BaseModel):
    """Position in a portfolio."""
    symbol: str
    name: str
    quantity: float
    current_price: float
    total_value: float
    weight: float
    returns: float
    
    class Config:
        from_attributes = True

class PortfolioResponse(BaseModel):
    """Portfolio response schema."""
    id: int
    name: str
    description: Optional[str] = None
    total_value: float
    returns: float
    positions: List[PositionResponse] = []
    strategy_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PortfolioCreateRequest(BaseModel):
    """Request to create a portfolio."""
    name: str
    description: Optional[str] = None
    strategy_config: Optional[Dict[str, Any]] = None