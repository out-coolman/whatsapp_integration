"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import TestingSettings
from main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    """Create database session for testing."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "helena_id": "test_lead_123",
        "first_name": "João",
        "last_name": "Silva",
        "email": "joao.silva@email.com",
        "phone": "+5563991234567",
        "stage": "new",
        "source": "organic",
        "tags": ["test"],
        "custom_fields": {"utm_source": "google"}
    }


@pytest.fixture
def sample_webhook_payload():
    """Sample Helena webhook payload."""
    return {
        "event_type": "lead_created",
        "timestamp": "2024-01-01T12:00:00Z",
        "data": {
            "helena_id": "test_lead_123",
            "first_name": "João",
            "last_name": "Silva",
            "email": "joao.silva@email.com",
            "phone": "+5563991234567",
            "stage": "new",
            "source": "organic"
        },
        "helena_lead_id": "test_lead_123"
    }


@pytest.fixture
def api_headers():
    """API headers with authentication."""
    return {
        "X-API-KEY": "your-secure-api-key-here",
        "Content-Type": "application/json"
    }