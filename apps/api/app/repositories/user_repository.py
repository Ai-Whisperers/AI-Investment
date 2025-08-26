"""SQLAlchemy implementation of the User repository."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from .interfaces import IUserRepository
from ..models.user import User

logger = logging.getLogger(__name__)


class SQLUserRepository(IUserRepository):
    """SQLAlchemy implementation of user repository."""
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User model or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User model or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, email: str, password_hash: str, is_active: bool = True) -> User:
        """Create a new user.
        
        Args:
            email: User email
            password_hash: Hashed password
            is_active: Whether user is active
            
        Returns:
            Created user model
            
        Raises:
            IntegrityError: If user with email already exists
        """
        try:
            user = User(
                email=email,
                password=password_hash,
                is_active=is_active
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user attributes.
        
        Args:
            user_id: User ID
            **kwargs: Attributes to update
            
        Returns:
            Updated user model or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Update only provided attributes
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    def delete(self, user_id: int) -> bool:
        """Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.
        
        Args:
            email: User email
            
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(User).filter(User.email == email).count() > 0