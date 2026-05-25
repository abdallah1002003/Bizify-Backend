from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai_pipeline,
    auth,
    billing,
    chat_sessions,
    export,
    groups,
    ideas,
    imports,
    marketplace,
    notifications,
    payment_methods,
    profile,
    settings,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Configuration"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(
    marketplace.router, prefix="/marketplace", tags=["Marketplace"]
)
api_router.include_router(profile.router, prefix="/profile", tags=["User Profiling"])

api_router.include_router(ideas.router, prefix="/ideas", tags=["Ideas"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
api_router.include_router(settings.router, prefix="/settings", tags=["User Settings"])
api_router.include_router(imports.router, prefix="/import", tags=["Import"])
api_router.include_router(groups.router, tags=["Teams"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(payment_methods.router, prefix="/payment-methods", tags=["Payment Methods"])
api_router.include_router(ai_pipeline.router, prefix="/ai")
api_router.include_router(ai_pipeline._system_router, prefix="/ai")
api_router.include_router(chat_sessions.router, prefix="/chat", tags=["Chat Sessions"])
