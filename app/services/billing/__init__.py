"""
Billing service module - refactored into modular components.
For backward compatibility, also imports from billing_service.
"""
# Import from individual modules
from app.services.billing import (
    payment_method,
    payment_service,
    plan_service,
    subscription_service,
    usage_service,
)

# For backward compatibility, also import from main service
try:
    from .billing_service import *  # noqa: F403
except ImportError:
    pass

__all__ = [
    "usage_service",
    "plan_service",
    "subscription_service",
    "payment_method",
    "payment_service",
]
