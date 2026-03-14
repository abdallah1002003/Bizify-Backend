from fastapi import FastAPI
from app.core.config import settings
from app.api.api import api_router
import uvicorn



app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Bizify API with FastAPI and SQLAlchemy",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "project_name": settings.PROJECT_NAME}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)