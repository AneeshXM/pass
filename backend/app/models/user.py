"""User model for authentication and authorization."""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


# Association table for user groups
user_group_association = Table(
    'user_group_members',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('group_id', Integer, ForeignKey('user_groups.id', ondelete='CASCADE'), primary_key=True),
    Column('joined_at', String(50), nullable=True)
)


class Role(BaseModel):
    """Role model for RBAC."""

    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(String(500), nullable=True)

    users = relationship("User", back_populates="role")


class User(BaseModel):
    """User account model."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, default=3)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(String(50), nullable=True)

    # MFA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    mfa_recovery_codes = Column(String(1000), nullable=True)

    # Profile
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)

    # Relationships
    role = relationship("Role", back_populates="users")
    credentials = relationship("Credential", back_populates="user", cascade="all, delete-orphan")
    owned_vaults = relationship("Vault", back_populates="owner", cascade="all, delete-orphan")
    vault_permissions = relationship("Permission", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    mfa_settings = relationship("MFASettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    groups = relationship("UserGroup", secondary=user_group_association, back_populates="members")