"""Vault and credential models."""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Vault(BaseModel):
    """Password vault model."""

    __tablename__ = "vaults"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    color = Column(String(20), nullable=True)
    is_shared = Column(Boolean, default=False, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("user_groups.id"), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owned_vaults")
    credentials = relationship("Credential", back_populates="vault", cascade="all, delete-orphan")
    permissions = relationship("Permission", back_populates="vault", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="vault", cascade="all, delete-orphan")
    group = relationship("UserGroup", back_populates="vaults")


class Credential(BaseModel):
    """Stored credential model."""

    __tablename__ = "credentials"

    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=True)
    username = Column(String(255), nullable=True)
    encrypted_password = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    favorite = Column(Boolean, default=False, nullable=False)
    vault_id = Column(Integer, ForeignKey("vaults.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(String(50), nullable=True)

    # Relationships
    vault = relationship("Vault", back_populates="credentials")
    user = relationship("User", back_populates="credentials")
    tags = relationship("CredentialTag", back_populates="credential", cascade="all, delete-orphan")


class Tag(BaseModel):
    """Tag model for categorizing credentials."""

    __tablename__ = "tags"

    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(20), nullable=True)
    vault_id = Column(Integer, ForeignKey("vaults.id"), nullable=True)

    vault = relationship("Vault", back_populates="tags")
    credentials = relationship("CredentialTag", back_populates="tag", cascade="all, delete-orphan")


class CredentialTag(BaseModel):
    """Association table for credentials and tags."""

    __tablename__ = "credential_tags"

    credential_id = Column(Integer, ForeignKey("credentials.id", ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete='CASCADE'), primary_key=True)

    credential = relationship("Credential", back_populates="tags")
    tag = relationship("Tag", back_populates="credentials")


class UserGroup(BaseModel):
    """User group model for team collaboration."""

    __tablename__ = "user_groups"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    vaults = relationship("Vault", back_populates="group", cascade="all, delete-orphan")
    members = relationship("User", secondary="user_group_members", back_populates="groups")