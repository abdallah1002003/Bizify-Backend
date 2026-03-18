import uvicorn
from fastapi import FastAPI

from app.api.api import api_router
from app.core.config import settings


app = FastAPI(
    title = settings.PROJECT_NAME,
    description = "Bizify",
    version = "1.0.0"
)

app.include_router(api_router, prefix = "/api/v1")


@app.get("/")
async def root() -> dict:
    """
    Root endpoint to verify API connectivity.
    """
    return {"message": "Hello World!"}


@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint to verify service status.
    """
    return {"status": "healthy", "project_name": settings.PROJECT_NAME}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host = "0.0.0.0", port = 8000, reload = True)