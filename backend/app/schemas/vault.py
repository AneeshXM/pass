"""Pydantic schemas for vault and credentials."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class VaultBase(BaseModel):
    """Base vault schema."""

    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class VaultCreate(VaultBase):
    """Schema for creating a vault."""

    is_shared: bool = False
    group_id: Optional[int] = None


class VaultUpdate(BaseModel):
    """Schema for updating a vault."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_shared: Optional[bool] = None
    group_id: Optional[int] = None


class VaultResponse(VaultBase):
    """Schema for vault response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_shared: bool
    owner_id: int
    group_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class VaultListResponse(BaseModel):
    """Schema for paginated vault list."""

    items: List[VaultResponse]
    total: int
    page: int
    page_size: int


class CredentialBase(BaseModel):
    """Base credential schema."""

    name: str = Field(..., max_length=255)
    url: Optional[str] = Field(None, max_length=500)
    username: Optional[str] = None
    notes: Optional[str] = None


class CredentialCreate(CredentialBase):
    """Schema for creating a credential."""

    password: str
    vault_id: int
    expires_at: Optional[str] = None
    tag_ids: Optional[List[int]] = None


class CredentialUpdate(BaseModel):
    """Schema for updating a credential."""

    name: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = Field(None, max_length=500)
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None
    favorite: Optional[bool] = None
    expires_at: Optional[str] = None
    tag_ids: Optional[List[int]] = None


class CredentialResponse(BaseModel):
    """Schema for credential response (without password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: Optional[str] = None
    username: Optional[str] = None
    notes: Optional[str] = None
    favorite: bool
    vault_id: int
    user_id: int
    expires_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    tags: List["TagResponse"] = []


class CredentialListResponse(BaseModel):
    """Schema for paginated credential list."""

    items: List[CredentialResponse]
    total: int
    page: int
    page_size: int


class CredentialDetailResponse(CredentialResponse):
    """Schema for credential response with decrypted password."""

    password: str


class TagBase(BaseModel):
    """Base tag schema."""

    name: str = Field(..., max_length=100)
    color: Optional[str] = None


class TagCreate(TagBase):
    """Schema for creating a tag."""

    vault_id: Optional[int] = None


class TagResponse(TagBase):
    """Schema for tag response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    vault_id: Optional[int] = None
    created_at: datetime


class UserGroupBase(BaseModel):
    """Base user group schema."""

    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class UserGroupCreate(UserGroupBase):
    """Schema for creating a user group."""

    pass


class UserGroupUpdate(BaseModel):
    """Schema for updating a user group."""

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class UserGroupResponse(UserGroupBase):
    """Schema for user group response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    created_at: datetime
    member_count: Optional[int] = None


class UserGroupMemberUpdate(BaseModel):
    """Schema for updating group members."""

    user_ids: List[int]


class PermissionBase(BaseModel):
    """Base permission schema."""

    can_read: bool = True
    can_write: bool = False
    can_share: bool = False
    can_delete: bool = False


class PermissionCreate(PermissionBase):
    """Schema for creating a permission."""

    user_id: int
    vault_id: int


class PermissionUpdate(PermissionBase):
    """Schema for updating a permission."""

    pass


class PermissionResponse(PermissionBase):
    """Schema for permission response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    vault_id: int
    created_at: datetime