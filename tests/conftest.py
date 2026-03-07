import os
import sys
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

# Add project root to sys.path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force testing env before any project imports
os.environ["APP_ENV"] = "test"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-local-tests-1234567890")

from typing import AsyncGenerator, Generator  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.security import get_password_hash  # noqa: E402
from app.db.database import Base, get_db, get_async_db  # noqa: E402
from main import app  # noqa: E402
import app.models as models # noqa: E402

@pytest.fixture(scope="function")
def sqlite_test_url():
    """Generate a unique in-memory SQLite URL for each test.
    Using shared cache with a unique name allows sync and async engines
    to see the SAME in-memory database instance.
    """
    db_name = uuid.uuid4().hex
    return f"sqlite:///file:{db_name}?mode=memory&cache=shared&uri=true"

@pytest.fixture(scope="function")
def sync_engine(sqlite_test_url):
    """Create a synchronous engine for the unique in-memory DB."""
    # URI=True is required for shared memory names
    engine = create_engine(
        sqlite_test_url, 
        connect_args={"check_same_thread": False, "uri": True},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    # Keep one connection open to ensure the in-memory DB stays alive
    connection = engine.connect()
    try:
        yield engine
    finally:
        connection.close()
        engine.dispose()

@pytest.fixture(scope="function")
def async_test_url(sqlite_test_url):
    """Convert sync SQLite URL to async version."""
    return sqlite_test_url.replace("sqlite:///", "sqlite+aiosqlite:///")

@pytest.fixture(scope="function")
async def async_engine(async_test_url):
    """Create an asynchronous engine for the unique in-memory DB."""
    engine = create_async_engine(
        async_test_url,
        connect_args={"check_same_thread": False, "uri": True},
        poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
def db(sync_engine):
    """Standard sync DB session fixture."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest_asyncio.fixture(scope="function")
async def async_db(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Standard async DB session fixture."""
    AsyncTestingSessionLocal = async_sessionmaker(
        async_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    async with AsyncTestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
def client(db, async_engine) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden dependencies."""
    
    async def override_async_db():
        AsyncTestingSessionLocal = async_sessionmaker(
            async_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        async with AsyncTestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_async_db] = override_async_db
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def async_client(async_db) -> AsyncGenerator[AsyncClient, None]:
    """httpx AsyncClient for async endpoint testing."""
    app.dependency_overrides[get_async_db] = lambda: async_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.fixture(scope="function", autouse=True)
def mock_dispatcher():
    """Global mock for event dispatcher and cleanup of global states."""
    from app.core.token_blacklist import clear_blacklist
    clear_blacklist()
    with patch("app.core.events.dispatcher.emit", new_callable=AsyncMock) as mock:
        yield mock

# Factories
def make_user(db, *, email=None, role: str = "entrepreneur", **overrides):
    import uuid
    data = {
        "email": email or f"user_{uuid.uuid4().hex[:8]}@example.com",
        "password_hash": get_password_hash("factory_pass_123"),
        "name": "Factory User",
        "role": role,
        "is_active": True,
        "is_verified": True,
        **overrides,
    }
    user = models.User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_user(db):
    return make_user(db)

@pytest.fixture(scope="function")
def auth_token(test_user):
    from app.core.security import create_access_token
    return create_access_token(subject=str(test_user.id))

@pytest.fixture(scope="function")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture(scope="function")
def user_token(auth_token):
    return auth_token

@pytest.fixture(scope="function")
def another_user(db):
    return make_user(db)

@pytest.fixture(scope="function")
def another_user_token(another_user):
    from app.core.security import create_access_token
    return create_access_token(subject=str(another_user.id))

@pytest.fixture(scope="function")
def user_subscription(test_user, db):
    from app.services.billing import billing_service
    from app.schemas.billing.plan import PlanCreate
    from app.schemas.billing.subscription import SubscriptionCreate
    
    plan = billing_service.create_plan(db, obj_in=PlanCreate(
        name="Test Plan",
        description="Test subscription plan", 
        price=29.99, 
        billing_cycle="monthly", 
        features=[]
    ))
    
    subscription = billing_service.create_subscription(db, obj_in=SubscriptionCreate(
        user_id=test_user.id, 
        plan_id=plan.id
    ))
    return subscription

def make_business(db, owner_id, *, stage: str = "early", **overrides):
    from app.models.enums import BusinessStage
    from app.services.business.business_service import get_business_service_manual

    stage_enum = BusinessStage(stage) if isinstance(stage, str) else stage
    svc = get_business_service_manual(db)

    class _In:
        def model_dump(self, **_):
            return {"owner_id": owner_id, "stage": stage_enum, **overrides}

    return svc.create_business(_In())

def make_plan(db, *, name: str = "Test Plan", price: float = 9.99, **overrides):
    plan = models.Plan(
        name=name, 
        price=price, 
        features_json=overrides.pop("features_json", {}),
        is_active=overrides.pop("is_active", True), 
        **overrides,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
