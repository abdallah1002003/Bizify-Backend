# Bizify Backend API

[![CI/CD Pipeline](https://github.com/abdallah1002003/Bizify-Backend/actions/workflows/ci.yml/badge.svg)](https://github.com/abdallah1002003/Bizify-Backend/actions/workflows/ci.yml)
[![CD - Build & Deploy](https://github.com/abdallah1002003/Bizify-Backend/actions/workflows/cd.yml/badge.svg)](https://github.com/abdallah1002003/Bizify-Backend/actions/workflows/cd.yml)
[![codecov](https://codecov.io/gh/abdallah1002003/Bizify-Backend/branch/main/graph/badge.svg)](https://codecov.io/gh/abdallah1002003/Bizify-Backend)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

FastAPI backend for idea management, business workflows, AI agents, billing, chat, partners, and core collaboration utilities.

## 🔀 API Versioning Strategy

All routes currently reside under the `v1` namespace (e.g., `/api/v1/users`).
When subsequent breaking database or contract modifications are required:
1. Do not overwrite `v1` controllers or models directly.
2. Scaffold a duplicate namespace in `app/api/routes_v2/` (or similar localized architectural paths).
3. Mount the new router namespace in `main.py` under `{app.include_router(..., prefix="/api/v2")}`.
4. Existing clients can smoothly migrate across bounded API lifecycle deprecations while maintaining backward compatibility.

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
3. Use token in request header:

```http
Authorization: Bearer <token>
```

Most routes require authentication.

If the header is missing or malformed, protected routes will return `401`.

### Admin Bootstrap (One-Time)

For first-time setup only, you can create the initial admin via:

- `POST /api/v1/auth/bootstrap-admin`
- Required header: `X-Bootstrap-Token: <ADMIN_BOOTSTRAP_TOKEN>`

Security behavior:
- Disabled by default (`ALLOW_ADMIN_BOOTSTRAP=false`)
- Requires exact bootstrap token match
- Works only if no admin account exists yet
- Returns JWT access token for the created admin

After creating the first admin, disable bootstrap again.

## Testing

```bash
# Optional (recommended): run tests against PostgreSQL
export TEST_DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/p7_test"
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

## Setup Notes & Environment Variables

- Default local database is PostgreSQL (`postgresql+psycopg2://localhost:5432/postgres`).
- **`SECRET_KEY`**: You **MUST** set a strong, random `SECRET_KEY` in your `.env` for production to secure JWT tokens.
- Set environment variables in `.env` to override defaults (database URL, JWT secret, etc).
- `DATABASE_URL` must be a PostgreSQL SQLAlchemy URL in normal runs.
- SQLite is supported only in automated tests (`APP_ENV=test`).
- App startup now validates DB connectivity (`SELECT 1`) and fails fast if DB is unreachable.
  - Ensure your DB server is running before `uvicorn main:app ...`.
  - You can disable this only for local debugging via `VERIFY_DB_ON_STARTUP=false`.
- `AUTO_CREATE_TABLES=false` by default. For local bootstrap either:
  - run migrations (`alembic upgrade head`), or
  - set `AUTO_CREATE_TABLES=true` in `.env`.
- Configure CORS via `CORS_ALLOWED_ORIGINS` (comma-separated origins).
- Configure request throttling via `RATE_LIMIT_PER_MINUTE`.
- Configure AI runtime via:
  - `AI_PROVIDER=mock|openai`
  - `OPENAI_API_KEY` (required only when `AI_PROVIDER=openai`)
  - `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_BASE_URL`
- For one-time admin provisioning:
  - `ALLOW_ADMIN_BOOTSTRAP` (default `false`)
  - `ADMIN_BOOTSTRAP_TOKEN` (required when bootstrap is enabled)
