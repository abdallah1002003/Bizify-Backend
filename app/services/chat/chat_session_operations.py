from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
<<<<<<< HEAD

from app.models import ChatSession
from app.models.enums import ChatSessionType
from app.core.crud_utils import _utc_now, _to_update_dict
from app.core.structured_logging import get_logger
from app.repositories.chat_repository import ChatSessionRepository
from app.services.base_service import BaseService
=======
from sqlalchemy import select

from app.models import ChatSession
from app.models.enums import ChatSessionType
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.structured_logging import get_logger
>>>>>>> origin/main

logger = get_logger(__name__)


<<<<<<< HEAD
class ChatSessionService(BaseService):
    """Service for ChatSession CRUD and session management operations."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = ChatSessionRepository(db)

    async def get_chat_session(self, id: UUID) -> Optional[ChatSession]:
        """Retrieve a chat session by ID."""
        return await self.repo.get(id)

    async def get_chat_sessions(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[ChatSession]:
        """Retrieve paginated chat sessions with optional user filtering."""
        if user_id is not None:
            return await self.repo.get_for_user(user_id, skip=skip, limit=limit)
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_chat_sessions_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ChatSession]:
        """Retrieve all chat sessions for a specific user with pagination."""
        return await self.repo.get_for_user(user_id, skip=skip, limit=limit)

    async def create_chat_session(
        self,
        user_id: UUID,
        session_type: ChatSessionType,
        business_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> ChatSession:
        """Create a new chat session for a user."""
        db_obj = await self.repo.create({
            "user_id": user_id,
            "session_type": session_type,
            "business_id": business_id,
            "idea_id": idea_id,
            "conversation_summary_json": {},
        })
        logger.info(f"Created chat session {db_obj.id} for user {user_id}, type={session_type}")
        return db_obj

    async def update_chat_session(self, db_obj: ChatSession, obj_in: Any) -> ChatSession:
        """Update an existing chat session."""
        updated = await self.repo.update(db_obj, _to_update_dict(obj_in))
        logger.info(f"Updated chat session {updated.id}")
        return updated

    async def delete_chat_session(self, id: UUID) -> Optional[ChatSession]:
        """Delete a chat session and all associated messages."""
        db_obj = await self.repo.get(id)
        if db_obj:
            deleted = await self.repo.delete(db_obj)
            logger.info(f"Deleted chat session {id}")
            return deleted
        return None

    def get_detailed_status(self) -> Dict[str, Any]:
        """Get status info for chat session operations."""
        return {
            "module": "chat_session_operations",
            "status": "operational",
            "timestamp": _utc_now().isoformat(),
        }



=======
# ----------------------------
# ChatSession CRUD Operations
# ----------------------------

async def get_chat_session(db: AsyncSession, id: UUID) -> Optional[ChatSession]:
    """Retrieve a chat session by ID."""
    stmt = select(ChatSession).where(ChatSession.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_chat_sessions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatSession]:
    """Retrieve paginated chat sessions with optional user filtering."""
    stmt = select(ChatSession)
    if user_id is not None:
        stmt = stmt.where(ChatSession.user_id == user_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_chat_sessions_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[ChatSession]:
    """Retrieve all chat sessions for a specific user with pagination."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_chat_session(
    db: AsyncSession,
    user_id: UUID,
    session_type: ChatSessionType,
    business_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
) -> ChatSession:
    """Create a new chat session for a user."""
    db_obj = ChatSession(
        user_id=user_id,
        session_type=session_type,
        business_id=business_id,
        idea_id=idea_id,
        conversation_summary_json={},
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    logger.info(f"Created chat session {db_obj.id} for user {user_id}, type={session_type}")
    return db_obj


async def update_chat_session(db: AsyncSession, db_obj: ChatSession, obj_in: Any) -> ChatSession:
    """Update an existing chat session."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    logger.info(f"Updated chat session {db_obj.id}")
    return db_obj


async def delete_chat_session(db: AsyncSession, id: UUID) -> Optional[ChatSession]:
    """Delete a chat session and all associated messages."""
    db_obj = await get_chat_session(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    logger.info(f"Deleted chat session {id}")
    return db_obj


async def get_detailed_status() -> Dict[str, Any]:
    """Get detailed status information for chat session operations."""
    return {
        "module": "chat_session_operations",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }
>>>>>>> origin/main
