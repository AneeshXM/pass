"""Audit and admin endpoints."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.audit import (
    AuditLogListResponse,
    AuditLogResponse,
    DashboardStats,
)
from app.services.user_service import UserService
from app.api.deps import get_current_user, get_current_superuser
from app.models.user import User
from app.models.permission import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: int = Query(None),
    action: str = Query(None),
    resource_type: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """List audit logs (admin only)."""
    query = db.query(AuditLog)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/logs/me", response_model=AuditLogListResponse)
async def list_my_audit_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List current user's audit logs."""
    query = db.query(AuditLog).filter(AuditLog.user_id == current_user.id)

    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics."""
    from app.models.vault import Vault, Credential
    
    # Get user's vaults
    owned_vaults_count = db.query(Vault).filter(Vault.owner_id == current_user.id).count()
    
    # Get permitted vaults
    from app.models.permission import Permission
    permitted_vault_ids = db.query(Permission.vault_id).filter(
        Permission.user_id == current_user.id,
        Permission.can_read == True
    ).subquery()
    
    permitted_vaults_count = db.query(Vault).filter(Vault.id.in_(permitted_vault_ids)).count()
    
    total_vaults = owned_vaults_count + permitted_vaults_count
    
    # Get credentials count
    total_credentials = db.query(Credential).filter(Credential.user_id == current_user.id).count()
    
    # Get shared vaults
    shared_vaults = db.query(Vault).filter(
        Vault.owner_id == current_user.id,
        Vault.is_shared == True
    ).count()
    
    # Get favorites count
    favorites_count = db.query(Credential).filter(
        Credential.user_id == current_user.id,
        Credential.favorite == True
    ).count()
    
    # Get expiring credentials (within 30 days)
    thirty_days_from_now = (datetime.now() + timedelta(days=30)).isoformat()
    expiring_credentials = db.query(Credential).filter(
        Credential.user_id == current_user.id,
        Credential.expires_at != None,
        Credential.expires_at <= thirty_days_from_now
    ).count()
    
    # Get recent activity (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_activity = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id,
        AuditLog.created_at >= seven_days_ago
    ).count()
    
    return DashboardStats(
        total_vaults=total_vaults,
        total_credentials=total_credentials,
        shared_vaults=shared_vaults,
        expiring_credentials=expiring_credentials,
        recent_activity=recent_activity,
        favorites_count=favorites_count
    )