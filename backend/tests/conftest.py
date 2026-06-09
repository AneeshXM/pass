"""Test configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.core.config import settings


@pytest.fixture
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "TestPass123!"
    }


@pytest.fixture
def test_vault_data():
    """Test vault data."""
    return {
        "name": "Test Vault",
        "description": "A test vault",
        "icon": "folder",
        "color": "#4F46E5",
        "is_shared": False
    }


@pytest.fixture
def test_credential_data():
    """Test credential data."""
    return {
        "name": "Test Credential",
        "url": "https://test.com",
        "username": "testuser",
        "password": "SecretPass123!",
        "notes": "Test notes"
    }