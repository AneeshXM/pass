"""Authentication endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import security
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserResponse,
)
from app.services.user_service import UserService
from app.services.mfa_service import MFAService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens."""
    user = UserService.get_user_by_email(db, login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if account is locked
    if UserService.check_login_attempts(db, user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account is temporarily locked. Please try again later."
        )

    # Verify password
    if not security.verify_password(login_data.password, user.hashed_password):
        UserService.record_failed_login(db, user)
        UserService.log_audit(
            db, user.id, "login_failed", "user",
            details="Invalid password",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            status="failure"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if MFA is enabled
    if user.mfa_enabled:
        # Return partial token for MFA verification
        partial_token = security.create_access_token(
            user.id, 
            ["mfa_pending"],
        )
        return TokenResponse(
            access_token=partial_token,
            refresh_token="",
        )

    # Reset failed login attempts
    UserService.reset_failed_logins(db, user)

    # Create tokens
    access_token = security.create_access_token(user.id, [user.role.name])
    refresh_token = security.create_refresh_token(user.id)

    # Log successful login
    UserService.log_audit(
        db, user.id, "login", "user",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/verify-mfa")
async def verify_mfa(
    request: Request,
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify MFA code and complete login."""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    is_valid, is_backup = MFAService.verify_mfa(db, current_user, code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code"
        )

    # Reset failed login attempts
    UserService.reset_failed_logins(db, current_user)

    # Create tokens
    access_token = security.create_access_token(current_user.id, [current_user.role.name])
    refresh_token = security.create_refresh_token(current_user.id)

    # Log successful login
    UserService.log_audit(
        db, current_user.id, "login", "user",
        details=f"MFA verified (backup: {is_backup})",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    payload = security.verify_refresh_token(refresh_data.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = int(payload.get("sub"))
    user = UserService.get_user_by_id(db, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    access_token = security.create_access_token(user.id, [user.role.name])
    refresh_token = security.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logout user."""
    UserService.log_audit(
        db, current_user.id, "logout", "user",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return {"message": "Successfully logged out"}


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset."""
    user = UserService.get_user_by_email(db, reset_data.email)
    
    if user:
        # In production, send email with reset link
        # For now, just log the request
        UserService.log_audit(
            db, user.id, "password_reset_requested", "user"
        )

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token."""
    # In production, verify the reset token from email
    # For now, just validate the new password
    return {"message": "Password has been reset successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user