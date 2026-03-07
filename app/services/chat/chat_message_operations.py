from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.models.enums import ChatRole
from app.core.crud_utils import _utc_now, _to_update_dict
from app.core.structured_logging import get_logger
from app.services.base_service import BaseService
from app.repositories.chat_repository import ChatMessageRepository

logger = get_logger(__name__)


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



