from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
<<<<<<< HEAD

from app.models import ChatMessage
from app.models.enums import ChatRole
from app.core.crud_utils import _utc_now, _to_update_dict
from app.core.structured_logging import get_logger
from app.services.base_service import BaseService
from app.repositories.chat_repository import ChatMessageRepository
=======
from sqlalchemy import select

from app.models import ChatMessage, ChatSession
from app.models.enums import ChatRole
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.structured_logging import get_logger
>>>>>>> origin/main

logger = get_logger(__name__)


<<<<<<< HEAD
class ChatMessageService(BaseService):
    """Service for ChatMessage CRUD and session history operations."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = ChatMessageRepository(db)

    async def get_chat_message(self, id: UUID) -> Optional[ChatMessage]:
        """Retrieve a single chat message by ID."""
        return await self.repo.get(id)

    async def get_chat_messages(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[ChatMessage]:
        """Retrieve paginated chat messages with optional user filtering."""
        if user_id is not None:
            return await self.repo.get_all_filtered(user_id=user_id, skip=skip, limit=limit)
        return await self.repo.get_all(skip=skip, limit=limit)

    async def add_message(self, session_id: UUID, role: ChatRole, content: str) -> ChatMessage:
        """Add a message to a chat session."""
        db_obj = await self.repo.create({
            "session_id": session_id,
            "role": role,
            "content": content
        })
        logger.info(f"Added message {db_obj.id} to session {session_id}, role={role}")
        return db_obj

    async def update_chat_message(self, db_obj: ChatMessage, obj_in: Any) -> ChatMessage:
        """Update an existing chat message."""
        updated = await self.repo.update(db_obj, _to_update_dict(obj_in))
        logger.info(f"Updated chat message {updated.id}")
        return updated

    async def delete_chat_message(self, id: UUID) -> Optional[ChatMessage]:
        """Delete a chat message from a session."""
        db_obj = await self.get_chat_message(id)
        if db_obj:
            deleted = await self.repo.delete(db_obj)
            logger.info(f"Deleted chat message {id}")
            return deleted
        return None

    async def get_session_history(self, session_id: UUID, limit: int = 50) -> List[ChatMessage]:
        """Retrieve the message history for a chat session."""
        return await self.repo.get_for_session(session_id, limit=limit)

    def get_detailed_status(self) -> Dict[str, Any]:
        """Get status info for chat message operations."""
        return {
            "module": "chat_message_operations",
            "status": "operational",
            "timestamp": _utc_now().isoformat(),
        }



=======
# ----------------------------
# ChatMessage CRUD Operations
# ----------------------------

async def get_chat_message(db: AsyncSession, id: UUID) -> Optional[ChatMessage]:
    """Retrieve a single chat message by ID."""
    stmt = select(ChatMessage).where(ChatMessage.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_chat_messages(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatMessage]:
    """Retrieve paginated chat messages with optional user filtering."""
    stmt = select(ChatMessage)
    if user_id is not None:
        stmt = (
            stmt
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(ChatSession.user_id == user_id)
        )
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession,
    session_id: UUID,
    role: ChatRole,
    content: str,
) -> ChatMessage:
    """Add a message to a chat session."""
    db_obj = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    logger.info(f"Added message {db_obj.id} to session {session_id}, role={role}")
    return db_obj


async def update_chat_message(
    db: AsyncSession,
    db_obj: ChatMessage,
    obj_in: Any,
) -> ChatMessage:
    """Update an existing chat message."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    logger.info(f"Updated chat message {db_obj.id}")
    return db_obj


async def delete_chat_message(db: AsyncSession, id: UUID) -> Optional[ChatMessage]:
    """Delete a chat message from a session."""
    db_obj = await get_chat_message(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    logger.info(f"Deleted chat message {id}")
    return db_obj


# ----------------------------
# Session History Operations
# ----------------------------

async def get_session_history(
    db: AsyncSession,
    session_id: UUID,
    limit: int = 50,
) -> List[ChatMessage]:
    """Retrieve the message history for a chat session."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_detailed_status() -> Dict[str, Any]:
    """Get detailed status information for chat message operations."""
    return {
        "module": "chat_message_operations",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }
>>>>>>> origin/main
