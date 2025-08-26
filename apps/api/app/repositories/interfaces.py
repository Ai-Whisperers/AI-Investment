"""Repository interfaces defining data access contracts.

These interfaces follow the Dependency Inversion Principle - high-level modules
should not depend on low-level modules; both should depend on abstractions.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class IUserRepository(ABC):
    """Interface for user data access."""
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[Any]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Any]:
        """Get user by email."""
        pass
    
    @abstractmethod
    def create(self, email: str, password_hash: str, is_active: bool = True) -> Any:
        """Create a new user."""
        pass
    
    @abstractmethod
    def update(self, user_id: int, **kwargs) -> Optional[Any]:
        """Update user attributes."""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete a user."""
        pass
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        pass


class IAssetRepository(ABC):
    """Interface for asset data access."""
    
    @abstractmethod
    def get_by_id(self, asset_id: int) -> Optional[Any]:
        """Get asset by ID."""
        pass
    
    @abstractmethod
    def get_by_symbol(self, symbol: str) -> Optional[Any]:
        """Get asset by symbol."""
        pass
    
    @abstractmethod
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Any]:
        """Get all assets with optional pagination."""
        pass
    
    @abstractmethod
    def get_by_type(self, asset_type: str) -> List[Any]:
        """Get assets by type (stock, etf, commodity)."""
        pass
    
    @abstractmethod
    def create(self, symbol: str, name: str, asset_type: str, **kwargs) -> Any:
        """Create a new asset."""
        pass
    
    @abstractmethod
    def update(self, asset_id: int, **kwargs) -> Optional[Any]:
        """Update asset attributes."""
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[Any]:
        """Search assets by symbol or name."""
        pass


class IPriceRepository(ABC):
    """Interface for price data access."""
    
    @abstractmethod
    def get_latest(self, asset_id: int) -> Optional[Any]:
        """Get latest price for an asset."""
        pass
    
    @abstractmethod
    def get_history(
        self, 
        asset_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Any]:
        """Get price history for an asset with pagination support."""
        pass
    
    @abstractmethod
    def get_history_by_symbol(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Any]:
        """Get price history by asset symbol with pagination support."""
        pass
    
    @abstractmethod
    def create_batch(self, prices: List[Dict[str, Any]]) -> int:
        """Create multiple price records. Returns count of created records."""
        pass
    
    @abstractmethod
    def delete_old(self, before_date: date) -> int:
        """Delete prices older than specified date. Returns count of deleted records."""
        pass
    
    @abstractmethod
    def get_price_range(self, asset_id: int) -> Dict[str, Any]:
        """Get min, max, avg price for an asset."""
        pass


class IPortfolioRepository(ABC):
    """Interface for portfolio data access."""
    
    @abstractmethod
    def get_by_id(self, portfolio_id: int) -> Optional[Any]:
        """Get portfolio by ID."""
        pass
    
    @abstractmethod
    def get_by_user(self, user_id: int) -> List[Any]:
        """Get all portfolios for a user."""
        pass
    
    @abstractmethod
    def create(self, user_id: int, name: str, **kwargs) -> Any:
        """Create a new portfolio."""
        pass
    
    @abstractmethod
    def update(self, portfolio_id: int, **kwargs) -> Optional[Any]:
        """Update portfolio attributes."""
        pass
    
    @abstractmethod
    def delete(self, portfolio_id: int) -> bool:
        """Delete a portfolio."""
        pass
    
    @abstractmethod
    def add_asset(self, portfolio_id: int, asset_id: int, weight: float) -> bool:
        """Add an asset to portfolio with specified weight."""
        pass
    
    @abstractmethod
    def remove_asset(self, portfolio_id: int, asset_id: int) -> bool:
        """Remove an asset from portfolio."""
        pass
    
    @abstractmethod
    def get_allocations(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Get all asset allocations for a portfolio."""
        pass