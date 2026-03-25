from fastapi import APIRouter

from app.api.v1 import (
    admin, 
    auth, 
    guidance, 
    ideas, 
    notifications,
    profile, 
    users,
    export,
    settings,
    imports,
    groups
)


api_router = APIRouter()

api_router.include_router(auth.router, prefix = "/auth", tags = ["Authentication"])
api_router.include_router(admin.router, prefix = "/admin", tags = ["Admin Configuration"])
api_router.include_router(users.router, prefix = "/users", tags = ["User Management"])
api_router.include_router(profile.router, prefix = "/profile", tags = ["User Profiling"])
api_router.include_router(guidance.router, prefix = "/guidance", tags = ["Business Guidance"])
api_router.include_router(ideas.router, prefix = "/ideas", tags = ["Ideas"])
api_router.include_router(notifications.router, prefix = "/notifications", tags = ["Notifications"])
api_router.include_router(export.router, prefix = "/export", tags = ["Export"])
api_router.include_router(settings.router, prefix = "/settings", tags = ["User Settings"])
api_router.include_router(imports.router, prefix="/import", tags=["Import"])
api_router.include_router(groups.router, tags=["Teams"])
