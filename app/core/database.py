from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Determine database connectivity arguments based on the URL type (e.g., SQLite requires special handling)
connect_args = (
    {"check_same_thread": False} 
    if settings.get_database_url().startswith("sqlite") 
    else {}
)

_is_postgres = not settings.get_database_url().startswith("sqlite")

engine = create_engine(
    settings.get_database_url(),
    connect_args=connect_args,
    # Transaction-mode pooler (port 6543) on Supabase multiplexes real Postgres
    # connections so many app-level connections share few actual DB connections.
    # Keep the pool small — transaction pooling does the heavy lifting server-side.
    # pool_pre_ping silently drops stale sockets; pool_timeout fails fast so a
    # full pool surfaces as a 503 quickly rather than queuing for 30 s.
    pool_size=5 if _is_postgres else 1,
    max_overflow=5 if _is_postgres else 0,
    pool_timeout=8,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()


def ensure_sqlite_compatibility_schema() -> None:
    """
    Backfill lightweight SQLite-only schema drift needed for local demos.
    """
    if not settings.get_database_url().startswith("sqlite"):
        return

    with engine.begin() as connection:
        user_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(users)").fetchall()
        }
        if not user_columns:
            return

        if "google_id" not in user_columns:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN google_id VARCHAR")

        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"
        )


ensure_sqlite_compatibility_schema()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get a SQLAlchemy database session.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
