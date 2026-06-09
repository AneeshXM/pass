"""Security utilities for authentication and encryption."""
import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Handles all security operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_token(data: dict, expires_delta: timedelta) -> str:
        """Generate a JWT token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and verify a JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    def create_access_token(user_id: int, roles: list[str]) -> str:
        """Create an access token."""
        data = {
            "sub": str(user_id),
            "roles": roles,
            "type": "access"
        }
        return SecurityManager.generate_token(
            data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Create a refresh token."""
        data = {
            "sub": str(user_id),
            "type": "refresh"
        }
        return SecurityManager.generate_token(
            data, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

    @staticmethod
    def verify_access_token(token: str) -> Optional[dict]:
        """Verify an access token and return payload."""
        payload = SecurityManager.decode_token(token)
        if payload and payload.get("type") == "access":
            return payload
        return None

    @staticmethod
    def verify_refresh_token(token: str) -> Optional[dict]:
        """Verify a refresh token and return payload."""
        payload = SecurityManager.decode_token(token)
        if payload and payload.get("type") == "refresh":
            return payload
        return None


class EncryptionManager:
    """Handles AES-256 encryption/decryption of passwords."""

    @staticmethod
    def get_encryption_key() -> bytes:
        """Get the encryption key from settings."""
        key = settings.ENCRYPTION_KEY
        if len(key) == 32:
            return key.encode('utf-8')
        if len(key) == 44:
            return base64.b64decode(key)
        # For development, generate a key from SECRET_KEY
        return secrets.token_bytes(32)

    @staticmethod
    def encrypt(plain_text: str) -> str:
        """Encrypt text using AES-256-CBC."""
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        key = EncryptionManager.get_encryption_key()
        iv = secrets.token_bytes(16)

        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # PKCS7 padding
        padding_length = 16 - (len(plain_text) % 16)
        padded_data = plain_text.encode() + bytes([padding_length]) * padding_length

        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        # Return IV + encrypted data, base64 encoded
        combined = iv + encrypted
        return base64.b64encode(combined).decode()

    @staticmethod
    def decrypt(encrypted_text: str) -> str:
        """Decrypt text using AES-256-CBC."""
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        key = EncryptionManager.get_encryption_key()
        combined = base64.b64decode(encrypted_text)

        iv = combined[:16]
        encrypted = combined[16:]

        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        decrypted = decryptor.update(encrypted) + decryptor.finalize()

        # Remove PKCS7 padding
        padding_length = decrypted[-1]
        return decrypted[:-padding_length].decode('utf-8')

    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new 32-byte encryption key."""
        return base64.b64encode(secrets.token_bytes(32)).decode()


security = SecurityManager()
encryption = EncryptionManager()