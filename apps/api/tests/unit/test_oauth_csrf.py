"""Test OAuth CSRF protection implementation."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.redis_client import RedisClient


class TestOAuthCSRF:
    """Test OAuth CSRF protection with Redis state management."""
    
    def test_google_oauth_redirect_creates_state(self):
        """Test that OAuth redirect creates and stores state in Redis."""
        client = TestClient(app)
        
        with patch('app.routers.auth.settings') as mock_settings:
            # Mock Google OAuth settings
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_settings.GOOGLE_REDIRECT_URI = ""
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            
            with patch('app.routers.auth.get_redis_client') as mock_redis:
                # Mock Redis client
                mock_redis_instance = MagicMock(spec=RedisClient)
                mock_redis_instance.is_connected = True
                mock_redis_instance.set = MagicMock(return_value=True)
                mock_redis.return_value = mock_redis_instance
                
                # Make request to OAuth redirect endpoint
                response = client.get("/api/v1/auth/google", follow_redirects=False)
                
                # Should redirect to Google OAuth
                assert response.status_code == 302
                assert "accounts.google.com" in response.headers["location"]
                
                # Should have state parameter in URL
                assert "state=" in response.headers["location"]
                
                # Redis set should have been called to store state
                mock_redis_instance.set.assert_called_once()
                call_args = mock_redis_instance.set.call_args
                
                # Verify state key format and expiration
                assert call_args[0][0].startswith("oauth_state:")
                assert call_args[1]["expire"] == 600  # 10 minutes
    
    def test_google_oauth_callback_validates_state(self):
        """Test that OAuth callback validates state from Redis."""
        client = TestClient(app)
        
        with patch('app.routers.auth.get_redis_client') as mock_redis:
            # Mock Redis client
            mock_redis_instance = MagicMock(spec=RedisClient)
            mock_redis_instance.is_connected = True
            mock_redis_instance.get = MagicMock(return_value={"timestamp": "test123"})
            mock_redis_instance.delete = MagicMock(return_value=True)
            mock_redis.return_value = mock_redis_instance
            
            # Mock the token exchange
            with patch('app.routers.auth.httpx.AsyncClient') as mock_httpx:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "access_token": "test_token",
                    "token_type": "Bearer"
                }
                mock_client.post.return_value = mock_response
                mock_httpx.return_value.__aenter__.return_value = mock_client
                
                # Make callback request with valid state
                response = client.get(
                    "/api/v1/auth/google/callback",
                    params={"code": "test_code", "state": "valid_state"}
                )
                
                # Redis get should have been called to validate state
                mock_redis_instance.get.assert_called_once_with("oauth_state:valid_state")
                
                # Redis delete should have been called to clean up state
                mock_redis_instance.delete.assert_called_once_with("oauth_state:valid_state")
    
    def test_google_oauth_callback_rejects_invalid_state(self):
        """Test that OAuth callback rejects invalid or missing state."""
        client = TestClient(app)
        
        with patch('app.routers.auth.get_redis_client') as mock_redis:
            # Mock Redis client
            mock_redis_instance = MagicMock(spec=RedisClient)
            mock_redis_instance.is_connected = True
            mock_redis_instance.get = MagicMock(return_value=None)  # State not found
            mock_redis.return_value = mock_redis_instance
            
            # Make callback request with invalid state
            response = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "test_code", "state": "invalid_state"}
            )
            
            # Should return 400 error for invalid state
            assert response.status_code == 400
            assert "Invalid or expired state parameter" in response.json()["detail"]
    
    def test_google_oauth_callback_prevents_replay_attacks(self):
        """Test that state cannot be reused (prevents replay attacks)."""
        client = TestClient(app)
        
        with patch('app.routers.auth.get_redis_client') as mock_redis:
            # Mock Redis client
            mock_redis_instance = MagicMock(spec=RedisClient)
            mock_redis_instance.is_connected = True
            
            # First call returns state, second call returns None (already deleted)
            mock_redis_instance.get = MagicMock(side_effect=[
                {"timestamp": "test123"},  # First call - state exists
                None  # Second call - state already deleted
            ])
            mock_redis_instance.delete = MagicMock(return_value=True)
            mock_redis.return_value = mock_redis_instance
            
            # Mock the token exchange
            with patch('app.routers.auth.httpx.AsyncClient') as mock_httpx:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "access_token": "test_token",
                    "token_type": "Bearer"
                }
                mock_client.post.return_value = mock_response
                mock_httpx.return_value.__aenter__.return_value = mock_client
                
                # First request should succeed
                response1 = client.get(
                    "/api/v1/auth/google/callback",
                    params={"code": "test_code", "state": "valid_state"}
                )
                
                # Second request with same state should fail
                response2 = client.get(
                    "/api/v1/auth/google/callback",
                    params={"code": "test_code", "state": "valid_state"}
                )
                
                assert response2.status_code == 400
                assert "Invalid or expired state parameter" in response2.json()["detail"]
    
    def test_google_oauth_works_without_redis(self):
        """Test OAuth still works (with warning) when Redis is unavailable."""
        client = TestClient(app)
        
        with patch('app.routers.auth.get_redis_client') as mock_redis:
            # Mock Redis client as disconnected
            mock_redis_instance = MagicMock(spec=RedisClient)
            mock_redis_instance.is_connected = False
            mock_redis.return_value = mock_redis_instance
            
            # Should still redirect but log warning
            with patch('app.routers.auth.logger') as mock_logger:
                response = client.get("/api/v1/auth/google", follow_redirects=False)
                
                assert response.status_code == 302
                assert "accounts.google.com" in response.headers["location"]
                
                # Should log warning about Redis unavailability
                mock_logger.warning.assert_called_once()
                assert "Redis unavailable" in mock_logger.warning.call_args[0][0]