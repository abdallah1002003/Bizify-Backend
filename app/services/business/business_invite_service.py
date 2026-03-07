from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.business import business_invite


async def create_business_invite(db: AsyncSession, obj_in):
    """Async wrapper for create_business_invite."""
    return await business_invite.create_business_invite(db, obj_in=obj_in)


async def update_business_invite(db: AsyncSession, db_obj, obj_in):
    """Async wrapper for update_business_invite."""
    return await business_invite.update_business_invite(db, db_obj=db_obj, obj_in=obj_in)
