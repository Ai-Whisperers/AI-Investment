"""
User factory for test data generation.
Single responsibility: Create user-related test data.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .base import BaseFactory


class UserFactory(BaseFactory):
    """Factory for creating user test data."""
    
    @staticmethod
    def create_user_data(
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_google_user: bool = False
    ) -> Dict[str, Any]:
        """Create user data for testing."""
        return {
            "email": email or UserFactory.random_email(),
            "password": password or "TestPassword123!",
            "is_google_user": is_google_user
        }
    
    @staticmethod
    def create_login_data(
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create login credentials for testing."""
        return {
            "username": email or UserFactory.random_email(),
            "password": password or "TestPassword123!"
        }
    
    @staticmethod
    def create_token_data(user_id: int = 1) -> Dict[str, Any]:
        """Create JWT token payload for testing."""
        return {
            "sub": str(user_id),
            "exp": datetime.utcnow().timestamp() + 3600
        }