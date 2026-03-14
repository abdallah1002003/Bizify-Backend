from fastapi import APIRouter
from app.api.v1 import users, auth,admin, profile, teams



api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(profile.router, prefix="/profile", tags=["User Profiling"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])

