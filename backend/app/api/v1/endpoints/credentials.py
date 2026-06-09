"""Credential management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vault import (
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialListResponse,
    CredentialDetailResponse,
)
from app.services.vault_service import VaultService, CredentialService
from app.services.user_service import UserService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/credentials", tags=["Credentials"])


@router.get("/", response_model=CredentialListResponse)
async def list_credentials(
    request: Request,
    vault_id: int = Query(..., description="Vault ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    favorites_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List credentials in a vault."""
    credentials, total = CredentialService.get_credentials_for_vault(
        db, vault_id, current_user.id, skip, limit, search, favorites_only
    )
    
    return CredentialListResponse(
        items=[CredentialResponse.model_validate(c) for c in credentials],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.post("/", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    request: Request,
    credential_data: CredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new credential."""
    credential = CredentialService.create_credential(db, current_user.id, credential_data)
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or vault not found"
        )
    
    UserService.log_audit(
        db, current_user.id, "credential_created", "credential", credential.id,
        ip_address=request.client.host if request.client else None
    )

    return credential


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    request: Request,
    credential_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get credential by ID."""
    credential = CredentialService.get_credential_by_id(db, credential_id)
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

    if not VaultService.check_vault_access(db, credential.vault_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return credential


@router.get("/{credential_id}/password", response_model=CredentialDetailResponse)
async def get_credential_with_password(
    request: Request,
    credential_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get credential with decrypted password."""
    credential = CredentialService.get_credential_by_id(db, credential_id)
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

    if not VaultService.check_vault_access(db, credential.vault_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    password = CredentialService.decrypt_password(db, credential_id, current_user.id)
    
    UserService.log_audit(
        db, current_user.id, "credential_password_viewed", "credential", credential_id,
        ip_address=request.client.host if request.client else None
    )

    response = CredentialResponse.model_validate(credential)
    response.password = password
    return response


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    request: Request,
    credential_id: int,
    credential_data: CredentialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update credential."""
    credential = CredentialService.get_credential_by_id(db, credential_id)
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

    if not VaultService.check_vault_access(db, credential.vault_id, current_user.id, require_write=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write access denied"
        )

    updated_credential = CredentialService.update_credential(db, credential_id, current_user.id, credential_data)
    
    if not updated_credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update credential"
        )
    
    UserService.log_audit(
        db, current_user.id, "credential_updated", "credential", credential_id,
        ip_address=request.client.host if request.client else None
    )

    return updated_credential


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    request: Request,
    credential_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete credential."""
    credential = CredentialService.get_credential_by_id(db, credential_id)
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

    if not VaultService.check_vault_access(db, credential.vault_id, current_user.id, require_write=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write access denied"
        )

    CredentialService.delete_credential(db, credential_id, current_user.id)
    
    UserService.log_audit(
        db, current_user.id, "credential_deleted", "credential", credential_id,
        ip_address=request.client.host if request.client else None
    )


@router.post("/{credential_id}/favorite")
async def toggle_favorite(
    request: Request,
    credential_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle credential favorite status."""
    credential = CredentialService.toggle_favorite(db, credential_id, current_user.id)
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found or access denied"
        )

    return {"favorite": credential.favorite}


@router.get("/all/", response_model=CredentialListResponse)
async def list_all_credentials(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all credentials for current user across all vaults."""
    credentials, total = CredentialService.get_all_credentials_for_user(
        db, current_user.id, skip, limit, search
    )
    
    return CredentialListResponse(
        items=[CredentialResponse.model_validate(c) for c in credentials],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )