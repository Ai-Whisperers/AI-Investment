"""
Integration tests for authentication flow.
Tests the complete auth workflow from registration to protected endpoints.
"""

import pytest
from fastapi import status
from jose import jwt

from app.core.config import settings
from app.utils.security import verify_password
from app.models.user import User
from tests.factories import UserFactory


@pytest.mark.integration
@pytest.mark.critical
class TestAuthenticationIntegration:
    """Test complete authentication workflows."""
    
    def test_complete_registration_flow(self, client, test_db_session):
        """Test the complete user registration workflow."""
        # 1. Register new user
        user_data = {
            "email": "integration@example.com",
            "password": "SecurePassword123!"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # 2. Verify user was created in database
        user = test_db_session.query(User).filter(User.email == user_data["email"]).first()
        assert user is not None
        assert user.email == user_data["email"]
        assert verify_password(user_data["password"], user.password_hash)
        
        # 3. Verify token works for protected endpoints
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        
        assert me_response.status_code == status.HTTP_200_OK
        user_info = me_response.json()
        assert user_info["email"] == user_data["email"]
        assert user_info["id"] == user.id
    
    def test_complete_login_flow(self, client, test_user):
        """Test the complete login workflow."""
        # 1. Login with valid credentials
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        token_data = response.json()
        assert "access_token" in token_data
        
        # 2. Verify token contains correct user info
        token = token_data["access_token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == str(test_user.id)
        
        # 3. Use token to access protected endpoints
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        
        assert me_response.status_code == status.HTTP_200_OK
        user_info = me_response.json()
        assert user_info["id"] == test_user.id
        assert user_info["email"] == test_user.email
    
    def test_google_oauth_integration_new_user(self, client, test_db_session):
        """Test Google OAuth for new user."""
        google_data = {
            "email": "google_user@gmail.com",
            "google_id": "123456789",
            "name": "Google User"
        }
        
        # 1. Authenticate with Google
        response = client.post("/api/v1/auth/google", json=google_data)
        
        assert response.status_code == status.HTTP_200_OK
        token_data = response.json()
        assert "access_token" in token_data
        
        # 2. Verify user was created as Google user
        user = test_db_session.query(User).filter(User.email == google_data["email"]).first()
        assert user is not None
        assert user.is_google_user is True
        
        # 3. Verify token works
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        
        assert me_response.status_code == status.HTTP_200_OK
        user_info = me_response.json()
        assert user_info["email"] == google_data["email"]
        assert user_info["is_google_user"] is True
    
    def test_google_oauth_existing_user(self, client, test_user):
        """Test Google OAuth for existing user (account linking)."""
        google_data = {
            "email": test_user.email,
            "google_id": "987654321",
            "name": "Test User"
        }
        
        # 1. Link Google account to existing user
        response = client.post("/api/v1/auth/google", json=google_data)
        
        assert response.status_code == status.HTTP_200_OK
        token_data = response.json()
        assert "access_token" in token_data
        
        # 2. Verify user account was linked
        # Refresh user from database
        test_user.refresh()
        assert test_user.is_google_user is True
        
        # 3. Verify token works
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        
        assert me_response.status_code == status.HTTP_200_OK
    
    def test_token_refresh_flow(self, client, test_user):
        """Test token refresh workflow."""
        # 1. Login to get initial token
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        original_token = login_response.json()["access_token"]
        
        # 2. Refresh token
        headers = {"Authorization": f"Bearer {original_token}"}
        refresh_response = client.post("/api/v1/auth/refresh", headers=headers)
        
        assert refresh_response.status_code == status.HTTP_200_OK
        refresh_data = refresh_response.json()
        new_token = refresh_data["access_token"]
        
        # 3. Verify new token is different and works
        assert new_token != original_token
        
        new_headers = {"Authorization": f"Bearer {new_token}"}
        me_response = client.get("/api/v1/auth/me", headers=new_headers)
        
        assert me_response.status_code == status.HTTP_200_OK
    
    def test_logout_flow(self, client, test_user):
        """Test logout workflow."""
        # 1. Login
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Verify token works before logout
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        
        # 3. Logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == status.HTTP_200_OK
        assert "logged out" in logout_response.json()["message"].lower()
        
        # Note: In current implementation, token is not server-side invalidated
        # This test documents the current behavior
    
    def test_authentication_error_handling(self, client):
        """Test various authentication error scenarios."""
        # 1. Invalid email format
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "ValidPassword123!"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # 2. Missing password
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # 3. Weak password
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "weak"
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # 4. Wrong login credentials
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "AnyPassword123!"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # 5. Invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_concurrent_authentication_requests(self, client, test_db_session):
        """Test handling of concurrent auth requests."""
        import threading
        import time
        
        results = []
        
        def register_user(email_suffix):
            """Register a user with unique email."""
            try:
                response = client.post("/api/v1/auth/register", json={
                    "email": f"concurrent{email_suffix}@example.com",
                    "password": "ConcurrentTest123!"
                })
                results.append(response.status_code)
            except Exception as e:
                results.append(str(e))
        
        # Create multiple threads for concurrent registration
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_user, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Verify all succeeded
        assert len(results) == 5
        assert all(status == 200 for status in results)
        
        # Verify all users were created
        users = test_db_session.query(User).filter(
            User.email.like("concurrent%@example.com")
        ).all()
        assert len(users) == 5