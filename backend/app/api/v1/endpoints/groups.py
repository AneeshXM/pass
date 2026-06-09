"""User group management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vault import (
    UserGroupCreate,
    UserGroupUpdate,
    UserGroupResponse,
    UserGroupMemberUpdate,
)
from app.services.vault_service import UserGroupService
from app.services.user_service import UserService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("/", response_model=list[UserGroupResponse])
async def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all groups the current user is a member of."""
    groups = UserGroupService.get_groups_for_user(db, current_user.id)
    
    # Add member count
    result = []
    for group in groups:
        group_dict = UserGroupResponse.model_validate(group).model_dump()
        group_dict["member_count"] = len(group.members)
        result.append(UserGroupResponse(**group_dict))
    
    return result


@router.post("/", response_model=UserGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    request: Request,
    group_data: UserGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user group."""
    group = UserGroupService.create_group(
        db, current_user.id, group_data.name, group_data.description
    )
    
    # Add creator as member
    UserGroupService.add_member_to_group(db, group.id, current_user.id)
    
    UserService.log_audit(
        db, current_user.id, "group_created", "group", group.id,
        ip_address=request.client.host if request.client else None
    )

    return group


@router.get("/{group_id}", response_model=UserGroupResponse)
async def get_group(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get group by ID."""
    group = UserGroupService.get_group_by_id(db, group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Check if user is member or superuser
    if current_user.id not in [m.id for m in group.members] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return group


@router.put("/{group_id}", response_model=UserGroupResponse)
async def update_group(
    request: Request,
    group_id: int,
    group_data: UserGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update group."""
    group = UserGroupService.get_group_by_id(db, group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Only creator or superuser can update
    if group.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creator can update group"
        )

    for field, value in group_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(group, field, value)

    db.commit()
    db.refresh(group)
    
    UserService.log_audit(
        db, current_user.id, "group_updated", "group", group_id,
        ip_address=request.client.host if request.client else None
    )

    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete group."""
    group = UserGroupService.get_group_by_id(db, group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Only creator or superuser can delete
    if group.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creator can delete group"
        )

    db.delete(group)
    db.commit()
    
    UserService.log_audit(
        db, current_user.id, "group_deleted", "group", group_id,
        ip_address=request.client.host if request.client else None
    )


@router.post("/{group_id}/members")
async def add_member(
    request: Request,
    group_id: int,
    member_data: UserGroupMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add members to group."""
    group = UserGroupService.get_group_by_id(db, group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Only creator or superuser can add members
    if group.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creator can add members"
        )

    for user_id in member_data.user_ids:
        UserGroupService.add_member_to_group(db, group_id, user_id)
    
    UserService.log_audit(
        db, current_user.id, "group_members_added", "group", group_id,
        details=f"Added {len(member_data.user_ids)} members",
        ip_address=request.client.host if request.client else None
    )

    return {"message": f"Added {len(member_data.user_ids)} members"}


@router.delete("/{group_id}/members")
async def remove_member(
    request: Request,
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove member from group."""
    group = UserGroupService.get_group_by_id(db, group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Only creator or superuser can remove members
    if group.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creator can remove members"
        )

    UserGroupService.remove_member_from_group(db, group_id, user_id)
    
    UserService.log_audit(
        db, current_user.id, "group_member_removed", "group", group_id,
        details=f"Removed user {user_id}",
        ip_address=request.client.host if request.client else None
    )

    return {"message": "Member removed"}