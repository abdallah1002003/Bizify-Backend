"""
Core service module - refactored into modular components.
For backward compatibility, also imports from core_service.
"""
# Import from individual modules
from app.services.core import (
    file_service,
    notification_service,
    share_link_service,
)

# For backward compatibility, also import from main services
try:
    from .core_service import *  # noqa: F403
except ImportError:
    pass

__all__ = [
    "file_service",
    "share_link_service",
    "notification_service",
]
