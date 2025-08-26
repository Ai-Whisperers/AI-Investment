"""Use case for Google OAuth authentication.

This layer orchestrates Google OAuth business logic with infrastructure concerns,
following Clean Architecture principles.
"""

import secrets
import httpx
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..services.domain.auth_service import AuthenticationService, AuthenticationResult
from ..repositories import IUserRepository, SQLUserRepository
from ..core.security import get_password_hash
from ..core.config import settings


class GoogleAuthError(Exception):
    """Base exception for Google authentication errors."""
    pass


class GoogleTokenExchangeError(GoogleAuthError):
    """Raised when token exchange with Google fails."""
    pass


class GoogleUserInfoError(GoogleAuthError):
    """Raised when fetching user info from Google fails."""
    pass


class NoEmailInGoogleAccountError(GoogleAuthError):
    """Raised when Google account has no email."""
    pass


class GoogleAuthUseCase:
    """Use case for Google OAuth authentication.
    
    Handles both OAuth callback flow and direct Google authentication.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: Database session for repository access
        """
        self.user_repo: IUserRepository = SQLUserRepository(db)
        self.auth_service = AuthenticationService()
    
    async def handle_oauth_callback(
        self,
        code: str,
        state: str
    ) -> AuthenticationResult:
        """Handle Google OAuth callback and authenticate user.
        
        Args:
            code: Authorization code from Google
            state: State parameter for CSRF protection
            
        Returns:
            Authentication result with token
            
        Raises:
            GoogleTokenExchangeError: If token exchange fails
            GoogleUserInfoError: If fetching user info fails
            NoEmailInGoogleAccountError: If Google account has no email
        """
        # Exchange code for tokens
        tokens = await self._exchange_code_for_tokens(code)
        
        # Get user info from Google
        userinfo = await self._fetch_user_info(tokens['access_token'])
        
        # Get or create user
        email = userinfo.get('email')
        if not email:
            raise NoEmailInGoogleAccountError("No email found in Google account")
        
        user = self._get_or_create_google_user(email)
        
        # Generate authentication result
        return self.auth_service.create_authentication_result(
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_admin=getattr(user, 'is_admin', False)
        )
    
    def authenticate_google_user(self, email: str) -> AuthenticationResult:
        """Authenticate or create user from Google account.
        
        This is for frontend-handled OAuth where the frontend
        has already verified the Google token.
        
        Args:
            email: Email from verified Google account
            
        Returns:
            Authentication result with token
        """
        user = self._get_or_create_google_user(email)
        
        # Generate authentication result
        return self.auth_service.create_authentication_result(
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_admin=getattr(user, 'is_admin', False)
        )
    
    async def _exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens.
        
        Private method for Google OAuth token exchange.
        """
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI or f"{settings.FRONTEND_URL}/api/v1/auth/google/callback",
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(token_url, data=token_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise GoogleTokenExchangeError(
                    f"Failed to exchange code for tokens: {e.response.text}"
                )
            except Exception as e:
                raise GoogleTokenExchangeError(
                    f"Error during token exchange: {str(e)}"
                )
    
    async def _fetch_user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetch user information from Google.
        
        Private method for Google user info retrieval.
        """
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise GoogleUserInfoError(
                    f"Failed to fetch user info: {e.response.text}"
                )
            except Exception as e:
                raise GoogleUserInfoError(
                    f"Error fetching user info: {str(e)}"
                )
    
    def _get_or_create_google_user(self, email: str):
        """Get existing user or create new Google user.
        
        Private method for user management.
        """
        # Check if user exists
        user = self.user_repo.get_by_email(email)
        
        if not user:
            # Create new user from Google account
            random_password = secrets.token_urlsafe(32)
            password_hash = get_password_hash(random_password)
            
            # Note: We're using password_hash field but user is Google-authenticated
            # This is a random password that won't be used for login
            user = self.user_repo.create(
                email=email,
                password_hash=password_hash,
                is_active=True
            )
            
            # Mark as Google user (would need to add this field to User model)
            # For now, we track this via the random password pattern
        
        return user