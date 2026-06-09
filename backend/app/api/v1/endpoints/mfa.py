"""MFA endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.audit import MFAEnableRequest, MFAVerifyRequest, MFAResponse, MFADisableRequest
from app.services.mfa_service import MFAService
from app.services.user_service import UserService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/mfa", tags=["MFA"])


@router.get("/status")
async def get_mfa_status(
    current_user: User = Depends(get_current_user)
):
    """Get MFA status for current user."""
    return {
        "enabled": current_user.mfa_enabled,
        "has_recovery_codes": current_user.mfa_recovery_codes is not None
    }


@router.post("/setup", response_model=MFAResponse)
async def setup_mfa(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Setup MFA for current user."""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )

    # Generate new secret
    secret = MFAService.generate_secret()
    
    # Get provisioning URI
    uri = MFAService.get_provisioning_uri(secret, current_user.email)
    
    # Generate QR code
    qr_code = MFAService.generate_qr_code(uri)
    
    # Generate backup codes
    backup_codes = MFAService.generate_backup_codes()
    
    # Store secret temporarily (will be verified in enable)
    current_user.mfa_secret = secret
    current_user.mfa_recovery_codes = ",".join(backup_codes)
    db.commit()
    
    UserService.log_audit(
        db, current_user.id, "mfa_setup_started", "user", current_user.id,
        ip_address=request.client.host if request.client else None
    )

    return MFAResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )


@router.post("/enable")
async def enable_mfa(
    request: Request,
    enable_data: MFAEnableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enable MFA after verification."""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )

    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated"
        )

    result = MFAService.enable_mfa(db, current_user, enable_data.password, enable_data.code)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password or MFA code"
        )
    
    UserService.log_audit(
        db, current_user.id, "mfa_enabled", "user", current_user.id,
        ip_address=request.client.host if request.client else None
    )

    return {
        "message": "MFA enabled successfully",
        "backup_codes": result["backup_codes"]
    }


@router.post("/disable")
async def disable_mfa(
    request: Request,
    disable_data: MFADisableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disable MFA."""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    success = MFAService.disable_mfa(db, current_user, disable_data.password, disable_data.code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password or MFA code"
        )
    
    UserService.log_audit(
        db, current_user.id, "mfa_disabled", "user", current_user.id,
        ip_address=request.client.host if request.client else None
    )

    return {"message": "MFA disabled successfully"}


@router.post("/verify")
async def verify_mfa_code(
    request: Request,
    verify_data: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify MFA code."""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    is_valid, is_backup = MFAService.verify_mfa(db, current_user, verify_data.code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code"
        )

    return {
        "valid": True,
        "is_backup": is_backup
    }


@router.post("/regenerate-backup-codes")
async def regenerate_backup_codes(
    request: Request,
    password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate MFA backup codes."""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    from app.core.security import security
    if not security.verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    backup_codes = MFAService.generate_backup_codes()
    current_user.mfa_recovery_codes = ",".join(backup_codes)
    db.commit()
    
    UserService.log_audit(
        db, current_user.id, "mfa_backup_codes_regenerated", "user", current_user.id,
        ip_address=request.client.host if request.client else None
    )

    return {
        "backup_codes": backup_codes
    }