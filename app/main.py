from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.api import api_router
from app.core.config import settings
from app.core.database import engine, ensure_sqlite_compatibility_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Apply local SQLite compatibility fixes and test DB connection before handling requests."""
    ensure_sqlite_compatibility_schema()
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(" Database connected successfully!")
    except Exception as e:
        print(f" Database connection failed: {e}")
        import sys
        if "pytest" not in sys.modules:
            raise RuntimeError("Database connection failed. Aborting startup.")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Bizify",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")





@app.get("/")
async def root() -> dict[str, str]:
    """Return a simple connectivity response."""
    return {"message": "Hello World!"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return the service health status."""
    return {"status": "healthy", "project_name": settings.PROJECT_NAME}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
