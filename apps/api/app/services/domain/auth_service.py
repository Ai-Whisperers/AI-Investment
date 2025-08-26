"""Domain service for authentication operations.

This service contains pure business logic for authentication,
following Clean Architecture principles. No HTTP or DB dependencies.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from ...core.security import get_password_hash, verify_password, create_access_token
from ...utils.password_validator import PasswordValidator


@dataclass
class UserRegistrationData:
    """Domain entity for user registration data."""
    email: str
    password: str


@dataclass
class UserCredentials:
    """Domain entity for user credentials."""
    email: str
    password: str


@dataclass
class AuthenticatedUser:
    """Domain entity for authenticated user."""
    id: int
    email: str
    is_active: bool
    is_admin: bool = False
    access_token: Optional[str] = None


@dataclass
class AuthenticationResult:
    """Domain entity for authentication result."""
    user: AuthenticatedUser
    access_token: str
    token_type: str = "bearer"


class AuthenticationService:
    """Domain service for authentication operations.
    
    This service contains pure business logic with no infrastructure dependencies.
    """
    
    def validate_registration_data(self, registration_data: UserRegistrationData) -> tuple[bool, list[str]]:
        """Validate user registration data.
        
        Args:
            registration_data: User registration data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate email format
        if not self._is_valid_email(registration_data.email):
            errors.append("Invalid email format")
        
        # Validate password strength
        is_valid, password_errors = PasswordValidator.validate(registration_data.password)
        if not is_valid:
            errors.extend(password_errors)
        
        return len(errors) == 0, errors
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storage.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return get_password_hash(password)
    
    def verify_credentials(
        self, 
        provided_password: str, 
        stored_password_hash: str
    ) -> bool:
        """Verify user credentials.
        
        Args:
            provided_password: Password provided by user
            stored_password_hash: Stored password hash
            
        Returns:
            True if credentials are valid
        """
        return verify_password(provided_password, stored_password_hash)
    
    def generate_access_token(self, user_id: int) -> str:
        """Generate access token for authenticated user.
        
        Args:
            user_id: ID of the authenticated user
            
        Returns:
            JWT access token
        """
        token_data = {"sub": str(user_id)}
        return create_access_token(token_data)
    
    def create_authentication_result(
        self,
        user_id: int,
        email: str,
        is_active: bool,
        is_admin: bool = False
    ) -> AuthenticationResult:
        """Create authentication result with token.
        
        Args:
            user_id: User ID
            email: User email
            is_active: Whether user is active
            is_admin: Whether user is admin
            
        Returns:
            Complete authentication result
        """
        # Generate token
        access_token = self.generate_access_token(user_id)
        
        # Create authenticated user
        user = AuthenticatedUser(
            id=user_id,
            email=email,
            is_active=is_active,
            is_admin=is_admin,
            access_token=access_token
        )
        
        # Create result
        return AuthenticationResult(
            user=user,
            access_token=access_token,
            token_type="bearer"
        )
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format.
        
        Private method for email validation.
        """
        # Basic email validation
        if not email or '@' not in email:
            return False
        
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        if not local or not domain:
            return False
        
        if '.' not in domain:
            return False
        
        return True