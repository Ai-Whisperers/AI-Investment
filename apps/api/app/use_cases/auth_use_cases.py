"""Use cases for authentication operations.

This layer orchestrates the authentication business logic with infrastructure concerns,
following Clean Architecture principles.
"""

from sqlalchemy.orm import Session

from ..services.domain.auth_service import (
    AuthenticationService,
    UserRegistrationData,
    UserCredentials,
    AuthenticationResult
)
from ..models import User


class EmailAlreadyExistsError(Exception):
    """Raised when email is already registered."""
    pass


class InvalidCredentialsError(Exception):
    """Raised when credentials are invalid."""
    pass


class UserInactiveError(Exception):
    """Raised when user account is inactive."""
    pass


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class RegisterUserUseCase:
    """Use case for user registration.
    
    Orchestrates user registration with repository access.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: Database session for repository access
        """
        self.db = db
        self.auth_service = AuthenticationService()
    
    def execute(self, email: str, password: str) -> AuthenticationResult:
        """Execute user registration use case.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Authentication result with token
            
        Raises:
            ValidationError: If registration data is invalid
            EmailAlreadyExistsError: If email is already registered
        """
        # Create registration data
        registration_data = UserRegistrationData(email=email, password=password)
        
        # Validate registration data using domain service
        is_valid, errors = self.auth_service.validate_registration_data(registration_data)
        if not is_valid:
            raise ValidationError(f"Registration validation failed: {'; '.join(errors)}")
        
        # Check if email already exists
        if self._email_exists(email):
            raise EmailAlreadyExistsError(f"Email {email} is already registered")
        
        # Hash password using domain service
        password_hash = self.auth_service.hash_password(password)
        
        # Create user in repository
        user = self._create_user(email, password_hash)
        
        # Generate authentication result
        result = self.auth_service.create_authentication_result(
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_admin=getattr(user, 'is_admin', False)
        )
        
        return result
    
    def _email_exists(self, email: str) -> bool:
        """Check if email already exists in repository.
        
        Private method for repository access.
        """
        existing = self.db.query(User).filter(User.email == email).first()
        return existing is not None
    
    def _create_user(self, email: str, password_hash: str) -> User:
        """Create user in repository.
        
        Private method for repository access.
        """
        user = User(email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class LoginUserUseCase:
    """Use case for user login.
    
    Orchestrates user authentication with repository access.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: Database session for repository access
        """
        self.db = db
        self.auth_service = AuthenticationService()
    
    def execute(self, email: str, password: str) -> AuthenticationResult:
        """Execute user login use case.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Authentication result with token
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserInactiveError: If user account is inactive
        """
        # Get user from repository
        user = self._get_user_by_email(email)
        
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        # Verify credentials using domain service
        is_valid = self.auth_service.verify_credentials(password, user.password_hash)
        if not is_valid:
            raise InvalidCredentialsError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise UserInactiveError("User account is inactive")
        
        # Generate authentication result
        result = self.auth_service.create_authentication_result(
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_admin=getattr(user, 'is_admin', False)
        )
        
        return result
    
    def _get_user_by_email(self, email: str) -> User:
        """Get user by email from repository.
        
        Private method for repository access.
        """
        return self.db.query(User).filter(User.email == email).first()