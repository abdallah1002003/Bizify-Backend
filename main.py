# ruff: noqa
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.security import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware

from app.db.database import Base, engine, verify_database_connection
from app import models as _models  # noqa: F401 - register models for metadata side effects
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.log_middleware import LogMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.rate_limiter_redis import RedisRateLimiterMiddleware
from config.settings import settings
from app.api.v1.api import api_router as api_router_v1
from app.db.database import SessionLocal
from app.services.core.cleanup_service import cleanup_all, cleanup_expired_tokens
from app.core.structured_logging import configure_structured_logging, get_logger
from app.core.event_handlers import register_all_handlers
from app.core.metrics import REGISTRY
from app.middleware.prometheus import setup_prometheus
import logging
import asyncio

# Configure structured logging at startup
configure_structured_logging(log_level="DEBUG" if settings.APP_ENV == "development" else "INFO")
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Sentry (optional — only activates when SENTRY_DSN is configured)
# ---------------------------------------------------------------------------
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.2,   # capture 20% of transactions for performance
        send_default_pii=False,   # never send personal data to Sentry
    )
    logger.info("Sentry initialized for environment: %s", settings.APP_ENV)




@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.VERIFY_DB_ON_STARTUP:
        verify_database_connection()
    if settings.AUTO_CREATE_TABLES and settings.APP_ENV != "production":
        Base.metadata.create_all(bind=engine)

    # Register internal event handlers
    register_all_handlers()

    # One-shot cleanup on startup (skip in test to avoid in-memory DB issues)
    if settings.APP_ENV != "test":
        db = SessionLocal()
        try:
            summary = cleanup_all(db)
            if any(v > 0 for v in summary.values()):
                logger.info("Startup cleanup: %s", summary)
        finally:
            db.close()

    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise API for User Profiling, Idea Management, Billing, Payments & Chat",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS and "*" not in settings.cors_allowed_origins_list,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Request-ID"],
)

# Custom middleware - Order matters (first added = last executed)
if settings.REDIS_ENABLED:
    app.add_middleware(RedisRateLimiterMiddleware)
else:
    app.add_middleware(RateLimiterMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LogMiddleware)

# Include routers
app.include_router(api_router_v1, prefix="/api/v1")

@app.get("/")
def read_root():
    """Root endpoint returning API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "1.0.0",
        "docs": "/docs"
    }

_internal_key_header = APIKeyHeader(name="X-Internal-Key", auto_error=False)


@app.get("/health")
async def health_check(
    x_internal_key: str = Depends(_internal_key_header),
):
    """
    Health check endpoint — two-tier response:

    * **Public** (no key): returns ``{status, version}`` only.
      Safe for load balancers and uptime monitors.
    * **Internal** (valid ``X-Internal-Key`` header): returns full
      diagnostics including database, Redis, and Stripe status.
      Use the same key as ``METRICS_API_KEY`` in your environment.
    """
    # ── Always check the database so the top-level status is accurate ──
    from sqlalchemy import text
    db_status = "ok"
    overall_status = "ok"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Health check - Database failed: %s", e)
        db_status = "error"
        overall_status = "degraded"

    # ── Public response (no key or wrong key) ───────────────────────────
    expected_key = getattr(settings, "METRICS_API_KEY", "")
    is_internal = bool(x_internal_key and x_internal_key == expected_key)

    if not is_internal:
        # Reveal only enough for a load-balancer / uptime probe
        return {"status": overall_status, "version": "1.0.0"}

    # ── Internal (authenticated) — full diagnostics ──────────────────────
    import stripe
    from app.middleware.rate_limiter_redis import redis_client

    results: dict = {
        "status": overall_status,
        "database": db_status,
        "version": "1.0.0",
    }

    # Redis check
    if settings.REDIS_ENABLED:
        try:
            if redis_client and redis_client.ping():
                results["redis"] = "ok"
            else:
                results["redis"] = "disconnected"
                results["status"] = "degraded"
        except Exception as e:
            logger.error("Health check - Redis failed: %s", e)
            results["redis"] = "error"
            results["status"] = "degraded"

    # Stripe check — asyncio-safe timeout via asyncio.wait_for
    if settings.STRIPE_ENABLED:
        stripe_status = "ok"

        def _call_stripe() -> None:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Balance.retrieve()

        try:
            # Run the synchronous Stripe call in a thread pool, with a 3-second timeout
            await asyncio.wait_for(asyncio.to_thread(_call_stripe), timeout=3.0)
        except asyncio.TimeoutError:
            logger.warning("Health check - Stripe timed out (3 s)")
            stripe_status = "timeout"
            results["status"] = "degraded"
        except Exception as exc:
            logger.error("Health check - Stripe failed: %s", exc)
            stripe_status = "error"
            results["status"] = "degraded"

        results["stripe"] = stripe_status

    return results

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette import status

metrics_api_key_header = APIKeyHeader(name="X-Metrics-Key", auto_error=False)

def verify_metrics_key(api_key: str = Depends(metrics_api_key_header)):
    """Dependency to verify the API key for Prometheus metrics."""
    # We can retrieve this from settings, or use a hardcoded value for now if it's missing.
    expected_key = getattr(settings, "METRICS_API_KEY", "dev-metrics-key")
    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Metrics-Key header",
        )

@app.get("/metrics", dependencies=[Depends(verify_metrics_key)])
def get_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    Requires X-Metrics-Key header matching METRICS_API_KEY setting.
    Access at http://localhost:8001/metrics
    """
    from prometheus_client import REGISTRY as prom_registry, generate_latest
    
    return generate_latest(REGISTRY).decode("utf-8")


# Initialize Prometheus instrumentation (after all routes are defined)
setup_prometheus(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
