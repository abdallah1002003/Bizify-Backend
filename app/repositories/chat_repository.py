"""
Repository for Chat domain models:
  - ChatSession
  - ChatMessage

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# Chat services should delegate all persistence to this repository.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat.chat import ChatSession, ChatMessage
from app.repositories.base_repository import GenericRepository


class ChatSessionRepository(GenericRepository[ChatSession]):
    """Repository for ChatSession model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ChatSession)

    async def get(self, id: UUID) -> Optional[ChatSession]:
        """Retrieve a chat session by ID."""
        stmt = select(ChatSession).where(ChatSession.id == id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_for_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ChatSession]:
        """Retrieve all chat sessions for a user, newest first."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[ChatSession]:
        if user_id:
            return await self.get_for_user(user_id, skip, limit)
        return await super().get_all(skip=skip, limit=limit)

    async def get_for_business(
        self, business_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ChatSession]:
        """Retrieve all chat sessions for a business."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.business_id == business_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_idea(
        self, idea_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ChatSession]:
        """Retrieve all chat sessions for an idea."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.idea_id == idea_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_with_count(self, user_id: UUID, skip: int = 0, limit: int = 100) -> tuple[List[ChatSession], int]:
        import asyncio
        data_stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        count_stmt = select(ChatSession).where(ChatSession.user_id == user_id).limit(10000)

        data_result, count_result = await asyncio.gather(
            self.db.execute(data_stmt),
            self.db.execute(count_stmt),
        )
        sessions = list(data_result.scalars().all())
        total = len(list(count_result.scalars().all()))
        return sessions, total


class ChatMessageRepository(GenericRepository[ChatMessage]):
    """Repository for ChatMessage model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ChatMessage)

    async def get(self, id: UUID) -> Optional[ChatMessage]:
        """Retrieve a chat message by ID."""
        stmt = select(ChatMessage).where(ChatMessage.id == id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_session_history(
        self,
        session_id: UUID,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Retrieve all messages in a session, ordered by creation time."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[ChatMessage]:
        if user_id:
            return await self.get_all_filtered(user_id, skip, limit)
        return await super().get_all(skip=skip, limit=limit)

    async def get_all_filtered(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(ChatSession.user_id == user_id)
            .offset(skip).limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
