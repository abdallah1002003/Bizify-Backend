from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession
from app.models.enums import ChatSessionType
from app.core.crud_utils import _utc_now, _to_update_dict
from app.core.structured_logging import get_logger
from app.services.base_service import BaseService

logger = get_logger(__name__)


class ChatSessionService(BaseService):
    """Refactored class-based access to chat sessions."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        from app.repositories.chat_repository import ChatSessionRepository
        self.repo = ChatSessionRepository(db)

    async def get_chat_session(self, id: UUID) -> Optional[ChatSession]:
        return await self.repo.get(id)

    async def get_chat_sessions(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[ChatSession]:
        return await self.repo.get_all(skip=skip, limit=limit, user_id=user_id)

    async def create_chat_session(self, user_id: UUID, session_type: ChatSessionType, business_id: Optional[UUID] = None, idea_id: Optional[UUID] = None) -> ChatSession:
        return await self.repo.create({
            "user_id": user_id,
            "session_type": session_type,
            "business_id": business_id,
            "idea_id": idea_id,
            "conversation_summary_json": {}
        })

    async def update_chat_session(self, db_obj: ChatSession, obj_in: Any) -> ChatSession:
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_chat_session(self, id: UUID) -> Optional[ChatSession]:
        return await self.repo.delete(id)
    
    async def get_chat_sessions_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        return await self.repo.get_all(skip=skip, limit=limit, user_id=user_id)

    def get_detailed_status(self) -> Dict[str, Any]:
        return {
            "module": "chat_session_operations",
            "status": "operational",
            "timestamp": _utc_now().isoformat(),
        }


# ----------------------------
# ChatSession CRUD Operations
# ----------------------------

async def get_chat_session(db: AsyncSession, id: UUID) -> Optional[ChatSession]:
    """Retrieve a chat session by ID."""
    from app.repositories.chat_repository import ChatSessionRepository
    return await ChatSessionRepository(db).get(id)


async def get_chat_sessions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatSession]:
    """Retrieve paginated chat sessions with optional user filtering."""
    from app.repositories.chat_repository import ChatSessionRepository
    return await ChatSessionRepository(db).get_all(skip=skip, limit=limit, user_id=user_id)


async def get_chat_sessions_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[ChatSession]:
    """Retrieve all chat sessions for a specific user with pagination."""
    from app.repositories.chat_repository import ChatSessionRepository
    return await ChatSessionRepository(db).get_for_user(user_id, skip=skip, limit=limit)


async def create_chat_session(
    db: AsyncSession,
    user_id: UUID,
    session_type: ChatSessionType,
    business_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
) -> ChatSession:
    """Create a new chat session for a user."""
    from app.repositories.chat_repository import ChatSessionRepository
    return await ChatSessionRepository(db).create({
        "user_id": user_id,
        "session_type": session_type,
        "business_id": business_id,
        "idea_id": idea_id,
        "conversation_summary_json": {}
    })


async def update_chat_session(db: AsyncSession, db_obj: ChatSession, obj_in: Any) -> ChatSession:
    """Update an existing chat session."""
    from app.repositories.chat_repository import ChatSessionRepository
    return await ChatSessionRepository(db).update(db_obj, obj_in)


async def delete_chat_session(db: AsyncSession, id: UUID) -> Optional[ChatSession]:
    """Delete a chat session and all associated messages."""
    from app.repositories.chat_repository import ChatSessionRepository
    return await ChatSessionRepository(db).delete(id)


async def get_detailed_status() -> Dict[str, Any]:
    """Get detailed status information for chat session operations."""
    return {
        "module": "chat_session_operations",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }
