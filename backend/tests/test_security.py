"""Unit tests for security module."""
import pytest
from app.core.security import security, encryption


class TestSecurityManager:
    """Tests for SecurityManager class."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = security.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = security.hash_password(password)
        
        assert security.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = security.hash_password(password)
        
        assert security.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = 1
        roles = ["User"]
        
        token = security.create_access_token(user_id, roles)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self):
        """Test access token verification."""
        user_id = 1
        roles = ["User"]
        
        token = security.create_access_token(user_id, roles)
        payload = security.verify_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["roles"] == roles
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = 1
        
        token = security.create_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)

    def test_verify_refresh_token(self):
        """Test refresh token verification."""
        user_id = 1
        
        token = security.create_refresh_token(user_id)
        payload = security.verify_refresh_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        payload = security.decode_token("invalid_token")
        
        assert payload is None


class TestEncryptionManager:
    """Tests for EncryptionManager class."""

    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        plain_text = "MySecretPassword123!"
        
        encrypted = encryption.encrypt(plain_text)
        decrypted = encryption.decrypt(encrypted)
        
        assert encrypted != plain_text
        assert decrypted == plain_text

    def test_encrypt_produces_different_output(self):
        """Test that same text produces different encrypted output."""
        plain_text = "MySecretPassword123!"
        
        encrypted1 = encryption.encrypt(plain_text)
        encrypted2 = encryption.encrypt(plain_text)
        
        # Different IVs should produce different ciphertexts
        assert encrypted1 != encrypted2

    def test_decrypt_wrong_data(self):
        """Test decryption with invalid data."""
        with pytest.raises(Exception):
            encryption.decrypt("invalid_base64_data")