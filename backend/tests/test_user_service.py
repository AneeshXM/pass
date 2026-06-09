"""Unit tests for user service."""
import pytest
from datetime import datetime, timezone

from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate


class TestUserService:
    """Tests for UserService class."""

    def test_create_user(self, db_session, test_user_data):
        """Test user creation."""
        user_data = UserCreate(**test_user_data)
        user = UserService.create_user(db_session, user_data)
        
        assert user.id is not None
        assert user.email == test_user_data["email"]
        assert user.username == test_user_data["username"]
        assert user.full_name == test_user_data["full_name"]
        assert user.hashed_password != test_user_data["password"]
        assert user.is_active is True
        assert user.role_id == 3  # Default User role

    def test_get_user_by_id(self, db_session, test_user_data):
        """Test getting user by ID."""
        user_data = UserCreate(**test_user_data)
        created_user = UserService.create_user(db_session, user_data)
        
        user = UserService.get_user_by_id(db_session, created_user.id)
        
        assert user is not None
        assert user.id == created_user.id

    def test_get_user_by_email(self, db_session, test_user_data):
        """Test getting user by email."""
        user_data = UserCreate(**test_user_data)
        UserService.create_user(db_session, user_data)
        
        user = UserService.get_user_by_email(db_session, test_user_data["email"])
        
        assert user is not None
        assert user.email == test_user_data["email"]

    def test_get_user_by_username(self, db_session, test_user_data):
        """Test getting user by username."""
        user_data = UserCreate(**test_user_data)
        UserService.create_user(db_session, user_data)
        
        user = UserService.get_user_by_username(db_session, test_user_data["username"])
        
        assert user is not None
        assert user.username == test_user_data["username"]

    def test_update_user(self, db_session, test_user_data):
        """Test user update."""
        user_data = UserCreate(**test_user_data)
        user = UserService.create_user(db_session, user_data)
        
        update_data = UserUpdate(full_name="Updated Name", phone="+1234567890")
        updated_user = UserService.update_user(db_session, user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.phone == "+1234567890"

    def test_update_password(self, db_session, test_user_data):
        """Test password update."""
        user_data = UserCreate(**test_user_data)
        user = UserService.create_user(db_session, user_data)
        
        from app.schemas.user import UserPasswordUpdate
        password_data = UserPasswordUpdate(
            current_password=test_user_data["password"],
            new_password="NewPassword123!"
        )
        
        result = UserService.update_password(db_session, user.id, password_data)
        
        assert result is True
        
        # Verify new password works
        from app.core.security import security
        user = UserService.get_user_by_id(db_session, user.id)
        assert security.verify_password("NewPassword123!", user.hashed_password)

    def test_update_password_wrong_current(self, db_session, test_user_data):
        """Test password update with wrong current password."""
        user_data = UserCreate(**test_user_data)
        user = UserService.create_user(db_session, user_data)
        
        from app.schemas.user import UserPasswordUpdate
        password_data = UserPasswordUpdate(
            current_password="WrongPassword",
            new_password="NewPassword123!"
        )
        
        result = UserService.update_password(db_session, user.id, password_data)
        
        assert result is False

    def test_deactivate_user(self, db_session, test_user_data):
        """Test user deactivation."""
        user_data = UserCreate(**test_user_data)
        user = UserService.create_user(db_session, user_data)
        
        deactivated = UserService.deactivate_user(db_session, user.id)
        
        assert deactivated is not None
        assert deactivated.is_active is False

    def test_activate_user(self, db_session, test_user_data):
        """Test user activation."""
        user_data = UserCreate(**test_user_data)
        user = UserService.create_user(db_session, user_data)
        UserService.deactivate_user(db_session, user.id)
        
        activated = UserService.activate_user(db_session, user.id)
        
        assert activated is not None
        assert activated.is_active is True
        assert activated.failed_login_attempts == 0

    def test_get_users_pagination(self, db_session, test_user_data):
        """Test user list pagination."""
        # Create multiple users
        for i in range(15):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                username=f"user{i}",
                password="TestPass123!"
            )
            UserService.create_user(db_session, user_data)
        
        # Test pagination
        users, total = UserService.get_users(db_session, skip=0, limit=10)
        
        assert len(users) == 10
        assert total == 15

    def test_get_users_search(self, db_session, test_user_data):
        """Test user search."""
        UserService.create_user(db_session, UserCreate(
            email="john.doe@example.com",
            username="johndoe",
            full_name="John Doe",
            password="TestPass123!"
        ))
        UserService.create_user(db_session, UserCreate(
            email="jane.doe@example.com",
            username="janedoe",
            full_name="Jane Doe",
            password="TestPass123!"
        ))
        
        users, total = UserService.get_users(db_session, search="john")
        
        assert total == 1
        assert users[0].full_name == "John Doe"

    def test_log_audit(self, db_session, test_user_data):
        """Test audit logging."""
        user = UserService.create_user(db_session, UserCreate(**test_user_data))
        
        audit_log = UserService.log_audit(
            db_session,
            user_id=user.id,
            action="test_action",
            resource_type="test_resource",
            resource_id=1,
            details="Test details",
            ip_address="127.0.0.1"
        )
        
        assert audit_log is not None
        assert audit_log.user_id == user.id
        assert audit_log.action == "test_action"
        assert audit_log.resource_type == "test_resource"