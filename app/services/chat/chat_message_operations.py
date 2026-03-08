from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.models.enums import ChatRole
from app.core.crud_utils import _utc_now, _to_update_dict
from app.core.structured_logging import get_logger
from app.services.base_service import BaseService

logger = get_logger(__name__)


class ChatMessageService(BaseService):
    """Refactored class-based access to chat messages."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        from app.repositories.chat_repository import ChatMessageRepository
        self.repo = ChatMessageRepository(db)

    async def get_chat_message(self, id: UUID) -> Optional[ChatMessage]:
        return await self.repo.get(id)

    async def get_chat_messages(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[ChatMessage]:
        return await self.repo.get_all(skip=skip, limit=limit, user_id=user_id)

    async def add_message(self, session_id: UUID, role: ChatRole, content: str) -> ChatMessage:
        return await self.repo.create({"session_id": session_id, "role": role, "content": content})

    async def update_chat_message(self, db_obj: ChatMessage, obj_in: Any) -> ChatMessage:
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_chat_message(self, id: UUID) -> Optional[ChatMessage]:
        return await self.repo.delete(id)

    async def get_session_history(self, session_id: UUID, limit: int = 50) -> List[ChatMessage]:
        return await self.repo.get_session_history(session_id, limit)

    def get_detailed_status(self) -> Dict[str, Any]:
        return {
            "module": "chat_message_operations",
            "status": "operational",
            "timestamp": _utc_now().isoformat(),
        }


# ----------------------------
# ChatMessage CRUD Operations
# ----------------------------

async def get_chat_message(db: AsyncSession, id: UUID) -> Optional[ChatMessage]:
    """Retrieve a single chat message by ID."""
    from app.repositories.chat_repository import ChatMessageRepository
    return await ChatMessageRepository(db).get(id)


async def get_chat_messages(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatMessage]:
    """Retrieve paginated chat messages with optional user filtering."""
    from app.repositories.chat_repository import ChatMessageRepository
    return await ChatMessageRepository(db).get_all(skip=skip, limit=limit, user_id=user_id)


async def add_message(
    db: AsyncSession,
    session_id: UUID,
    role: ChatRole,
    content: str,
) -> ChatMessage:
    """Add a message to a chat session."""
    from app.repositories.chat_repository import ChatMessageRepository
    return await ChatMessageRepository(db).create({"session_id": session_id, "role": role, "content": content})


async def update_chat_message(
    db: AsyncSession,
    db_obj: ChatMessage,
    obj_in: Any,
) -> ChatMessage:
    """Update an existing chat message."""
    from app.repositories.chat_repository import ChatMessageRepository
    return await ChatMessageRepository(db).update(db_obj, obj_in)


async def delete_chat_message(db: AsyncSession, id: UUID) -> Optional[ChatMessage]:
    """Delete a chat message from a session."""
    from app.repositories.chat_repository import ChatMessageRepository
    return await ChatMessageRepository(db).delete(id)


async def get_session_history(
    db: AsyncSession,
    session_id: UUID,
    limit: int = 50,
) -> List[ChatMessage]:
    """Retrieve the message history for a chat session."""
    from app.repositories.chat_repository import ChatMessageRepository
    return await ChatMessageRepository(db).get_session_history(session_id, limit)


async def get_detailed_status() -> Dict[str, Any]:
    """Get detailed status information for chat message operations."""
    return {
        "module": "chat_message_operations",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }
