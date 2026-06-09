"""Vault and credential service for business logic."""
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.vault import Vault, Credential, Tag, CredentialTag, UserGroup
from app.models.user import User
from app.models.permission import Permission
from app.core.security import encryption
from app.schemas.vault import VaultCreate, VaultUpdate, CredentialCreate, CredentialUpdate


class VaultService:
    """Service for vault management."""

    @staticmethod
    def get_vault_by_id(db: Session, vault_id: int) -> Optional[Vault]:
        """Get vault by ID."""
        return db.query(Vault).filter(Vault.id == vault_id).first()

    @staticmethod
    def get_vaults_for_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        shared_only: bool = False
    ) -> Tuple[List[Vault], int]:
        """Get vaults accessible by user."""
        # Get owned vaults
        owned_query = db.query(Vault).filter(Vault.owner_id == user_id)
        
        # Get vaults with permissions
        permitted_ids = db.query(Permission.vault_id).filter(
            Permission.user_id == user_id,
            Permission.can_read == True
        ).subquery()
        permitted_query = db.query(Vault).filter(Vault.id.in_(permitted_ids))

        if shared_only:
            owned_query = owned_query.filter(Vault.is_shared == True)
            permitted_query = permitted_query.filter(Vault.is_shared == True)

        # Combine queries
        query = owned_query.union(permitted_query)

        if search:
            query = query.filter(Vault.name.ilike(f"%{search}%"))

        total = query.count()
        vaults = query.order_by(Vault.created_at.desc()).offset(skip).limit(limit).all()

        return vaults, total

    @staticmethod
    def create_vault(db: Session, user_id: int, vault_data: VaultCreate) -> Vault:
        """Create a new vault."""
        vault = Vault(
            name=vault_data.name,
            description=vault_data.description,
            icon=vault_data.icon,
            color=vault_data.color,
            is_shared=vault_data.is_shared,
            owner_id=user_id,
            group_id=vault_data.group_id
        )
        db.add(vault)
        db.commit()
        db.refresh(vault)
        return vault

    @staticmethod
    def update_vault(db: Session, vault_id: int, vault_data: VaultUpdate) -> Optional[Vault]:
        """Update vault details."""
        vault = VaultService.get_vault_by_id(db, vault_id)
        if not vault:
            return None

        for field, value in vault_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(vault, field, value)

        db.commit()
        db.refresh(vault)
        return vault

    @staticmethod
    def delete_vault(db: Session, vault_id: int) -> bool:
        """Delete a vault."""
        vault = VaultService.get_vault_by_id(db, vault_id)
        if not vault:
            return False

        db.delete(vault)
        db.commit()
        return True

    @staticmethod
    def check_vault_access(db: Session, vault_id: int, user_id: int, require_write: bool = False) -> bool:
        """Check if user has access to vault."""
        vault = VaultService.get_vault_by_id(db, vault_id)
        if not vault:
            return False

        # Owner has full access
        if vault.owner_id == user_id:
            return True

        # Check permissions
        permission = db.query(Permission).filter(
            Permission.vault_id == vault_id,
            Permission.user_id == user_id
        ).first()

        if not permission:
            return False

        if require_write:
            return permission.can_write
        return permission.can_read

    @staticmethod
    def get_vault_stats(db: Session, user_id: int) -> dict:
        """Get vault statistics for user."""
        total_vaults = db.query(Vault).filter(Vault.owner_id == user_id).count()
        
        shared_vaults = db.query(Vault).filter(
            Vault.owner_id == user_id,
            Vault.is_shared == True
        ).count()

        return {
            "total_vaults": total_vaults,
            "shared_vaults": shared_vaults
        }


