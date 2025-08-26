"""Repository layer for data access abstraction.

Following the repository pattern to separate business logic from data access,
implementing Clean Architecture principles.
"""

from .interfaces import (
    IUserRepository,
    IAssetRepository,
    IPriceRepository,
    IPortfolioRepository
)
from .user_repository import SQLUserRepository
from .asset_repository import SQLAssetRepository
from .price_repository import SQLPriceRepository
from .portfolio_repository import SQLPortfolioRepository

__all__ = [
    # Interfaces
    'IUserRepository',
    'IAssetRepository',
    'IPriceRepository',
    'IPortfolioRepository',
    # Implementations
    'SQLUserRepository',
    'SQLAssetRepository', 
    'SQLPriceRepository',
    'SQLPortfolioRepository'
]