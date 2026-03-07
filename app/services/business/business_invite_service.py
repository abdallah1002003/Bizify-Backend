from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.business.business_invite import BusinessInviteService


class BusinessInviteServiceFacade(BusinessInviteService):
    """Thin facade kept for backward compatibility. Now inherits from BusinessInviteService directly."""
    pass


