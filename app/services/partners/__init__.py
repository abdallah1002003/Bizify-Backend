"""
Partner service module - refactored into modular components.
For backward compatibility, also imports from partner_service.
"""
# Import from individual modules
from app.services.partners import (
    partner_profile,
    partner_request,
)

# For backward compatibility, also import from main service
try:
    from .partner_service import *  # noqa: F403
except ImportError:
    pass

__all__ = [
    "partner_profile",
    "partner_request",
]
