# P7 - Idea Spark API

FastAPI backend for idea management, business workflows, AI agents, billing, chat, partners, and core collaboration utilities.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://localhost:5432/postgres"
alembic upgrade head
uvicorn main:app --reload --port 8001
```

API base URL: `http://127.0.0.1:8001/api/v1`

## Authentication

1. Create user: `POST /api/v1/users/`
2. Login: `POST /api/v1/auth/login`
3. Use token: `Authorization: Bearer <token>`

Most routes require authentication.

## Testing

```bash
pytest -q
```

Current status: all tests pass.

## Project Structure

- `app/api/routes/`: API endpoints
- `app/services/`: business logic
- `app/models/`: SQLAlchemy models
- `app/schemas/`: Pydantic schemas
- `alembic/`: migrations
- `tests/`: API, integration, security, and unit tests

## Notes

- Default local database is PostgreSQL (`postgresql+psycopg2://localhost:5432/postgres`).
- Set environment variables in `.env` to override defaults (database URL, JWT secret, etc).
- `AUTO_CREATE_TABLES=false` by default. For local bootstrap either:
  - run migrations (`alembic upgrade head`), or
  - set `AUTO_CREATE_TABLES=true` in `.env`.
- Configure CORS via `CORS_ALLOWED_ORIGINS` (comma-separated origins).
- Configure request throttling via `RATE_LIMIT_PER_MINUTE`.
