# Bizify — Database Connection Reference

This document covers all database and cache connection details, configuration, lifecycle, and usage patterns in the Bizify backend.

---

## 1. PostgreSQL Connection

### Configuration (`app/core/database.py`)

The connection is built using **SQLAlchemy** and configured through environment variables loaded by `pydantic-settings`.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(settings.get_database_url(), connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

| Setting | Value |
|---|---|
| `autocommit` | `False` — all changes require explicit `db.commit()` |
| `autoflush` | `False` — prevents automatic flushing before queries |
| `connect_args` | `{}` for PostgreSQL, `{"check_same_thread": False}` for SQLite |

### URL Resolution (`get_database_url`)

The URL is resolved in this priority order:

1. **`DATABASE_URL`** env var (used in production/Supabase)
2. **Assembled from components:** `postgresql://{USER}:{PASSWORD}@{SERVER}/{DB}`

**Current production URL (Supabase):**
```
postgresql://postgres.<project-ref>:<password>@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
```

---

## 2. Session Lifecycle — `get_db()`

Every API endpoint that needs database access receives a session via **FastAPI Dependency Injection**:

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Usage in an endpoint:**
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

@router.get("/ideas")
def list_ideas(db: Session = Depends(get_db)):
    return idea_repo.get_by_owner(db, user_id=...)
```

| Lifecycle Step | Detail |
|---|---|
| **Open** | `SessionLocal()` creates a new session per request |
| **Yield** | Session is passed to the endpoint via `Depends(get_db)` |
| **Close** | `db.close()` is called in the `finally` block — always runs |

> **Note:** Sessions are **not shared** across requests. Each HTTP request gets its own isolated session.

---

## 3. SQLite Compatibility (Local Dev)

When `DATABASE_URL` starts with `sqlite://`, a compatibility function auto-runs at startup to patch schema drift:

```python
ensure_sqlite_compatibility_schema()  # called in app startup event
```

**What it does:**
- Detects if `google_id` column is missing from `users` table
- Adds the column via `ALTER TABLE` if absent
- Creates a unique index on `google_id`

This allows running the app locally against `sql_app.db` without needing a full PostgreSQL instance.

---

## 4. ORM Base — `Base`

All SQLAlchemy models inherit from the shared `Base`:

```python
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    ...
```

Models are registered in `app/models/__init__.py` and discovered automatically by Alembic.

---

## 5. Migrations — Alembic

Database schema changes are managed through **Alembic**.

| Command | Description |
|---|---|
| `alembic revision --autogenerate -m "message"` | Auto-generate a migration from model changes |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back the last migration |
| `alembic history` | List all migration history |

**Config file:** `alembic.ini` at the project root.
**Migrations directory:** `alembic/versions/`

---

## 6. Redis Connection (`app/core/cache.py`)

Redis is used for two purposes:
1. **Application cache** — via `CacheService`
2. **Celery broker & backend** — for background task queueing

### URL Resolution

```python
redis_url = settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
```

| Setting | Default |
|---|---|
| `REDIS_HOST` | `localhost` |
| `REDIS_PORT` | `6379` |
| `REDIS_URL` | Optional override (full URL) |
| Celery broker | `redis://localhost:6379/0` |
| Celery backend | `redis://localhost:6379/0` |

### `CacheService` — API

A singleton `cache` instance is imported wherever caching is needed:

```python
from app.core.cache import cache
```

| Method | Signature | Description |
|---|---|---|
| `get` | `(key: str)` | Fetch and deserialize a cached value (returns `None` on miss or error) |
| `set` | `(key, value, expire_seconds=3600)` | Serialize and store a value with TTL |
| `delete` | `(key: str)` | Remove a specific key |
| `delete_pattern` | `(pattern: str)` | Remove all keys matching a glob pattern (e.g. `"skills:*"`) |

> **Resilient by design:** All methods catch exceptions and return `None` / `False` instead of crashing — Redis is treated as optional infrastructure.

---

## 7. Supabase Storage Connection

Used exclusively for **partner document uploads** (not for the main database).

```python
from supabase import create_client
client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
```

| Setting | Value |
|---|---|
| `SUPABASE_URL` | `https://<project-ref>.supabase.co` |
| `SUPABASE_KEY` | Service role JWT key |
| `SUPABASE_BUCKET_NAME` | `partner-documents` |

---

## 8. Environment Variables Summary

| Variable | Used For |
|---|---|
| `DATABASE_URL` | Full PostgreSQL connection string (overrides component vars) |
| `POSTGRES_SERVER` | DB host (used only if `DATABASE_URL` is not set) |
| `POSTGRES_USER` | DB username |
| `POSTGRES_PASSWORD` | DB password |
| `POSTGRES_DB` | Database name |
| `REDIS_URL` | Full Redis URL (overrides host/port vars) |
| `REDIS_HOST` | Redis hostname (default: `localhost`) |
| `REDIS_PORT` | Redis port (default: `6379`) |
| `CELERY_BROKER_URL` | Celery task broker (default: `redis://localhost:6379/0`) |
| `CELERY_RESULT_BACKEND` | Celery result storage (default: `redis://localhost:6379/0`) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service role key |
| `SUPABASE_BUCKET_NAME` | Storage bucket for partner documents |

---

## 9. Connection Flow Diagram

```
HTTP Request
    │
    ▼
FastAPI Endpoint
    │
    ├── Depends(get_db)
    │       └── SessionLocal() → SQLAlchemy Session
    │               │
    │               └── PostgreSQL (Supabase)
    │                       via psycopg2-binary driver
    │
    ├── cache.get / cache.set
    │       └── Redis (CacheService)
    │
    └── Celery Task (async)
            └── Redis (broker + backend)
```
