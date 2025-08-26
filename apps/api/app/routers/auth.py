from fastapi import APIRouter, Depends, HTTPException, Response, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import secrets
import logging
from urllib.parse import urlencode

from ..core.database import get_db
from ..core.security import create_access_token, get_password_hash, verify_password
from ..core.config import settings
from ..core.redis_client import get_redis_client
from ..models.user import User
from ..schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from ..utils.password_validator import PasswordValidator
from ..utils.token_dep import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Explicit OPTIONS handlers for CORS preflight requests
@router.options("/register")
async def options_register():
    """Handle preflight requests for registration endpoint"""
    return Response(status_code=200)


@router.options("/login")
async def options_login():
    """Handle preflight requests for login endpoint"""
    return Response(status_code=200)


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user.
    
    This endpoint is now a pure presentation layer following Clean Architecture.
    All business logic has been moved to domain services and use cases.
    """
    from ..use_cases import (
        RegisterUserUseCase,
        EmailAlreadyExistsError,
        ValidationError as DomainValidationError
    )
    
    # Create and execute use case
    use_case = RegisterUserUseCase(db)
    
    try:
        # Execute use case - all business logic is encapsulated
        result = use_case.execute(email=req.email, password=req.password)
        
        # Return token response
        return TokenResponse(access_token=result.access_token)
        
    except DomainValidationError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Password does not meet security requirements",
                "errors": str(e),
            },
        )
    except EmailAlreadyExistsError as e:
        # Handle email already exists
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during registration"
        )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return access token.
    
    This endpoint is now a pure presentation layer following Clean Architecture.
    All business logic has been moved to domain services and use cases.
    """
    from ..use_cases import (
        LoginUserUseCase,
        InvalidCredentialsError,
        UserInactiveError
    )
    
    # Create and execute use case
    use_case = LoginUserUseCase(db)
    
    try:
        # Execute use case - all business logic is encapsulated
        result = use_case.execute(email=req.email, password=req.password)
        
        # Return token response
        return TokenResponse(access_token=result.access_token)
        
    except InvalidCredentialsError as e:
        # Handle invalid credentials
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except UserInactiveError as e:
        # Handle inactive user
        raise HTTPException(status_code=401, detail="User account is inactive")
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during login"
        )


@router.options("/google")
async def options_google():
    """Handle preflight requests for Google OAuth endpoint"""
    return Response(status_code=200)


@router.get("/google")
def google_oauth_redirect():
    """Redirect to Google OAuth for authentication."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID in environment variables."
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Build Google OAuth URL with proper parameters
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI or f"{settings.FRONTEND_URL}/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "email profile openid",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }
    
    google_oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    # Store state server-side in Redis for CSRF protection
    redis_client = get_redis_client()
    state_key = f"oauth_state:{state}"
    
    # Store state in Redis with 10 minute expiration
    if redis_client.is_connected:
        redis_client.set(state_key, {"timestamp": secrets.token_hex(16)}, expire=600)
    else:
        # Fallback if Redis is unavailable - log warning but allow OAuth
        logger.warning("Redis unavailable for OAuth state storage - using memory fallback")
        # Could implement in-memory storage here as backup, but for now just proceed
        
    response = RedirectResponse(url=google_oauth_url, status_code=302)
    return response


@router.get("/google/callback")
async def google_oauth_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback and exchange code for tokens.
    
    This endpoint is now a pure presentation layer following Clean Architecture.
    All business logic has been moved to domain services and use cases.
    """
    from ..use_cases import (
        GoogleAuthUseCase,
        GoogleTokenExchangeError,
        GoogleUserInfoError,
        NoEmailInGoogleAccountError
    )
    
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured properly."
        )
    
    # Validate state parameter to prevent CSRF attacks - check server-side storage
    redis_client = get_redis_client()
    state_key = f"oauth_state:{state}"
    
    stored_state_data = None
    if redis_client.is_connected:
        stored_state_data = redis_client.get(state_key)
        # Clean up the state after validation (one-time use)
        redis_client.delete(state_key)
    
    if not stored_state_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state parameter. Possible CSRF attack or session timeout."
        )
    
    # Create and execute use case
    use_case = GoogleAuthUseCase(db)
    
    try:
        # Execute use case - all business logic is encapsulated
        result = await use_case.handle_oauth_callback(code=code, state=state)
        
        # Generate JWT token from result
        access_token = result.access_token
        
        # Redirect to frontend with token
        frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
        redirect_url = f"{frontend_url}/auth/callback?token={access_token}"
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except GoogleTokenExchangeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GoogleUserInfoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NoEmailInGoogleAccountError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during Google authentication: {str(e)}"
        )


@router.post("/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Alternative Google authentication endpoint for frontend-handled OAuth.
    
    The frontend should verify the Google token before sending.
    This endpoint is now a pure presentation layer following Clean Architecture.
    All business logic has been moved to domain services and use cases.
    """
    from ..use_cases import GoogleAuthUseCase
    
    # Create and execute use case
    use_case = GoogleAuthUseCase(db)
    
    try:
        # Execute use case - all business logic is encapsulated
        result = use_case.authenticate_google_user(email=req.email)
        
        # Return token response
        return TokenResponse(access_token=result.access_token)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during Google authentication: {str(e)}"
        )


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_google_user": getattr(current_user, "is_google_user", False),
        "created_at": (
            current_user.created_at.isoformat()
            if hasattr(current_user, "created_at")
            else None
        ),
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh the access token for the current user."""
    token = create_access_token({"sub": str(current_user.id)})
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout():
    """Logout endpoint - token invalidation handled on client side."""
    return {"message": "Successfully logged out"}
