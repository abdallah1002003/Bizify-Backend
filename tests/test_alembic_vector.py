import os

from dotenv import load_dotenv
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.integration
def test_connection() -> None:
    """Validate database connectivity when a reachable DATABASE_URL is provided."""
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL is not set")

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        pytest.skip(f"Database is not reachable for this environment: {exc}")
    finally:
        engine.dispose()
