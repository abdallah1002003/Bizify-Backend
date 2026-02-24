import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.db.database import Base, engine, verify_database_connection
from app import models as _models  # noqa: F401 - register models for metadata side effects
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.log_middleware import LogMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.rate_limiter_redis import RedisRateLimiterMiddleware
from config.settings import settings
from app.api.api import api_router
from app.db.database import SessionLocal
from app.services.core.cleanup_service import cleanup_all, cleanup_expired_tokens
from app.core.structured_logging import configure_structured_logging, get_logger
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



_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60  # 24 hours


async def _periodic_cleanup() -> None:
    """Background task: runs cleanup_all every 24 hours."""
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            summary = cleanup_all(db)
            logger.info("Periodic cleanup completed: %s", summary)
        except Exception:
            logger.exception("Periodic cleanup failed")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.VERIFY_DB_ON_STARTUP:
        verify_database_connection()
    if settings.AUTO_CREATE_TABLES and settings.APP_ENV != "production":
        Base.metadata.create_all(bind=engine)

    # One-shot cleanup on startup
    db = SessionLocal()
    try:
        summary = cleanup_all(db)
        if any(v > 0 for v in summary.values()):
            logger.info("Startup cleanup: %s", summary)
    finally:
        db.close()

    # Launch the 24-hour periodic cleanup task
    cleanup_task = asyncio.create_task(_periodic_cleanup())
    logger.info("Periodic cleanup task started (interval: %ds)", _CLEANUP_INTERVAL_SECONDS)

    yield

    # Gracefully cancel the background task on shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title=settings.APP_NAME,
    description="API for User Profiling and Idea Management",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS and "*" not in settings.cors_allowed_origins_list,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)

# Custom middleware - Order matters (first added = last executed)
if settings.REDIS_ENABLED:
    app.add_middleware(RedisRateLimiterMiddleware)
else:
    app.add_middleware(RateLimiterMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LogMiddleware)

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    """Root endpoint returning API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    from sqlalchemy import text
    import stripe
    from app.middleware.rate_limiter_redis import redis_client
    
    results = {
        "status": "ok",
        "database": "ok",
        "version": "1.0.0"
    }
    
    # 1. Database Check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check - Database failed: {e}")
        results["database"] = "error"
        results["status"] = "degraded"
        
    # 2. Redis Check
    if settings.REDIS_ENABLED:
        try:
            if redis_client and redis_client.ping():
                results["redis"] = "ok"
            else:
                results["redis"] = "disconnected"
                results["status"] = "degraded"
        except Exception as e:
            logger.error(f"Health check - Redis failed: {e}")
            results["redis"] = "error"
            results["status"] = "degraded"
    
    # 3. Stripe Check
    if settings.STRIPE_ENABLED:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            # Simple check to verify connectivity
            stripe.Balance.retrieve()
            results["stripe"] = "ok"
        except Exception as e:
            logger.error(f"Health check - Stripe failed: {e}")
            results["stripe"] = "error"
            results["status"] = "degraded"
            
    return results

# Initialize Prometheus instrumentation (after all routes are defined)
setup_prometheus(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
