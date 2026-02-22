# Routes Architecture and Security

## Architecture Overview

The API follows a layered FastAPI architecture:

- Entry point: `main.py`
- Router composition: `app/api/api.py`
- Domain routes: `app/api/routes/*`
- Business logic: `app/services/*`
- Data models: `app/models/*`
- Schemas: `app/schemas/*`
- Infrastructure: `app/core`, `app/db`, `app/middleware`

## Request Flow

1. Request enters FastAPI app.
2. Middleware executes (`RateLimiterMiddleware`, `ErrorHandlerMiddleware`, `LogMiddleware`).
3. Route dependency resolution runs (`get_current_active_user` where configured).
4. Route handler calls service layer.
5. Service layer interacts with DB session.
6. Response serialized via Pydantic schema.

## AuthN/AuthZ Model

- Authentication uses JWT tokens produced by `/auth/login`.
- Protected routers depend on `get_current_active_user`.
- Authorization is enforced by:
  - router-level dependency for broad protection
  - service-level ownership checks for object-level protection
  - explicit admin checks for privileged operations

## Security Controls in Codebase

- Password hashing and verification in auth/security modules.
- JWT token generation and validation.
- Request throttling via `RATE_LIMIT_PER_MINUTE`.
- CORS allowlist via `CORS_ALLOWED_ORIGINS`.
- Centralized error handling middleware.
- Startup DB connectivity verification (`SELECT 1`) to fail fast.

## Environment and Secrets

- Required environment variable: `DATABASE_URL`.
- Mandatory in production: strong `SECRET_KEY` from secret manager.
- Do not rely on default secret values outside local development.

## Operational Hardening Checklist

- Set strong random `SECRET_KEY` per environment.
- Limit CORS origins to trusted frontends.
- Tune rate limits based on traffic profile.
- Enable DB connection pooling and pre-ping.
- Add structured audit logging for admin actions.
- Add metrics/alerts for auth failures and 5xx spikes.
- Run migrations (`alembic upgrade head`) on deployment.

## Production Recommendations

- Deploy behind HTTPS reverse proxy.
- Isolate database network access.
- Rotate secrets periodically.
- Add centralized logging and tracing.
- Add backup and restore drills for database.
