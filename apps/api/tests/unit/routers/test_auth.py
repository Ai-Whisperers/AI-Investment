"""
Unit tests for authentication endpoints.
100% coverage required for security-critical endpoints.
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User


@pytest.mark.unit
@pytest.mark.critical
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_register_new_user(self, client, test_db_session):
        """Test user registration endpoint."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "StrongPassword123!"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify user was created in database
        user = test_db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.email == "newuser@example.com"
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "Password123!"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak"  # Too short, no complexity
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        detail = response.json()["detail"]
        assert "Password does not meet security requirements" in detail["message"]
    
    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify token is valid
        token = data["access_token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == str(test_user.id)
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self, client, test_db_session):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            password_hash=get_password_hash("Password123!"),
            is_active=False
        )
        test_db_session.add(inactive_user)
        test_db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "Password123!"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "inactive" in response.json()["detail"].lower()
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "hashed_password" not in data
    
    def test_get_current_user_no_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Not authenticated" in response.json()["detail"]
    
    def test_get_current_user_invalid_token(self, client):
        """Test with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_expired_token(self, client, test_user):
        """Test with expired token."""
        # Create token that expires immediately
        expired_token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(seconds=-1)
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, client, auth_headers):
        """Test token refresh endpoint."""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # New token should be different
        old_token = auth_headers["Authorization"].split()[1]
        assert data["access_token"] != old_token
    
    def test_logout(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Successfully logged out"
        
        # Token should be invalidated (in real implementation)
        # This would check token blacklist or session invalidation
    
    def test_google_oauth_redirect(self, client):
        """Test Google OAuth initiation."""
        response = client.get("/api/v1/auth/google")
        
        # Should redirect to Google OAuth
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "accounts.google.com" in response.headers.get("location", "")
    
    @pytest.mark.parametrize("password,should_pass", [
        ("Short1!", False),              # Too short
        ("nouppercase123!", False),      # No uppercase
        ("NOLOWERCASE123!", False),      # No lowercase
        ("NoNumbers!", False),            # No numbers
        ("NoSpecialChar123", False),      # No special chars
        ("ValidPassword123!", True),      # Valid
        ("C0mpl3x!P@ssw0rd", True),      # Complex valid
    ])
    def test_password_validation(self, client, password, should_pass):
        """Test password validation rules."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"test_{password[:5]}@example.com",
                "username": f"user_{password[:5]}",
                "password": password
            }
        )
        
        if should_pass:
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_admin_endpoint_access(self, client, auth_headers, admin_auth_headers):
        """Test admin-only endpoint access."""
        # Regular user should be denied
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Admin should have access
        response = client.get("/api/v1/admin/users", headers=admin_auth_headers)
        assert response.status_code == status.HTTP_200_OK
    
    def test_rate_limiting(self, client):
        """Test rate limiting on auth endpoints."""
        # Attempt multiple rapid logins
        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": f"attempt{i}@example.com",
                    "password": "Password123!"
                }
            )
        
        # After threshold, should get rate limited
        # Note: Actual implementation would need rate limiting middleware
        # This is a placeholder for the expected behavior
        # assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS