"""Test admin authentication for protected endpoints."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.utils.admin_auth import require_admin_token, verify_admin_websocket


class TestAdminAuth:
    """Test admin authentication functionality."""
    
    def test_require_admin_token_without_header(self):
        """Test that missing authorization header raises 401."""
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = "test_admin_token"
            
            with pytest.raises(HTTPException) as exc:
                require_admin_token(authorization=None)
            
            assert exc.value.status_code == 401
            assert "Admin authorization required" in str(exc.value.detail)
    
    def test_require_admin_token_with_invalid_format(self):
        """Test that invalid authorization format raises 401."""
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = "test_admin_token"
            
            with pytest.raises(HTTPException) as exc:
                require_admin_token(authorization="InvalidFormat")
            
            assert exc.value.status_code == 401
            assert "Invalid authorization format" in str(exc.value.detail)
    
    def test_require_admin_token_with_wrong_token(self):
        """Test that wrong token raises 403."""
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = "test_admin_token"
            
            with pytest.raises(HTTPException) as exc:
                require_admin_token(authorization="Bearer wrong_token")
            
            assert exc.value.status_code == 403
            assert "Invalid admin credentials" in str(exc.value.detail)
    
    def test_require_admin_token_with_valid_token(self):
        """Test that valid token returns True."""
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = "test_admin_token"
            
            result = require_admin_token(authorization="Bearer test_admin_token")
            assert result is True
    
    def test_require_admin_token_when_not_configured(self):
        """Test that missing ADMIN_TOKEN configuration raises 503."""
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = ""  # Not configured
            
            with pytest.raises(HTTPException) as exc:
                require_admin_token(authorization="Bearer any_token")
            
            assert exc.value.status_code == 503
            assert "Admin functionality not configured" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_verify_admin_websocket_with_valid_token(self):
        """Test WebSocket admin verification with valid token."""
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = "test_admin_token"
            
            # Test with Bearer format
            assert await verify_admin_websocket("Bearer test_admin_token") is True
            
            # Test with raw token
            assert await verify_admin_websocket("test_admin_token") is True
    
    @pytest.mark.asyncio
    async def test_verify_admin_websocket_with_invalid_token(self):
        """Test WebSocket admin verification with invalid token."""
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = "test_admin_token"
            
            assert await verify_admin_websocket("Bearer wrong_token") is False
            assert await verify_admin_websocket("wrong_token") is False
            assert await verify_admin_websocket(None) is False
    
    @pytest.mark.asyncio
    async def test_verify_admin_websocket_when_not_configured(self):
        """Test WebSocket admin verification when not configured."""
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = ""
            
            assert await verify_admin_websocket("any_token") is False


class TestWebSocketAdminEndpoints:
    """Test admin-protected WebSocket endpoints."""
    
    def test_broadcast_without_auth(self):
        """Test broadcast endpoint requires authentication."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/websocket/ws/broadcast/system",
            json={"message": "Test message", "severity": "info"}
        )
        
        # Should require authentication
        assert response.status_code in [401, 503]  # 401 if configured, 503 if not
    
    def test_broadcast_with_invalid_token(self):
        """Test broadcast endpoint rejects invalid token."""
        client = TestClient(app)
        
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = "test_admin_token"
            
            response = client.post(
                "/api/v1/websocket/ws/broadcast/system",
                json={"message": "Test message", "severity": "info"},
                headers={"Authorization": "Bearer wrong_token"}
            )
            
            assert response.status_code == 403
    
    def test_stats_without_auth(self):
        """Test stats endpoint requires authentication."""
        client = TestClient(app)
        
        response = client.get("/api/v1/websocket/ws/stats")
        
        # Should require authentication
        assert response.status_code in [401, 503]  # 401 if configured, 503 if not
    
    def test_stats_with_valid_token(self):
        """Test stats endpoint works with valid token."""
        client = TestClient(app)
        
        with patch('app.utils.admin_auth.settings') as mock_settings:
            mock_settings.ADMIN_TOKEN = "test_admin_token"
            
            with patch('app.routers.websocket.manager') as mock_manager:
                mock_manager.get_stats.return_value = {"active": 0, "rooms": {}}
                mock_manager.health_check.return_value = {"status": "healthy"}
                
                response = client.get(
                    "/api/v1/websocket/ws/stats",
                    headers={"Authorization": "Bearer test_admin_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["authenticated"] is True