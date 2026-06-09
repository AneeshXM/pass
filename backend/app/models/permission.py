"""Permission and audit log models."""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Permission(BaseModel):
    """Permission model for vault access control."""

    __tablename__ = "permissions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vault_id = Column(Integer, ForeignKey("vaults.id"), nullable=False)
    can_read = Column(Boolean, default=True, nullable=False)
    can_write = Column(Boolean, default=False, nullable=False)
    can_share = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="vault_permissions")
    vault = relationship("Vault", back_populates="permissions")


class AuditLog(BaseModel):
    """Audit log model for tracking user actions."""

    __tablename__ = "audit_logs"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="success")

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class MFASettings(BaseModel):
    """Multi-factor authentication settings."""

    __tablename__ = "mfa_settings"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    enabled = Column(Boolean, default=False, nullable=False)
    secret = Column(String(255), nullable=True)
    backup_codes = Column(Text, nullable=True)  # JSON array of backup codes
    last_used = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="mfa_settings")


class Session(BaseModel):
    """User session model."""

    __tablename__ = "sessions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=True, index=True)
    expires_at = Column(String(50), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", backref="sessions")