class CredentialService:
    """Service for credential management."""

    @staticmethod
    def get_credential_by_id(db: Session, credential_id: int) -> Optional[Credential]:
        """Get credential by ID."""
        return db.query(Credential).filter(Credential.id == credential_id).first()

    @staticmethod
    def get_credentials_for_vault(
        db: Session,
        vault_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        favorites_only: bool = False
    ) -> Tuple[List[Credential], int]:
        """Get credentials for a vault."""
        if not VaultService.check_vault_access(db, vault_id, user_id):
            return [], 0

        query = db.query(Credential).filter(Credential.vault_id == vault_id)

        if favorites_only:
            query = query.filter(Credential.favorite == True)

        if search:
            query = query.filter(
                (Credential.name.ilike(f"%{search}%")) |
                (Credential.username.ilike(f"%{search}%")) |
                (Credential.url.ilike(f"%{search}%"))
            )

        total = query.count()
        credentials = query.order_by(Credential.name).offset(skip).limit(limit).all()

        return credentials, total

    @staticmethod
    def get_all_credentials_for_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> Tuple[List[Credential], int]:
        """Get all credentials for user."""
        query = db.query(Credential).filter(Credential.user_id == user_id)

        if search:
            query = query.filter(
                (Credential.name.ilike(f"%{search}%")) |
                (Credential.username.ilike(f"%{search}%")) |
                (Credential.url.ilike(f"%{search}%"))
            )

        total = query.count()
        credentials = query.order_by(Credential.name).offset(skip).limit(limit).all()

        return credentials, total

    @staticmethod
    def create_credential(
        db: Session,
        user_id: int,
        credential_data: CredentialCreate
    ) -> Optional[Credential]:
        """Create a new credential."""
        # Verify vault access
        if not VaultService.check_vault_access(db, credential_data.vault_id, user_id, require_write=True):
            return None

        encrypted_password = encryption.encrypt(credential_data.password)

        credential = Credential(
            name=credential_data.name,
            url=credential_data.url,
            username=credential_data.username,
            encrypted_password=encrypted_password,
            notes=credential_data.notes,
            vault_id=credential_data.vault_id,
            user_id=user_id,
            expires_at=credential_data.expires_at
        )
        db.add(credential)

        # Add tags
        if credential_data.tag_ids:
            for tag_id in credential_data.tag_ids:
                tag = db.query(Tag).filter(Tag.id == tag_id).first()
                if tag:
                    ct = CredentialTag(credential=credential, tag=tag)
                    db.add(ct)

        db.commit()
        db.refresh(credential)
        return credential

    @staticmethod
    def update_credential(
        db: Session,
        credential_id: int,
        user_id: int,
        credential_data: CredentialUpdate
    ) -> Optional[Credential]:
        """Update credential details."""
        credential = CredentialService.get_credential_by_id(db, credential_id)
        if not credential:
            return None

        if not VaultService.check_vault_access(db, credential.vault_id, user_id, require_write=True):
            return None

        for field, value in credential_data.model_dump(exclude_unset=True).items():
            if field == "password" and value is not None:
                setattr(credential, "encrypted_password", encryption.encrypt(value))
            elif field == "tag_ids" and value is not None:
                # Update tags
                db.query(CredentialTag).filter(
                    CredentialTag.credential_id == credential_id
                ).delete()
                for tag_id in value:
                    tag = db.query(Tag).filter(Tag.id == tag_id).first()
                    if tag:
                        ct = CredentialTag(credential_id=credential_id, tag_id=tag_id)
                        db.add(ct)
            elif value is not None:
                setattr(credential, field, value)

        db.commit()
        db.refresh(credential)
        return credential

    @staticmethod
    def delete_credential(db: Session, credential_id: int, user_id: int) -> bool:
        """Delete a credential."""
        credential = CredentialService.get_credential_by_id(db, credential_id)
        if not credential:
            return False

        if not VaultService.check_vault_access(db, credential.vault_id, user_id, require_write=True):
            return False

        db.delete(credential)
        db.commit()
        return True

    @staticmethod
    def decrypt_password(db: Session, credential_id: int, user_id: int) -> Optional[str]:
        """Decrypt and return credential password."""
        credential = CredentialService.get_credential_by_id(db, credential_id)
        if not credential:
            return None

        if not VaultService.check_vault_access(db, credential.vault_id, user_id):
            return None

        return encryption.decrypt(credential.encrypted_password)

    @staticmethod
    def toggle_favorite(db: Session, credential_id: int, user_id: int) -> Optional[Credential]:
        """Toggle credential favorite status."""
        credential = CredentialService.get_credential_by_id(db, credential_id)
        if not credential:
            return None

        if not VaultService.check_vault_access(db, credential.vault_id, user_id):
            return None

        credential.favorite = not credential.favorite
        db.commit()
        db.refresh(credential)
        return credential


