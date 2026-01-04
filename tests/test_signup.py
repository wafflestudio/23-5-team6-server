from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from asset_management.app.user.models import User
from asset_management.database.common import Base
from asset_management.database.session import get_session
from asset_management.main import app

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, future=True
)


def override_get_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


def setup_function():
    # Create only the user table needed for signup tests.
    Base.metadata.create_all(bind=engine, tables=[User.__table__])


def teardown_function():
    Base.metadata.drop_all(bind=engine, tables=[User.__table__])


def test_signup_success():
    payload = {"name": "Alice", "email": "alice@example.com", "password": "strongpass"}

    response = client.post("/api/users/signup", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["name"] == payload["name"]
    assert "id" in data

    with TestingSessionLocal() as session:
        user = session.query(User).filter(User.email == payload["email"]).one()
        assert user.hashed_password != payload["password"]
        assert len(user.hashed_password) == 64


def test_signup_conflict_email():
    payload = {"name": "Bob", "email": "bob@example.com", "password": "securepass"}

    first = client.post("/api/users/signup", json=payload)
    second = client.post("/api/users/signup", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Email already registered"
