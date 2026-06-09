"""User management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserPasswordUpdate,
    RoleResponse,
)
from app.services.user_service import UserService
from app.api.deps import get_current_user, get_current_superuser
from app.models.user import User, Role

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    role_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """List all users (admin only)."""
    users, total = UserService.get_users(db, skip, limit, search, role_id)
    
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Create a new user (admin only)."""
    # Check if email already exists
    if UserService.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    if user_data.username and UserService.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    user = UserService.create_user(db, user_data)
    
    UserService.log_audit(
        db, current_user.id, "user_created", "user", user.id,
        ip_address=request.client.host if request.client else None
    )

    return user


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    request: Request,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile."""
    # Check if email is being changed and already exists
    if user_data.email and user_data.email != current_user.email:
        existing = UserService.get_user_by_email(db, user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Check if username is being changed and already exists
    if user_data.username and user_data.username != current_user.username:
        existing = UserService.get_user_by_username(db, user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    user = UserService.update_user(db, current_user.id, user_data)
    
    UserService.log_audit(
        db, current_user.id, "profile_updated", "user", current_user.id,
        ip_address=request.client.host if request.client else None
    )

    return user


@router.put("/me/password", status_code=status.HTTP_200_OK)
async def change_my_password(
    request: Request,
    password_data: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change current user password."""
    success = UserService.update_password(db, current_user.id, password_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    UserService.log_audit(
        db, current_user.id, "password_changed", "user", current_user.id,
        ip_address=request.client.host if request.client else None
    )

    return {"message": "Password updated successfully"}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get user by ID (admin only)."""
    user = UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Update user (admin only)."""
    user = UserService.update_user(db, user_id, user_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    UserService.log_audit(
        db, current_user.id, "user_updated", "user", user_id,
        ip_address=request.client.host if request.client else None
    )

    return user


@router.put("/{user_id}/role")
async def update_user_role(
    request: Request,
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Update user role (admin only)."""
    user = UserService.update_user_role(db, user_id, role_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or role not found"
        )

    UserService.log_audit(
        db, current_user.id, "user_role_updated", "user", user_id,
        details=f"Role changed to {role_id}",
        ip_address=request.client.host if request.client else None
    )

    return {"message": "User role updated successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Activate a user (admin only)."""
    user = UserService.activate_user(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    UserService.log_audit(
        db, current_user.id, "user_activated", "user", user_id,
        ip_address=request.client.host if request.client else None
    )

    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Deactivate a user (admin only)."""
    user = UserService.deactivate_user(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    UserService.log_audit(
        db, current_user.id, "user_deactivated", "user", user_id,
        ip_address=request.client.host if request.client else None
    )

    return {"message": "User deactivated successfully"}


@router.get("/roles/", response_model=list[RoleResponse])
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """List all roles (admin only)."""
    roles = db.query(Role).all()
    return roles