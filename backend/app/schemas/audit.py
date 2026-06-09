"""Pydantic schemas for audit logging."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""

    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class MFAEnableRequest(BaseModel):
    """Schema for enabling MFA."""

    password: str


class MFAVerifyRequest(BaseModel):
    """Schema for verifying MFA code."""

    code: str


class MFAResponse(BaseModel):
    """Schema for MFA setup response."""

    secret: str
    qr_code: str
    backup_codes: List[str]


class MFADisableRequest(BaseModel):
    """Schema for disabling MFA."""

    password: str
    code: str


class BackupRequest(BaseModel):
    """Schema for backup request."""

    password: Optional[str] = None


class BackupResponse(BaseModel):
    """Schema for backup response."""

    filename: str
    size: int
    created_at: datetime


class RestoreRequest(BaseModel):
    """Schema for restore request."""

    password: Optional[str] = None


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""

    total_vaults: int
    total_credentials: int
    shared_vaults: int
    expiring_credentials: int
    recent_activity: int
    favorites_count: int