from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    GoogleAuthRequest,
)
from ..core.security import get_password_hash, verify_password, create_access_token
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
    # In a real implementation, this would build the Google OAuth URL
    # with client_id, redirect_uri, scope, etc.
    google_oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?client_id=YOUR_CLIENT_ID"
        "&redirect_uri=YOUR_REDIRECT_URI"
        "&response_type=code"
        "&scope=email%20profile"
    )
    return Response(status_code=307, headers={"Location": google_oauth_url})


@router.post("/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate or register user via Google OAuth.
    The frontend should verify the Google token before sending.
    """
    # Check if user exists
    user = db.query(User).filter(User.email == req.email).first()

    if not user:
        # Create new user from Google account
        # Google users don't have a password, so we generate a random one
        import secrets

        random_password = secrets.token_urlsafe(32)

        user = User(
            email=req.email,
            password_hash=get_password_hash(random_password),
            is_google_user=True,  # Mark as Google user
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
