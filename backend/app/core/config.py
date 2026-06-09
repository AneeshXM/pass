"""Application configuration."""
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Password Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Domain
    DOMAIN: str = "localhost"
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production", max_length=64)
    ENCRYPTION_KEY: str = Field(default="", max_length=44)  # Base64 encoded 32 bytes
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_TIMEOUT_MINUTES: int = 60
    BCRYPT_ROUNDS: int = 12

    # Rate Limiting
    LOGIN_RATE_LIMIT: int = 5  # per minute
    LOGIN_LOCKOUT_MINUTES: int = 15
    API_RATE_LIMIT: int = 100  # per minute

    # Database
    DATABASE_URL: str = "postgresql://vault_user:password@db:5432/vault"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost", "http://localhost:3000"]

    # Backup
    BACKUP_DIR: str = "/backups"
    MAX_BACKUPS: int = 30

    @property
    def get_database_url(self) -> str:
        """Get database URL."""
        return self.DATABASE_URL

    def get_encryption_key_bytes(self) -> bytes:
        """Get encryption key as bytes."""
        import base64
        if len(self.ENCRYPTION_KEY) == 32:
            return self.ENCRYPTION_KEY.encode()
        return base64.b64decode(self.ENCRYPTION_KEY)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()