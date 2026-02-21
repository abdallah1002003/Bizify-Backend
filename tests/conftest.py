import os
import sys

import pytest
import pytest_asyncio

# Add project root to sys.path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force testing database URL before any project imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from typing import AsyncGenerator, Generator  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.security import get_password_hash  # noqa: E402
from app.db.database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
import app.models as models # noqa: E402

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Remove global engine instantiation to prevent memory leak across tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    # Deprecated: Engine is now generated per function
    pass

@pytest.fixture(scope="function")
def db():
    # Generate a fresh memory engine for every test
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    connection.close()
    engine.dispose()

@pytest.fixture(scope="function")
def client(db) -> Generator[TestClient, None, None]:
    """
    Synchronous client for backward compatibility or simple tests
    """
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, headers={"X-Skip-Rate-Limit": "true"}) as c:
        yield c
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def async_client(db) -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous client using httpx
    """
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"X-Skip-Rate-Limit": "true"}
    ) as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db):
    user_data = {
        "email": "test@example.com",
        "password_hash": get_password_hash("testpass123"),
        "name": "Test User",
        "role": "entrepreneur",
        "is_active": True,
        "is_verified": True
    }
    user = models.User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_token(test_user):
    """Mint a direct secure JWT for testing, bypassing mock session issues."""
    from app.core.security import create_access_token
    # Directly return a valid cryptographic token simulating a logged-in user
    return create_access_token(subject=str(test_user.id))

@pytest.fixture(scope="function")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
