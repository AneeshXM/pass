"""User service for business logic."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.user import User, Role
from app.models.permission import AuditLog
from app.core.security import security
from app.schemas.user import UserCreate, UserUpdate, UserPasswordUpdate
from app.core.config import settings


class UserService:
    """Service for user management."""

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role_id: Optional[int] = None
    ) -> tuple[List[User], int]:
        """Get paginated list of users."""
        query = db.query(User)

        if search:
            query = query.filter(
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%")) |
                (User.username.ilike(f"%{search}%"))
            )

        if role_id:
            query = query.filter(User.role_id == role_id)

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        return users, total

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=security.hash_password(user_data.password),
            role_id=3  # Default to User role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user details."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        for field, value in user_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user_id: int, password_data: UserPasswordUpdate) -> bool:
        """Update user password."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        if not security.verify_password(password_data.current_password, user.hashed_password):
            return False

        user.hashed_password = security.hash_password(password_data.new_password)
        db.commit()
        return True

    @staticmethod
    def update_user_role(db: Session, user_id: int, role_id: int) -> Optional[User]:
        """Update user role."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return None

        user.role_id = role_id
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> Optional[User]:
        """Deactivate a user."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        user.is_active = False
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def activate_user(db: Session, user_id: int) -> Optional[User]:
        """Activate a user."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        user.is_active = True
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def check_login_attempts(db: Session, user: User) -> bool:
        """Check if user is locked out."""
        if user.locked_until:
            locked_until = datetime.fromisoformat(user.locked_until)
            if datetime.now(timezone.utc) < locked_until:
                return True
            # Unlock if time has passed
            user.locked_until = None
            user.failed_login_attempts = 0
            db.commit()

        return False

    @staticmethod
    def record_failed_login(db: Session, user: User) -> None:
        """Record a failed login attempt."""
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= settings.LOGIN_RATE_LIMIT:
            locked_until = datetime.now(timezone.utc) + \
                timezone(timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES))
            user.locked_until = locked_until.isoformat()

        db.commit()

    @staticmethod
    def reset_failed_logins(db: Session, user: User) -> None:
        """Reset failed login counter."""
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    @staticmethod
    def log_audit(
        db: Session,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success"
    ) -> AuditLog:
        """Create an audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        db.add(audit_log)
        db.commit()
        return audit_log