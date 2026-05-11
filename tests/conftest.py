import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.database import Base
from app.main import app

# Create an in-memory SQLite database for fast, isolated testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def mock_global_services():
    """
    Globally mock email delivery and DB compatibility tasks to prevent hangs.
    """
    with patch("app.services.user_service.send_otp_email"), \
         patch("app.core.database.ensure_sqlite_compatibility_schema"):
        yield


@pytest.fixture(scope="function")
def db_session():
    """
    Creates a fresh database schema for each test function,
    and drops it when the test completes. This ensures isolation.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Returns a FastAPI TestClient configured to use the test database
    instead of the real development database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
        
    # Clean up the override after the test
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client(client: TestClient, db_session):
    """
    Returns a TestClient with a Bearer token already set for a verified test user.
    Also returns the user's email so tests can query the user if needed.
    """
    from app.models.user import User
    import uuid
    
    # Generate unique email for the fixture
    email = f"testuser_{uuid.uuid4().hex[:6]}@bizify.com"
    password = "StrongPassword123!"
    
    client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "full_name": "Fixture User",
            "password": password,
            "confirm_password": password
        }
    )
    
    user = db_session.query(User).filter_by(email=email).first()
    user.is_verified = True
    db_session.commit()
    
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    
    token = login_resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    # Store user details in the client object to access it in tests
    client.user_id = user.id
    client.user_email = user.email
    
    return client


@pytest.fixture(scope="function")
def admin_client(db_session):
    """
    Returns an INDEPENDENT TestClient (its own instance) logged in as an ADMIN.
    Avoids header conflicts when used alongside auth_client in the same test.
    """
    from app.models.user import User, UserRole
    import uuid

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as admin_http:
        email = f"admin_{uuid.uuid4().hex[:6]}@bizify.com"
        password = "AdminPassword123!"

        admin_http.post(
            "/api/v1/users/register",
            json={
                "email": email,
                "full_name": "Admin User",
                "password": password,
                "confirm_password": password,
            },
        )

        user = db_session.query(User).filter_by(email=email).first()
        user.is_verified = True
        user.role = UserRole.ADMIN
        db_session.commit()

        login_resp = admin_http.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )

        token = login_resp.json()["access_token"]
        admin_http.headers.update({"Authorization": f"Bearer {token}"})

        admin_http.user_id = user.id
        admin_http.user_email = user.email

        yield admin_http

    app.dependency_overrides.clear()

