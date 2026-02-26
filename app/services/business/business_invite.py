from __future__ import annotations

from datetime import timedelta
import logging
import secrets
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import BusinessInvite, BusinessInviteIdea, User
from app.models.enums import CollaboratorRole, InviteStatus
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# BusinessInvite
# ----------------------------

async def get_invite(db: AsyncSession, id: UUID) -> Optional[BusinessInvite]:
    """Return a single business invite by id."""
    stmt = select(BusinessInvite).where(BusinessInvite.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_business_invite(db: AsyncSession, id: UUID) -> Optional[BusinessInvite]:
    """Alias for get_invite."""
    return await get_invite(db, id=id)


async def get_invites(db: AsyncSession, business_id: UUID) -> List[BusinessInvite]:
    """Retrieve all invites for a specific business."""
    stmt = select(BusinessInvite).where(BusinessInvite.business_id == business_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_business_invites(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[BusinessInvite]:
    """Retrieve paginated business invites."""
    stmt = select(BusinessInvite).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_invite(db: AsyncSession, business_id: UUID, email: str, invited_by: UUID) -> BusinessInvite:
    """Create a new business invite."""
    db_obj = BusinessInvite(
        business_id=business_id,
        email=email,
        token=secrets.token_urlsafe(32),
        status=InviteStatus.PENDING,
        invited_by=invited_by,
        expires_at=_utc_now() + timedelta(days=7),
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def create_business_invite(db: AsyncSession, obj_in: Any) -> BusinessInvite:
    """Create a business invite from a schema object."""
    data = _to_update_dict(obj_in)
    data.setdefault("expires_at", _utc_now() + timedelta(days=7))
    db_obj = BusinessInvite(**data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_business_invite(db: AsyncSession, db_obj: BusinessInvite, obj_in: Any) -> BusinessInvite:
    """Update a business invite and handle acceptance logic."""
    
    before = db_obj.status
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    if before != InviteStatus.ACCEPTED and db_obj.status == InviteStatus.ACCEPTED:
        # Check if user already exists to auto-add as collaborator
        stmt = select(User).where(User.email == db_obj.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is not None:
            # Note: business_collaborator.add_collaborator is expected to be async
            # We need to ensure we can get an instance or call it correctly.
            # For now assuming it is refactored to take AsyncSession.
            from app.services.business.business_collaborator import BusinessCollaboratorService
            collab_service = BusinessCollaboratorService(db)
            await collab_service.add_collaborator(db_obj.business_id, user.id, CollaboratorRole.VIEWER)

    return db_obj


async def delete_business_invite(db: AsyncSession, id: UUID) -> Optional[BusinessInvite]:
    """Delete a business invite by id."""
    db_obj = await get_business_invite(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    return db_obj


async def accept_invite(db: AsyncSession, token: str, user_id: UUID) -> bool:
    """Accept an invite given its token and the user's ID."""
    stmt = select(BusinessInvite).where(BusinessInvite.token == token)
    result = await db.execute(stmt)
    invite = result.scalar_one_or_none()
    
    if invite is None:
        return False

    if invite.status != InviteStatus.PENDING:
        return False

    if invite.expires_at < _utc_now():
        invite.status = InviteStatus.EXPIRED
        await db.commit()
        return False

    invite.status = InviteStatus.ACCEPTED
    await db.commit()
    
    from app.services.business.business_collaborator import BusinessCollaboratorService
    collab_service = BusinessCollaboratorService(db)
    await collab_service.add_collaborator(invite.business_id, user_id, CollaboratorRole.EDITOR)
    return True


# ----------------------------
# BusinessInviteIdea
# ----------------------------

async def get_business_invite_idea(db: AsyncSession, id: UUID) -> Optional[BusinessInviteIdea]:
    """Retrieve a single business invite idea by id."""
    stmt = select(BusinessInviteIdea).where(BusinessInviteIdea.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_business_invite_ideas(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[BusinessInviteIdea]:
    """Retrieve paginated business invite ideas."""
    stmt = select(BusinessInviteIdea).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_business_invite_idea(db: AsyncSession, obj_in: Any) -> BusinessInviteIdea:
    """Create a new business invite idea."""
    db_obj = BusinessInviteIdea(**_to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_business_invite_idea(db: AsyncSession, db_obj: BusinessInviteIdea, obj_in: Any) -> BusinessInviteIdea:
    """Update an existing business invite idea."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_business_invite_idea(db: AsyncSession, id: UUID) -> Optional[BusinessInviteIdea]:
    """Delete a business invite idea by id."""
    db_obj = await get_business_invite_idea(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    return db_obj
