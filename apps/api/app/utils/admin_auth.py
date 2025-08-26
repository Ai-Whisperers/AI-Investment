"""Admin authentication utilities for secure admin endpoints."""

from fastapi import HTTPException, Header, status
from typing import Optional
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


def require_admin_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify admin token for protected endpoints.
    
    Args:
        authorization: Authorization header value (format: "Bearer <token>")
        
    Returns:
        True if authorized
        
    Raises:
        HTTPException: If unauthorized
    """
    if not settings.ADMIN_TOKEN:
        logger.warning("Admin token not configured - admin endpoints are unprotected!")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin functionality not configured. Please set ADMIN_TOKEN environment variable."
        )
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    if token != settings.ADMIN_TOKEN:
        logger.warning(f"Invalid admin token attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials"
        )
    
    return True


async def verify_admin_websocket(authorization: Optional[str]) -> bool:
    """Verify admin token for WebSocket connections.
    
    Args:
        authorization: Authorization header or query param value
        
    Returns:
        True if authorized, False otherwise
    """
    if not settings.ADMIN_TOKEN:
        logger.warning("Admin token not configured - WebSocket admin endpoints unprotected!")
        return False
    
    if not authorization:
        return False
    
    # Handle both "Bearer <token>" format and raw token
    if authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    else:
        token = authorization
    
    return token == settings.ADMIN_TOKEN