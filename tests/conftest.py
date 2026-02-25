import os
import sys

import pytest
import pytest_asyncio

# Add project root to sys.path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force testing env before any project imports
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-local-tests-1234567890")

from typing import AsyncGenerator, Generator  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.security import get_password_hash  # noqa: E402
from app.db.database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
import app.models as models # noqa: E402

IS_SQLITE_TEST = TEST_DATABASE_URL.startswith("sqlite://")
ENGINE_KWARGS = {}
if IS_SQLITE_TEST:
    ENGINE_KWARGS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
test_engine = None
TestingSessionLocal = None
if not IS_SQLITE_TEST:
    test_engine = create_engine(TEST_DATABASE_URL, **ENGINE_KWARGS)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_engine():
    yield
    if test_engine is not None:
        test_engine.dispose()

@pytest.fixture(scope="function")
def db():
    # Keep every test isolated regardless of backend (SQLite or PostgreSQL).
    if IS_SQLITE_TEST:
        sqlite_engine = create_engine(TEST_DATABASE_URL, **ENGINE_KWARGS)
        sqlite_session_local = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
        Base.metadata.create_all(bind=sqlite_engine)
        connection = sqlite_engine.connect()
        session = sqlite_session_local(bind=connection)

        yield session

        session.close()
        connection.close()
        sqlite_engine.dispose()
        return

    # PostgreSQL: TRUNCATE all tables with CASCADE to clear data between tests.
    # This avoids drop_all's circular FK topological sort failure (ideas ↔ businesses).
    # The schema already exists from the CI `alembic upgrade head` step.
    with test_engine.connect() as raw_conn:
        # Get all table names from Base metadata
        table_names = ", ".join(
            f'"{name}"' for name in Base.metadata.tables.keys()
        )
        if table_names:
            raw_conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
        raw_conn.commit()

    connection = test_engine.connect()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    connection.close()

@pytest.fixture(scope="function")
def client(db) -> Generator[TestClient, None, None]:
    """
    Synchronous client for backward compatibility or simple tests
    """
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
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
        base_url="http://test"
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
@pytest.fixture(scope="function")
def user_token(auth_token):
    """Alias for auth_token for backward compatibility."""
    return auth_token

@pytest.fixture(scope="function")
def another_user(db):
    """Create a second test user for multi-user scenarios."""
    from app.core.security import get_password_hash
    user_data = {
        "email": "another@example.com",
        "password_hash": get_password_hash("anotherpass123"),
        "name": "Another User",
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
def another_user_token(another_user):
    """Create a token for another user."""
    from app.core.security import create_access_token
    return create_access_token(subject=str(another_user.id))

@pytest.fixture(scope="function")
def user_subscription(test_user, db):
    """Create a subscription for the test user."""
    from app.services.billing import billing_service
    from app.schemas.billing.plan import PlanCreate
    from app.schemas.billing.subscription import SubscriptionCreate
    
    # Create a plan first
    plan = billing_service.create_plan(db, obj_in=PlanCreate(
        name="Test Plan",
        description="Test subscription plan",
        price=29.99,
        billing_cycle="monthly",
        features=[]
    ))
    
    # Create a subscription for the test user
    subscription = billing_service.create_subscription(db, obj_in=SubscriptionCreate(
        user_id=test_user.id,
        plan_id=plan.id
    ))
    return subscription


# =============================================================================
# Factory helpers — reusable across test modules
# =============================================================================

def make_user(db, *, email=None, role: str = "entrepreneur", **overrides):
    """
    Factory: create and persist a User with sensible defaults.

    Args:
        db: SQLAlchemy session
        email: unique email — auto-generated when omitted
        role: user role string (default: 'entrepreneur')
        **overrides: any User field to override

    Returns:
        Persisted User instance
    """
    import uuid as _uuid
    from app.core.security import get_password_hash as _hash

    data = {
        "email": email or f"user_{_uuid.uuid4().hex[:8]}@factory.test",
        "password_hash": _hash("factory_pass_123"),
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


def make_business(db, owner_id, *, stage: str = "early", **overrides):
    """
    Factory: create and persist a Business and its default roadmap.

    Args:
        db: SQLAlchemy session
        owner_id: UUID of the business owner
        stage: BusinessStage string (default: 'early')
        **overrides: any Business field to override

    Returns:
        Persisted Business instance
    """
    from app.models.enums import BusinessStage
    from app.services.business.business_service import get_business_service_manual

    stage_enum = BusinessStage(stage) if isinstance(stage, str) else stage
    svc = get_business_service_manual(db)

    class _In:
        def model_dump(self, **_):
            return {"owner_id": owner_id, "stage": stage_enum, **overrides}

    return svc.create_business(_In())


def make_plan(db, *, name: str = "Test Plan", price: float = 9.99, **overrides):
    """
    Factory: create and persist a billing Plan.

    Args:
        db: SQLAlchemy session
        name: plan name (default: 'Test Plan')
        price: plan price in USD (default: 9.99)
        **overrides: any Plan field to override

    Returns:
        Persisted Plan instance
    """
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