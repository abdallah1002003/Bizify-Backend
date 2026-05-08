# Bizify — Configuration & Setup

This guide details how to configure the environment variables and run the backend locally for development.

## 1. Environment Variables

Settings are strictly typed and loaded by `app/core/config.py` using `pydantic-settings` from a `.env` file located in the project root.

| Variable | Purpose |
|---|---|
| `PROJECT_NAME` | Application display name. |
| `DATABASE_URL` | Full SQLAlchemy database URL (e.g., `postgresql://...`). If missing, it builds one from the POSTGRES components. |
| `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | PostgreSQL connection components used if `DATABASE_URL` is empty. |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_URL` | Redis cache and Celery transport configuration. |
| `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT generation and validation settings. |
| `SESSION_TIMEOUT_MINUTES`, `SESSION_WARNING_MINUTES` | Inactivity timeout rules. |
| `SMTP_TLS`, `SMTP_PORT`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAILS_FROM_EMAIL` | SMTP credentials for sending automated emails. |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | URLs connecting Celery to Redis. |
| `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_MODE`, `PAYPAL_WEBHOOK_ID` | PayPal Orders API integration credentials. |
| `PAYMOB_API_KEY`, `PAYMOB_HMAC_SECRET`, `PAYMOB_INTEGRATION_ID`, `PAYMOB_IFRAME_ID` | Paymob iframe payment integration. |
| `FRONTEND_URL` | Allowed CORS origin and OAuth redirect base URL. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google Cloud Console OAuth credentials. |
| `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_BUCKET_NAME` | Supabase document storage API keys. |

---

## 2. Setup and Running Locally

### Step 1: Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install dependencies
Using **uv** (recommended for speed):
```bash
uv sync
```
Using **pip**:
```bash
pip install -e .
```

### Step 3: Configure `.env`
Create a `.env` file in the root directory. Minimum required for local SQLite development:
```env
DATABASE_URL=sqlite:///./sql_app.db
SECRET_KEY=change-this-dev-secret
FRONTEND_URL=http://localhost:3000
```

### Step 4: Run database migrations
Ensure the schema is up to date. Alembic will use `DATABASE_URL` automatically.
```bash
alembic upgrade head
```

### Step 5: Seed useful local data
Populate the database with plans, skills, and demo data for testing:
```bash
python scripts/seed_plans.py
python scripts/seed_skills.py
python seed_db/seed_guidance.py
python seed_db/seed_demo_data.py
```

### Step 6: Run the API server
```bash
uvicorn app.main:app --reload
```
**Useful URLs:**
- Connectivity check: `http://localhost:8000/`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

### Step 7: Run Redis and Celery (For Exports)
If you need to test background exports, start Redis and the Celery worker:
```bash
redis-server
celery -A app.core.celery_app.celery_app worker -Q export_queue --loglevel=info
```

### Step 8: Run the smoke check
Verify the core endpoints are working:
```bash
python smoke_checks/app_smoke_check.py
```
*(This forces `DATABASE_URL=sqlite:///./sql_app.db` locally for testing)*
