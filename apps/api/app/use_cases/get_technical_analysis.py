"""Use case for getting technical analysis.

This layer orchestrates the business logic with infrastructure concerns,
following Clean Architecture principles.
"""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..services.domain.technical_analysis_service import (
    TechnicalAnalysisService,
    PriceData,
    TechnicalAnalysisResult
)
from ..repositories import IAssetRepository, IPriceRepository
from ..repositories import SQLAssetRepository, SQLPriceRepository


class AssetNotFoundError(Exception):
    """Raised when asset is not found in database."""
    pass


class InsufficientPriceDataError(Exception):
    """Raised when there's not enough price data for analysis."""
    pass


class GetTechnicalAnalysisUseCase:
    """Application use case for getting technical analysis.
    
    This use case orchestrates the domain service with repository access.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: Database session for repository access
        """
        self.asset_repo: IAssetRepository = SQLAssetRepository(db)
        self.price_repo: IPriceRepository = SQLPriceRepository(db)
        self.analysis_service = TechnicalAnalysisService()
    
    def execute(
        self,
        symbol: str,
        period: int = 100,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> TechnicalAnalysisResult:
        """Execute the use case to get technical analysis.
        
        Args:
            symbol: Asset symbol to analyze
            period: Number of days of price history to analyze
            
        Returns:
            Technical analysis result
            
        Raises:
            AssetNotFoundError: If asset doesn't exist
            InsufficientPriceDataError: If not enough price data
        """
        # Validate input
        if period < 20:
            raise ValueError("Period must be at least 20 days for technical analysis")
        
        if period > 365:
            raise ValueError("Period cannot exceed 365 days")
        
        # Get asset from repository
        asset = self.asset_repo.get_by_symbol(symbol)
        if not asset:
            raise AssetNotFoundError(f"Asset {symbol} not found")
        
        # Get price history from repository
        price_data = self._get_price_history(asset.id, period)
        
        # Perform technical analysis using domain service
        result = self.analysis_service.perform_complete_analysis(
            symbol=symbol,
            prices=price_data,
            period_days=period
        )
        
        return result
    
    
    def _get_price_history(self, asset_id: int, period: int) -> list[PriceData]:
        """Get price history from repository.
        
        Private method for repository access.
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period)
        
        prices = self.price_repo.get_history(
            asset_id=asset_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not prices:
            raise InsufficientPriceDataError(
                f"No price data available for the requested period"
            )
        
        if len(prices) < 20:
            raise InsufficientPriceDataError(
                f"Insufficient price data for technical analysis. "
                f"Found {len(prices)} data points, minimum 20 required"
            )
        
        # Convert to domain entities
        price_data = [
            PriceData(
                date=p.date,
                close=float(p.close),
                open=float(p.open) if p.open else None,
                high=float(p.high) if p.high else None,
                low=float(p.low) if p.low else None,
                volume=float(p.volume) if p.volume else None
            )
            for p in prices
        ]
        
        return price_data