class TagService:
    """Service for tag management."""

    @staticmethod
    def get_tag_by_id(db: Session, tag_id: int) -> Optional[Tag]:
        """Get tag by ID."""
        return db.query(Tag).filter(Tag.id == tag_id).first()

    @staticmethod
    def get_tags_for_vault(db: Session, vault_id: int) -> List[Tag]:
        """Get tags for a vault."""
        return db.query(Tag).filter(Tag.vault_id == vault_id).all()

    @staticmethod
    def create_tag(db: Session, vault_id: int, name: str, color: str = None) -> Tag:
        """Create a new tag."""
        tag = Tag(name=name, color=color, vault_id=vault_id)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    def delete_tag(db: Session, tag_id: int) -> bool:
        """Delete a tag."""
        tag = TagService.get_tag_by_id(db, tag_id)
        if not tag:
            return False

        db.delete(tag)
        db.commit()
        return True


class PermissionService:
    """Service for vault permissions."""

    @staticmethod
    def get_permission(db: Session, user_id: int, vault_id: int) -> Optional[Permission]:
        """Get permission for user on vault."""
        return db.query(Permission).filter(
            Permission.user_id == user_id,
            Permission.vault_id == vault_id
        ).first()

    @staticmethod
    def create_or_update_permission(
        db: Session,
        user_id: int,
        vault_id: int,
        can_read: bool = True,
        can_write: bool = False,
        can_share: bool = False,
        can_delete: bool = False
    ) -> Permission:
        """Create or update permission."""
        permission = PermissionService.get_permission(db, user_id, vault_id)

        if permission:
            permission.can_read = can_read
            permission.can_write = can_write
            permission.can_share = can_share
            permission.can_delete = can_delete
        else:
            permission = Permission(
                user_id=user_id,
                vault_id=vault_id,
                can_read=can_read,
                can_write=can_write,
                can_share=can_share,
                can_delete=can_delete
            )
            db.add(permission)

        db.commit()
        db.refresh(permission)
        return permission

    @staticmethod
    def delete_permission(db: Session, user_id: int, vault_id: int) -> bool:
        """Delete permission."""
        permission = PermissionService.get_permission(db, user_id, vault_id)
        if not permission:
            return False

        db.delete(permission)
        db.commit()
        return True


class UserGroupService:
    """Service for user groups."""

    @staticmethod
    def get_group_by_id(db: Session, group_id: int) -> Optional[UserGroup]:
        """Get group by ID."""
        return db.query(UserGroup).filter(UserGroup.id == group_id).first()

    @staticmethod
    def get_groups_for_user(db: Session, user_id: int) -> List[UserGroup]:
        """Get groups for a user."""
        return db.query(UserGroup).join(UserGroup.members).filter(
            UserGroup.members.any(id=user_id)
        ).all()

    @staticmethod
    def create_group(db: Session, user_id: int, name: str, description: str = None) -> UserGroup:
        """Create a new user group."""
        group = UserGroup(name=name, description=description, created_by=user_id)
        db.add(group)
        db.commit()
        db.refresh(group)
        return group

    @staticmethod
    def add_member_to_group(db: Session, group_id: int, user_id: int) -> bool:
        """Add user to group."""
        group = UserGroupService.get_group_by_id(db, group_id)
        if not group:
            return False

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        if user not in group.members:
            group.members.append(user)
            db.commit()

        return True

    @staticmethod
    def remove_member_from_group(db: Session, group_id: int, user_id: int) -> bool:
        """Remove user from group."""
        group = UserGroupService.get_group_by_id(db, group_id)
        if not group:
            return False

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        if user in group.members:
            group.members.remove(user)
            db.commit()

        return True