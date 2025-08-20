"""
Unit tests for security utilities.
100% coverage required for security-critical functions.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)
from app.core.config import settings


@pytest.mark.unit
@pytest.mark.critical
class TestSecurityUtils:
    """Test security utility functions."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        # Test basic hashing
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Hash should not be the same as password
        assert hashed != password
        
        # Hash should be verifiable
        assert verify_password(password, hashed) is True
        
        # Wrong password should fail
        assert verify_password("WrongPassword", hashed) is False
    
    def test_password_hashing_edge_cases(self):
        """Test password hashing with edge cases."""
        # Empty password
        empty_hash = get_password_hash("")
        assert verify_password("", empty_hash) is True
        assert verify_password("nonempty", empty_hash) is False
        
        # Very long password
        long_password = "a" * 1000
        long_hash = get_password_hash(long_password)
        assert verify_password(long_password, long_hash) is True
        
        # Special characters
        special_password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        special_hash = get_password_hash(special_password)
        assert verify_password(special_password, special_hash) is True
        
        # Unicode characters
        unicode_password = "пароль123!测试"
        unicode_hash = get_password_hash(unicode_password)
        assert verify_password(unicode_password, unicode_hash) is True
    
    def test_password_hash_uniqueness(self):
        """Test that same password generates different hashes."""
        password = "SamePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_access_token_creation(self):
        """Test JWT access token creation."""
        user_id = "123"
        token = create_access_token(user_id)
        
        # Should be a string
        assert isinstance(token, str)
        
        # Should be decodable
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_access_token_with_custom_expiry(self):
        """Test token creation with custom expiry."""
        user_id = "456"
        custom_delta = timedelta(hours=1)
        token = create_access_token(user_id, expires_delta=custom_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # Check expiry is approximately 1 hour from now
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + custom_delta
        actual_exp = datetime.fromtimestamp(exp_timestamp)
        
        # Allow 1 minute tolerance
        assert abs((actual_exp - expected_exp).total_seconds()) < 60
    
    def test_access_token_decoding(self):
        """Test access token decoding utility."""
        user_id = "789"
        token = create_access_token(user_id)
        
        # Should decode successfully
        decoded_user_id = decode_access_token(token)
        assert decoded_user_id == user_id
    
    def test_invalid_token_decoding(self):
        """Test decoding of invalid tokens."""
        # Invalid token
        assert decode_access_token("invalid_token") is None
        
        # Expired token
        expired_token = create_access_token("user", timedelta(seconds=-1))
        assert decode_access_token(expired_token) is None
        
        # Token with wrong secret
        wrong_secret_token = jwt.encode(
            {"sub": "user", "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong_secret",
            algorithm="HS256"
        )
        assert decode_access_token(wrong_secret_token) is None
        
        # Malformed token
        assert decode_access_token("not.a.jwt") is None
    
    def test_token_payload_structure(self):
        """Test JWT token payload structure."""
        user_id = "test_user_123"
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # Required fields
        assert "sub" in payload  # Subject (user ID)
        assert "exp" in payload  # Expiration
        assert "iat" in payload  # Issued at
        
        # Values
        assert payload["sub"] == user_id
        assert isinstance(payload["exp"], int)
        assert isinstance(payload["iat"], int)
        
        # Expiration should be in the future
        assert payload["exp"] > payload["iat"]
    
    def test_token_algorithm_security(self):
        """Test that tokens use secure algorithms."""
        user_id = "security_test"
        token = create_access_token(user_id)
        
        # Should not decode with none algorithm (security vulnerability)
        with pytest.raises(JWTError):
            jwt.decode(token, None, algorithms=["none"])
        
        # Should not decode with different algorithm
        with pytest.raises(JWTError):
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS512"])
        
        # Should decode correctly with proper algorithm
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == user_id
    
    def test_password_timing_attack_resistance(self):
        """Test that password verification is resistant to timing attacks."""
        import time
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Time verification of correct password
        start_time = time.time()
        result1 = verify_password(password, hashed)
        time1 = time.time() - start_time
        
        # Time verification of incorrect password
        start_time = time.time()
        result2 = verify_password("WrongPassword123!", hashed)
        time2 = time.time() - start_time
        
        assert result1 is True
        assert result2 is False
        
        # Times should be relatively close (within order of magnitude)
        # This is a basic check - proper timing attack testing requires more sophisticated tools
        ratio = max(time1, time2) / min(time1, time2)
        assert ratio < 10  # Allow up to 10x difference
    
    @pytest.mark.parametrize("user_id", [
        "1",
        "999999",
        "user_with_underscores",
        "user-with-hyphens",
        "UserWithCamelCase",
        "123e4567-e89b-12d3-a456-426614174000",  # UUID format
    ])
    def test_token_with_various_user_ids(self, user_id):
        """Test token creation with various user ID formats."""
        token = create_access_token(user_id)
        decoded_id = decode_access_token(token)
        assert decoded_id == user_id
    
    def test_concurrent_token_operations(self):
        """Test concurrent token creation and verification."""
        import threading
        import concurrent.futures
        
        def create_and_verify_token(user_id):
            """Create and verify a token."""
            token = create_access_token(f"user_{user_id}")
            decoded = decode_access_token(token)
            return decoded == f"user_{user_id}"
        
        # Test with thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_verify_token, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All operations should succeed
        assert all(results)
        assert len(results) == 50