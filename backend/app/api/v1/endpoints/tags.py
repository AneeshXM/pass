"""Tag management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vault import TagCreate, TagResponse
from app.services.vault_service import TagService, VaultService
from app.services.user_service import UserService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=list[TagResponse])
async def list_tags(
    vault_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all tags for a vault."""
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

    tags = TagService.get_tags_for_vault(db, vault_id)
    return tags


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    request: Request,
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new tag."""
    if tag_data.vault_id:
        vault = VaultService.get_vault_by_id(db, tag_data.vault_id)
        
        if not vault:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vault not found"
            )

        if not VaultService.check_vault_access(db, tag_data.vault_id, current_user.id, require_write=True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Write access denied"
            )

    tag = TagService.create_tag(db, tag_data.vault_id, tag_data.name, tag_data.color)
    
    UserService.log_audit(
        db, current_user.id, "tag_created", "tag", tag.id,
        ip_address=request.client.host if request.client else None
    )

    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a tag."""
    tag = TagService.get_tag_by_id(db, tag_id)
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    if tag.vault_id:
        if not VaultService.check_vault_access(db, tag.vault_id, current_user.id, require_write=True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Write access denied"
            )

    TagService.delete_tag(db, tag_id)
    
    UserService.log_audit(
        db, current_user.id, "tag_deleted", "tag", tag_id,
        ip_address=request.client.host if request.client else None
    )