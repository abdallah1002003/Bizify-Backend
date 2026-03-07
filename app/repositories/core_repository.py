"""
Repository for Core domain models:
  - File
  - Notification
  - ShareLink

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# Core services should delegate all persistence to this repository.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core.core import EmailMessage, File, Notification, ShareLink
from app.repositories.base_repository import GenericRepository


class FileRepository(GenericRepository[File]):
    """Repository for File model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, File)

    async def get_for_owner(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[File]:
        """Retrieve all files belonging to a specific owner."""
        stmt = (
            select(File)
            .where(File.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class NotificationRepository(GenericRepository[Notification]):
    """Repository for Notification model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Notification)

    async def get_for_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Notification]:
        """Retrieve all notifications for a user, newest first."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_for_user(self, user_id: UUID) -> List[Notification]:
        """Retrieve all unread notifications for a user."""
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ShareLinkRepository(GenericRepository[ShareLink]):
    """Repository for ShareLink model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ShareLink)

    async def get_by_token(self, token: str) -> Optional[ShareLink]:
        """Retrieve a share link by its unique token."""
        stmt = select(ShareLink).where(ShareLink.token == token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[ShareLink]:
        """Create a share link safely, returning None on IntegrityError (duplicate token)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def get_for_idea(self, idea_id: UUID) -> List[ShareLink]:
        """Retrieve all share links for a given idea."""
        stmt = select(ShareLink).where(ShareLink.idea_id == idea_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_business(self, business_id: UUID) -> List[ShareLink]:
        """Retrieve all share links for a given business."""
        stmt = select(ShareLink).where(ShareLink.business_id == business_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class EmailMessageRepository(GenericRepository[EmailMessage]):
    """Repository for EmailMessage model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, EmailMessage)

    async def get_pending_or_retrying(self, limit: int = 50) -> List[EmailMessage]:
        """Retrieve pending/retrying emails with an upper bound."""
        stmt = (
            select(EmailMessage)
            .where(EmailMessage.status.in_(["PENDING", "RETRYING"]))
            .order_by(EmailMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
