from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import secrets
from urllib.parse import urlencode

from ..core.database import get_db
from ..core.security import create_access_token, get_password_hash, verify_password
from ..core.config import settings
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
    # Validate password strength
    is_valid, errors = PasswordValidator.validate(req.password)
    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Password does not meet security requirements",
                "errors": errors,
            },
        )

    # Check if email already exists
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user with hashed password
    user = User(email=req.email, password_hash=get_password_hash(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is inactive")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


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
    
    # Store state in response for verification (in production, use session/redis)
    response = RedirectResponse(url=google_oauth_url, status_code=302)
    response.set_cookie(key="oauth_state", value=state, httponly=True, max_age=600)
    return response


@router.get("/google/callback")
async def google_oauth_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback and exchange code for tokens."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured properly."
        )
    
    # Validate state parameter to prevent CSRF attacks
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter. Possible CSRF attack."
        )
    
    # Exchange authorization code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI or f"{settings.FRONTEND_URL}/api/v1/auth/google/callback",
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:  # Add 10 second timeout
        try:
            # Exchange code for tokens
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user info from Google
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to authenticate with Google: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error during Google authentication: {str(e)}"
            )
    
    # Check if user exists
    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email found in Google account")
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user from Google account
        random_password = secrets.token_urlsafe(32)
        user = User(
            email=email,
            password_hash=get_password_hash(random_password),
            is_google_user=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not getattr(user, "is_google_user", False):
        # Link existing account with Google
        user.is_google_user = True
        db.commit()
    
    # Generate JWT token
    access_token = create_access_token({"sub": str(user.id)})
    
    # Redirect to frontend with token
    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
    redirect_url = f"{frontend_url}/auth/callback?token={access_token}"
    
    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Alternative Google authentication endpoint for frontend-handled OAuth.
    The frontend should verify the Google token before sending.
    """
    # Check if user exists
    user = db.query(User).filter(User.email == req.email).first()

    if not user:
        # Create new user from Google account
        random_password = secrets.token_urlsafe(32)

        user = User(
            email=req.email,
            password_hash=get_password_hash(random_password),
            is_google_user=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not getattr(user, "is_google_user", False):
        # Existing user but not a Google user - link the account
        user.is_google_user = True
        db.commit()

    # Generate token
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


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
