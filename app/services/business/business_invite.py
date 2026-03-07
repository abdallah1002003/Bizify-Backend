from __future__ import annotations

from datetime import timedelta
import logging
import secrets
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
<<<<<<< HEAD

from app.models import BusinessInvite, BusinessInviteIdea, User
from app.models.enums import CollaboratorRole, InviteStatus
from app.core.crud_utils import _utc_now, _to_update_dict
from app.services.base_service import BaseService
from app.repositories.business_repository import BusinessInviteRepository, BusinessInviteIdeaRepository
from app.repositories.user_repository import UserRepository
=======
from sqlalchemy import select

from app.models import BusinessInvite, BusinessInviteIdea, User
from app.models.enums import CollaboratorRole, InviteStatus
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
>>>>>>> origin/main

logger = logging.getLogger(__name__)


<<<<<<< HEAD
class BusinessInviteService(BaseService):
    """Service for managing Business Invites and BusinessInviteIdeas."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.invite_repo = BusinessInviteRepository(db)
        self.user_repo = UserRepository(db, User)
        self.invite_idea_repo = BusinessInviteIdeaRepository(db)

    # ----------------------------
    # BusinessInvite
    # ----------------------------

    async def get_invite(self, id: UUID) -> Optional[BusinessInvite]:
        """Return a single business invite by id."""
        return await self.invite_repo.get(id)

    async def get_business_invite(self, id: UUID) -> Optional[BusinessInvite]:
        """Alias for get_invite."""
        return await self.invite_repo.get(id)

    async def get_invites(self, business_id: UUID) -> List[BusinessInvite]:
        """Retrieve all invites for a specific business."""
        return await self.invite_repo.get_for_business(business_id)

    async def get_business_invites(self, skip: int = 0, limit: int = 100) -> List[BusinessInvite]:
        """Retrieve paginated business invites."""
        return await self.invite_repo.get_all(skip=skip, limit=limit)

    async def create_invite(self, business_id: UUID, email: str, invited_by: UUID) -> BusinessInvite:
        """Create a new business invite."""
        return await self.invite_repo.create({
            "business_id": business_id,
            "email": email,
            "token": secrets.token_urlsafe(32),
            "status": InviteStatus.PENDING,
            "invited_by": invited_by,
            "expires_at": _utc_now() + timedelta(days=7),
        })

    async def create_business_invite(self, obj_in: Any) -> BusinessInvite:
        """Create a business invite from a schema object."""
        data = _to_update_dict(obj_in)
        data.setdefault("expires_at", _utc_now() + timedelta(days=7))
        if "token" not in data:
            data["token"] = secrets.token_urlsafe(32)
        return await self.invite_repo.create(data)

    async def update_business_invite(self, db_obj: BusinessInvite, obj_in: Any) -> BusinessInvite:
        """Update a business invite and handle acceptance logic."""
        before = db_obj.status
        updated = await self.invite_repo.update(db_obj, obj_in)

        if before != InviteStatus.ACCEPTED and updated.status == InviteStatus.ACCEPTED:
            user = await self.user_repo.get_by_email(updated.email)
            if user is not None:
                from app.services.business.business_collaborator import BusinessCollaboratorService
                collab_service = BusinessCollaboratorService(self.db)
                await collab_service.add_collaborator(updated.business_id, user.id, CollaboratorRole.VIEWER)

        return updated

    async def delete_business_invite(self, id: UUID) -> Optional[BusinessInvite]:
        """Delete a business invite by id."""
        db_obj = await self.get_business_invite(id)
        if db_obj:
            return await self.invite_repo.delete(db_obj)
        return None

    async def accept_invite(self, token: str, user_id: UUID) -> bool:
        """Accept an invite given its token and the user's ID."""
        invite = await self.invite_repo.get_by_token(token)

        if invite is None:
            return False
        if invite.status != InviteStatus.PENDING:
            return False
        if invite.expires_at < _utc_now():
            await self.invite_repo.update(invite, {"status": InviteStatus.EXPIRED})
            return False

        await self.invite_repo.update(invite, {"status": InviteStatus.ACCEPTED})

        from app.services.business.business_collaborator import BusinessCollaboratorService
        collab_service = BusinessCollaboratorService(self.db)
        await collab_service.add_collaborator(invite.business_id, user_id, CollaboratorRole.EDITOR)
        return True

    # ----------------------------
    # BusinessInviteIdea
    # ----------------------------

    async def get_business_invite_idea(self, id: UUID) -> Optional[BusinessInviteIdea]:
        """Retrieve a single business invite idea by id."""
        return await self.invite_idea_repo.get(id)

    async def get_business_invite_ideas(self, skip: int = 0, limit: int = 100) -> List[BusinessInviteIdea]:
        """Retrieve paginated business invite ideas."""
        return await self.invite_idea_repo.get_all(skip=skip, limit=limit)

    async def create_business_invite_idea(self, obj_in: Any) -> BusinessInviteIdea:
        """Create a new business invite idea."""
        return await self.invite_idea_repo.create(_to_update_dict(obj_in))

    async def update_business_invite_idea(self, db_obj: BusinessInviteIdea, obj_in: Any) -> BusinessInviteIdea:
        """Update an existing business invite idea."""
        return await self.invite_idea_repo.update(db_obj, obj_in)

    async def delete_business_invite_idea(self, id: UUID) -> Optional[BusinessInviteIdea]:
        """Delete a business invite idea by id."""
        db_obj = await self.get_business_invite_idea(id)
        if db_obj:
            return await self.invite_idea_repo.delete(db_obj)
        return None


=======
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
>>>>>>> origin/main
