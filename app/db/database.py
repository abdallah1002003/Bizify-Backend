from typing import Any, AsyncGenerator, Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config.settings import settings

load_dotenv()
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

ENGINE_KWARGS: dict[str, object] = {"pool_pre_ping": True}
if SQLALCHEMY_DATABASE_URL.startswith(("postgresql://", "postgresql+")):
    ENGINE_KWARGS.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        }
    )

engine = create_engine(SQLALCHEMY_DATABASE_URL, **ENGINE_KWARGS)

if settings.APP_ENV.lower() != "test" and engine.url.get_backend_name() != "postgresql":
    raise RuntimeError(
        "DATABASE_URL must point to PostgreSQL when APP_ENV is not 'test'."
    )


if engine.url.get_backend_name() == "sqlite":
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
        _ = connection_record
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# Async engine (asyncpg for PostgreSQL, aiosqlite for SQLite in test env)
# ---------------------------------------------------------------------------

def _build_async_url(sync_url: str) -> str:
    """Derive an async-compatible SQLAlchemy URL from the synchronous one."""
    if sync_url.startswith("postgresql+psycopg2://"):
        return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    if sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://")
    if sync_url.startswith("sqlite:///"):
        return sync_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if sync_url.startswith("sqlite://"):
        return sync_url.replace("sqlite://", "sqlite+aiosqlite://")
    return sync_url  # Fallback


ASYNC_DATABASE_URL = _build_async_url(SQLALCHEMY_DATABASE_URL)

_async_engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
if ASYNC_DATABASE_URL.startswith("postgresql+asyncpg://"):
    _async_engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 1800,
        }
    )

async_engine = create_async_engine(ASYNC_DATABASE_URL, **_async_engine_kwargs)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def verify_database_connection() -> None:
    """
    Fail fast at startup if DATABASE_URL is wrong or the DB server is down.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "Database connection failed. Ensure DATABASE_URL in .env is valid "
            "and your PostgreSQL server is running."
        ) from exc


def get_db() -> Generator[Session, None, None]:
    """Sync FastAPI dependency — yields a SQLAlchemy Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Async FastAPI dependency — yields an AsyncSession.

    Usage in a route::

        @router.get("/sessions/{id}")
        async def read_session(
            id: UUID,
            db: AsyncSession = Depends(get_async_db),
        ):
            return await get_chat_session_async(db, id)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
