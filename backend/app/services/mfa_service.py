"""MFA and backup services."""
import secrets
import json
from typing import Optional, List, Tuple

import pyotp
import qrcode
from io import BytesIO
import base64

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.permission import MFASettings, AuditLog
from app.core.security import security, encryption
from app.schemas.vault import VaultCreate, CredentialCreate


class MFAService:
    """Service for multi-factor authentication."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(secret: str, email: str) -> str:
        """Get provisioning URI for QR code."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name="Password Manager")

    @staticmethod
    def generate_qr_code(data: str) -> str:
        """Generate QR code as base64 string."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        return base64.b64encode(buffer.getvalue()).decode()

    @staticmethod
    def generate_backup_codes(count: int = 8) -> List[str]:
        """Generate backup codes."""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Verify TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    @staticmethod
    def enable_mfa(db: Session, user: User, password: str, code: str) -> Optional[dict]:
        """Enable MFA for user."""
        # Verify password
        if not security.verify_password(password, user.hashed_password):
            return None

        # Verify TOTP code
        if not user.mfa_secret or not MFAService.verify_code(user.mfa_secret, code):
            return None

        # Generate backup codes
        backup_codes = MFAService.generate_backup_codes()
        
        # Store backup codes (hashed)
        hashed_codes = [security.hash_password(code) for code in backup_codes]

        # Update MFA settings
        mfa_settings = MFASettings(
            user_id=user.id,
            enabled=True,
            secret=user.mfa_secret,
            backup_codes=json.dumps(hashed_codes)
        )
        
        # Remove existing settings
        existing = db.query(MFASettings).filter(MFASettings.user_id == user.id).first()
        if existing:
            db.delete(existing)
        
        db.add(mfa_settings)
        
        # Update user
        user.mfa_enabled = True
        user.mfa_recovery_codes = json.dumps(backup_codes)
        
        db.commit()

        return {
            "backup_codes": backup_codes
        }

    @staticmethod
    def disable_mfa(db: Session, user: User, password: str, code: str) -> bool:
        """Disable MFA for user."""
        if not security.verify_password(password, user.hashed_password):
            return False

        if not user.mfa_enabled:
            return True

        # Verify code or backup code
        verified = False
        
        # Check TOTP
        if user.mfa_secret and MFAService.verify_code(user.mfa_secret, code):
            verified = True
        
        # Check backup codes
        if not verified and user.mfa_recovery_codes:
            backup_codes = json.loads(user.mfa_recovery_codes)
            for backup_code in backup_codes:
                if code == backup_code:
                    verified = True
                    break

        if not verified:
            return False

        # Disable MFA
        mfa_settings = db.query(MFASettings).filter(MFASettings.user_id == user.id).first()
        if mfa_settings:
            db.delete(mfa_settings)

        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_recovery_codes = None
        
        db.commit()
        return True

    @staticmethod
    def verify_mfa(db: Session, user: User, code: str) -> Tuple[bool, bool]:
        """
        Verify MFA code.
        Returns (is_valid, is_backup_code).
        """
        if not user.mfa_enabled:
            return True, False

        # Check TOTP
        if user.mfa_secret and MFAService.verify_code(user.mfa_secret, code):
            return True, False

        # Check backup codes
        if user.mfa_recovery_codes:
            backup_codes = json.loads(user.mfa_recovery_codes)
            if code in backup_codes:
                # Remove used backup code
                backup_codes.remove(code)
                user.mfa_recovery_codes = json.dumps(backup_codes)
                db.commit()
                return True, True

        return False, False


class BackupService:
    """Service for backup and restore."""

    @staticmethod
    def create_backup(db: Session, user_id: int, password: str = None) -> dict:
        """Create a backup of all user data."""
        from app.services.vault_service import VaultService, CredentialService
        
        # Get user data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        vaults, _ = VaultService.get_vaults_for_user(db, user_id, limit=10000)
        
        backup_data = {
            "version": "1.0",
            "exported_at": str(user.created_at),
            "user": {
                "email": user.email,
                "full_name": user.full_name
            },
            "vaults": []
        }

        for vault in vaults:
            credentials, _ = CredentialService.get_credentials_for_vault(
                db, vault.id, user_id, limit=10000
            )
            
            vault_data = {
                "name": vault.name,
                "description": vault.description,
                "is_shared": vault.is_shared,
                "credentials": []
            }

            for cred in credentials:
                decrypted_password = encryption.decrypt(cred.encrypted_password)
                vault_data["credentials"].append({
                    "name": cred.name,
                    "url": cred.url,
                    "username": cred.username,
                    "password": decrypted_password,
                    "notes": cred.notes
                })

            backup_data["vaults"].append(vault_data)

        # Encrypt if password provided
        if password:
            encrypted_data = encryption.encrypt(json.dumps(backup_data))
            return {
                "encrypted": True,
                "data": encrypted_data
            }

        return backup_data

    @staticmethod
    def restore_backup(db: Session, user_id: int, backup_data: dict, password: str = None) -> bool:
        """Restore backup data."""
        from app.services.vault_service import VaultService, CredentialService
        
        if password and backup_data.get("encrypted"):
            decrypted = encryption.decrypt(backup_data["data"])
            backup_data = json.loads(decrypted)

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        for vault_data in backup_data.get("vaults", []):
            vault = VaultService.create_vault(
                db, user_id,
                VaultCreate(
                    name=vault_data["name"],
                    description=vault_data.get("description"),
                    is_shared=vault_data.get("is_shared", False)
                )
            )

            for cred_data in vault_data.get("credentials", []):
                CredentialService.create_credential(
                    db, user_id,
                    CredentialCreate(
                        name=cred_data["name"],
                        url=cred_data.get("url"),
                        username=cred_data.get("username"),
                        password=cred_data["password"],
                        notes=cred_data.get("notes"),
                        vault_id=vault.id
                    )
                )

        return True