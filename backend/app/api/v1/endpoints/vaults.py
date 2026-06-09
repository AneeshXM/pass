"""Vault management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vault import (
    VaultCreate,
    VaultUpdate,
    VaultResponse,
    VaultListResponse,
)
from app.services.vault_service import VaultService, PermissionService, UserGroupService
from app.services.user_service import UserService
from app.api.deps import get_current_user
from app.models.user import User
from app.models.permission import Permission

router = APIRouter(prefix="/vaults", tags=["Vaults"])


@router.get("/", response_model=VaultListResponse)
async def list_vaults(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    shared_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all vaults accessible by the current user."""
    vaults, total = VaultService.get_vaults_for_user(
        db, current_user.id, skip, limit, search, shared_only
    )
    
    return VaultListResponse(
        items=[VaultResponse.model_validate(v) for v in vaults],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.post("/", response_model=VaultResponse, status_code=status.HTTP_201_CREATED)
async def create_vault(
    request: Request,
    vault_data: VaultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new vault."""
    vault = VaultService.create_vault(db, current_user.id, vault_data)
    
    UserService.log_audit(
        db, current_user.id, "vault_created", "vault", vault.id,
        ip_address=request.client.host if request.client else None
    )

    return vault


@router.get("/{vault_id}", response_model=VaultResponse)
async def get_vault(
    request: Request,
    vault_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get vault by ID."""
    vault = VaultService.get_vault_by_id(db, vault_id)
    
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault not found"
        )

    if not VaultService.check_vault_access(db, vault_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return vault


@router.put("/{vault_id}", response_model=VaultResponse)
async def update_vault(
    request: Request,
    vault_id: int,
    vault_data: VaultUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update vault."""
    vault = VaultService.get_vault_by_id(db, vault_id)
    
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault not found"
        )

    if not VaultService.check_vault_access(db, vault_id, current_user.id, require_write=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write access denied"
        )

    updated_vault = VaultService.update_vault(db, vault_id, vault_data)
    
    UserService.log_audit(
        db, current_user.id, "vault_updated", "vault", vault_id,
        ip_address=request.client.host if request.client else None
    )

    return updated_vault


@router.delete("/{vault_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vault(
    request: Request,
    vault_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete vault."""
    vault = VaultService.get_vault_by_id(db, vault_id)
    
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault not found"
        )

    # Only owner can delete
    if vault.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete vault"
        )

    VaultService.delete_vault(db, vault_id)
    
    UserService.log_audit(
        db, current_user.id, "vault_deleted", "vault", vault_id,
        ip_address=request.client.host if request.client else None
    )


@router.post("/{vault_id}/share")
async def share_vault(
    request: Request,
    vault_id: int,
    user_id: int,
    can_read: bool = True,
    can_write: bool = False,
    can_share: bool = False,
    can_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Share vault with another user."""
    vault = VaultService.get_vault_by_id(db, vault_id)
    
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault not found"
        )

    # Only owner or users with share permission can share
    if vault.owner_id != current_user.id:
        permission = PermissionService.get_permission(db, current_user.id, vault_id)
        if not permission or not permission.can_share:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Share permission denied"
            )

    permission = PermissionService.create_or_update_permission(
        db, user_id, vault_id, can_read, can_write, can_share, can_delete
    )
    
    UserService.log_audit(
        db, current_user.id, "vault_shared", "vault", vault_id,
        details=f"Shared with user {user_id}",
        ip_address=request.client.host if request.client else None
    )

    return {"message": "Vault shared successfully"}


@router.delete("/{vault_id}/share/{user_id}")
async def unshare_vault(
    request: Request,
    vault_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove vault sharing from another user."""
    vault = VaultService.get_vault_by_id(db, vault_id)
    
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault not found"
        )

    # Only owner can unshare
    if vault.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can unshare vault"
        )

    PermissionService.delete_permission(db, user_id, vault_id)
    
    UserService.log_audit(
        db, current_user.id, "vault_unshared", "vault", vault_id,
        details=f"Unshared from user {user_id}",
        ip_address=request.client.host if request.client else None
    )

    return {"message": "Vault unshared successfully"}


@router.get("/{vault_id}/permissions")
async def get_vault_permissions(
    request: Request,
    vault_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all permissions for a vault."""
    vault = VaultService.get_vault_by_id(db, vault_id)
    
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault not found"
        )

    if not VaultService.check_vault_access(db, vault_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    permissions = db.query(Permission).filter(Permission.vault_id == vault_id).all()
    return permissions