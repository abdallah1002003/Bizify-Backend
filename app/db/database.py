from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import settings

load_dotenv()
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

ENGINE_KWARGS = {"pool_pre_ping": True}
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
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        _ = connection_record
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
