import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.db.database import Base, engine, verify_database_connection
import app.models  # Register all models for create_all
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.log_middleware import LogMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.session_activity import SessionActivityMiddleware
from config.settings import settings

# import central router
from app.api.api import api_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.VERIFY_DB_ON_STARTUP:
        verify_database_connection()
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
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

# Custom middleware
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(SessionActivityMiddleware)
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
