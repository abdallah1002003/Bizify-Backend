"""
Share Link CRUD operations and validation.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ShareLink
from app.services.base_service import BaseService
from app.core.crud_utils import _utc_now, _to_update_dict
from app.repositories.core_repository import ShareLinkRepository

logger = logging.getLogger(__name__)

def _is_expired(expires_at: datetime) -> bool:
    now = _utc_now()
    # SQLite commonly returns naive datetimes even for timezone-aware columns.
    if expires_at.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    return expires_at < now

class ShareLinkService(BaseService):
    """Service for managing ShareLink records."""
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
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
        all_links = await self.repo.get_all()
        if created_by is not None:
            filtered_links = [link for link in all_links if link.created_by == created_by]
            return filtered_links[skip:skip+limit]
        return all_links[skip:skip+limit]

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
            data = _to_update_dict(obj_in)
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
        """Update an existing share link."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

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

async def get_share_link_service(db: AsyncSession) -> ShareLinkService:
    """Dependency provider for ShareLinkService."""
    return ShareLinkService(db)
