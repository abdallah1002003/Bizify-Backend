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

# import central router
from app.api.api import api_router
from app.db.database import SessionLocal
from app.services.core.cleanup_service import cleanup_expired_tokens
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.VERIFY_DB_ON_STARTUP:
        verify_database_connection()
    if settings.AUTO_CREATE_TABLES and settings.APP_ENV != "production":
        Base.metadata.create_all(bind=engine)
    
    # Cleanup expired tokens on startup
    db = SessionLocal()
    try:
        cleaned = cleanup_expired_tokens(db)
        if cleaned:
            logger.info(f"Cleaned {cleaned} expired refresh tokens on startup")
    finally:
        db.close()
        
    yield

app = FastAPI(
    title="Bizify",
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
        "message": "Welcome to Bizify",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = "error"
    
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
