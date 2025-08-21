"""
Authentication and authorization schemas.
"""

from pydantic import BaseModel, ConfigDict, EmailStr


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "SecurePassword123!"}
        }
    )


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "SecurePassword123!"}
        }
    )


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class GoogleAuthRequest(BaseModel):
    """Google OAuth authentication request."""

    email: EmailStr
    google_id: str
    name: str = ""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@gmail.com",
                "google_id": "1234567890",
                "name": "John Doe",
            }
        }
    )
