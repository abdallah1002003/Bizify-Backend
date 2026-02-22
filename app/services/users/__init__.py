"""
User service module - refactored into modular components.
For backward compatibility, also imports from user_service.
"""
# Import from individual modules
from app.services.users import (
    admin_log_service,
    user_core,
    user_profile,
)

# For backward compatibility, also import from main service
try:
    from .user_service import *  # noqa: F403
except ImportError:
    pass

__all__ = [
    "user_core",
    "user_profile",
    "admin_log_service",
]
