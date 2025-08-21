"""Portfolio schemas for API responses."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


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
    description: str | None = None
    total_value: float
    returns: float
    positions: list[PositionResponse] = []
    strategy_config: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PortfolioCreateRequest(BaseModel):
    """Request to create a portfolio."""
    name: str
    description: str | None = None
    strategy_config: dict[str, Any] | None = None
