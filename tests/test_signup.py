from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from asset_management.database.common import Base
from asset_management.database.session import get_session
from asset_management.main import app

# Import all models to ensure they are registered
from asset_management.database import import_models
import_models()

from asset_management.app.user.models import User

# Use SQLite in-memory database for testing instead of MySQL
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database override"""
    TestingSessionLocal = sessionmaker(
        bind=test_db, autocommit=False, autoflush=False, future=True
    )
    
    def override_get_session():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_session(test_db):
    """Provide a database session for verification"""
    TestingSessionLocal = sessionmaker(
        bind=test_db, autocommit=False, autoflush=False, future=True
    )
    return TestingSessionLocal


def test_signup_success(client, db_session):
    payload = {"name": "Alice", "email": "alice@example.com", "password": "strongpass"}

    response = client.post("/api/users/signup", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["name"] == payload["name"]
    assert "id" in data

    with db_session() as session:
        user = session.query(User).filter(User.email == payload["email"]).one()
        assert user.hashed_password != payload["password"]
        # argon2 해시는 "$argon2"로 시작함
        assert user.hashed_password.startswith("$argon2")


def test_signup_conflict_email(client):
    payload = {"name": "Bob", "email": "bob@example.com", "password": "securepass"}

    first = client.post("/api/users/signup", json=payload)
    second = client.post("/api/users/signup", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Email already registered"
