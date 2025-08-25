import os
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user_optional(
    token: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Optional authentication - returns None if no token provided, useful for backward compatibility"""
    if not token:
        # Check if auth should be enforced
        if os.getenv("REQUIRE_AUTH", "false").lower() == "true":
            raise HTTPException(status_code=401, detail="Authentication required")
        return None

    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except (JWTError, AttributeError):
        return None


def require_admin(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> bool:
    """Require admin token for admin endpoints"""
    if not token:
        raise HTTPException(status_code=401, detail="Admin token required")

    # Use constant-time comparison to prevent timing attacks
    if secrets.compare_digest(token.credentials, settings.ADMIN_TOKEN):
        return True

    # Otherwise, check if it's a valid user token with admin privileges
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        is_admin = payload.get("is_admin", False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        return True
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
