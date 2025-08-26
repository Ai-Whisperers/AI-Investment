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
from ..repositories import IUserRepository, SQLUserRepository


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
        self.user_repo: IUserRepository = SQLUserRepository(db)
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
        if self.user_repo.exists_by_email(email):
            raise EmailAlreadyExistsError(f"Email {email} is already registered")
        
        # Hash password using domain service
        password_hash = self.auth_service.hash_password(password)
        
        # Create user in repository
        user = self.user_repo.create(email=email, password_hash=password_hash)
        
        # Generate authentication result
        result = self.auth_service.create_authentication_result(
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_admin=getattr(user, 'is_admin', False)
        )
        
        return result
    


class LoginUserUseCase:
    """Use case for user login.
    
    Orchestrates user authentication with repository access.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: Database session for repository access
        """
        self.user_repo: IUserRepository = SQLUserRepository(db)
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
        user = self.user_repo.get_by_email(email)
        
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        # Verify credentials using domain service
        is_valid = self.auth_service.verify_credentials(password, user.password)
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
    
