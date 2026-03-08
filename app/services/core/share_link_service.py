from __future__ import annotations
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ShareLink
from app.services.base_service import BaseService
from app.db.database import get_async_db
from app.core.crud_utils import _utc_now
from app.repositories.core_repository import ShareLinkRepository

logger = logging.getLogger(__name__)

def _is_expired(expires_at: datetime) -> bool:
    now = _utc_now()
    if expires_at.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    return expires_at < now

class ShareLinkService(BaseService):
    """Service for managing ShareLink records."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = ShareLinkRepository(db)

    async def get_share_link(self, id: UUID) -> Optional[ShareLink]:
        """Retrieve a share link by ID."""
        return await self.repo.get(id)

    async def get_share_links(
        self,
        skip: int = 0,
        limit: int = 100,
        created_by: Optional[UUID] = None,
    ) -> List[ShareLink]:
        """Retrieve multiple share links with optional creator filtering."""
        # Note: repository doesn't have get_for_creator, but get_all supports user_id if we override it, 
        # but here we use base get_all and filter if needed. 
        # Actually, let's just use the base repo's get_all for now and if needed we'll add custom method.
        # But wait, share_link has created_by, not user_id.
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_share_link(
        self,
        obj_in: Any = None,
        business_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
        creator_id: Optional[UUID] = None,
        expires_in_days: int = 7,
    ) -> ShareLink:
        """Create a new share link record."""
        if obj_in is not None:
            if isinstance(obj_in, dict):
                data = obj_in
            elif hasattr(obj_in, "model_dump"):
                data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, "dict"):
                data = obj_in.dict(exclude_unset=True)
            else:
                data = dict(obj_in)
        else:
            data = {
                "business_id": business_id,
                "idea_id": idea_id,
                "created_by": creator_id,
                "token": secrets.token_urlsafe(32),
                "is_public": False,
                "expires_at": _utc_now() + timedelta(days=expires_in_days),
            }

        if not data.get("token"):
            data["token"] = secrets.token_urlsafe(32)

        return await self.repo.create(data)

    async def update_share_link(self, db_obj: ShareLink, obj_in: Any) -> ShareLink:
        """Update an existing share link record."""
        return await self.repo.update(db_obj, obj_in)

    async def delete_share_link(self, id: UUID) -> Optional[ShareLink]:
        """Delete a share link record."""
        return await self.repo.delete(id)

    async def validate_share_link(self, token: str) -> Optional[ShareLink]:
        """Validate a share link token."""
        link = await self.repo.get_by_token(token)
        
        if link is None:
            return None

        if link.expires_at is not None and _is_expired(link.expires_at):
            return None

        return link

async def get_share_link_service(db: AsyncSession = Depends(get_async_db)) -> ShareLinkService:
    """Dependency provider for ShareLinkService."""
    return ShareLinkService(db)

# ----------------------------
# Legacy Async Aliases
# ----------------------------

async def get_share_link(db: AsyncSession, id: UUID) -> Optional[ShareLink]:
    return await ShareLinkService(db).get_share_link(id)

async def get_share_links(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    created_by: Optional[UUID] = None,
) -> List[ShareLink]:
    return await ShareLinkService(db).get_share_links(skip, limit, created_by)

async def create_share_link(
    db: AsyncSession,
    obj_in: Any = None,
    business_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
    creator_id: Optional[UUID] = None,
    expires_in_days: int = 7,
) -> ShareLink:
    return await ShareLinkService(db).create_share_link(obj_in, business_id, idea_id, creator_id, expires_in_days)

async def update_share_link(db: AsyncSession, db_obj: ShareLink, obj_in: Any) -> ShareLink:
    return await ShareLinkService(db).update_share_link(db_obj, obj_in)

async def delete_share_link(db: AsyncSession, id: UUID) -> Optional[ShareLink]:
    return await ShareLinkService(db).delete_share_link(id)

async def validate_share_link(db: AsyncSession, token: str) -> Optional[ShareLink]:
    return await ShareLinkService(db).validate_share_link(token)
