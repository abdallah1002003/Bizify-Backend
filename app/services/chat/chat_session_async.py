"""
Async ChatSession operations using SQLAlchemy AsyncSession.

Mirrors chat_session_operations.py with non-blocking async equivalents.
Use these functions in async FastAPI routes with `get_async_db()`.

All sync variants in chat_session_operations.py remain unchanged
and can coexist with these async functions.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession
from app.models.enums import ChatSessionType
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.structured_logging import get_logger

logger = get_logger(__name__)


async def get_chat_session_async(
    db: AsyncSession,
    id: UUID,
) -> Optional[ChatSession]:
    """Retrieve a chat session by ID (async).

    Args:
        db: AsyncSession from get_async_db()
        id: ChatSession UUID

    Returns:
        ChatSession if found, None otherwise
    """
    stmt = select(ChatSession).where(ChatSession.id == id)
    result = await db.execute(stmt)
    return result.scalars().first()  # type: ignore[no-any-return]


async def get_chat_sessions_by_user_async(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[ChatSession], int]:
    """Retrieve paginated sessions for a user with total count (async).

    Executes both the data query and the count query concurrently using
    asyncio.gather for reduced latency.

    Args:
        db: AsyncSession
        user_id: Owner user ID
        skip: Pagination offset
        limit: Pagination limit

    Returns:
        Tuple of (sessions list, total count)
    """
    import asyncio

    data_stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    count_stmt = select(ChatSession).where(ChatSession.user_id == user_id)

    data_result, count_result = await asyncio.gather(
        db.execute(data_stmt),
        db.execute(count_stmt),
    )

    sessions = list(data_result.scalars().all())
    total = len(list(count_result.scalars().all()))
    return sessions, total


async def create_chat_session_async(
    db: AsyncSession,
    user_id: UUID,
    session_type: ChatSessionType,
    business_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
) -> ChatSession:
    """Create a new chat session (async).

    Args:
        db: AsyncSession
        user_id: Owning user UUID
        session_type: ChatSessionType enum value
        business_id: Optional linked business ID
        idea_id: Optional linked idea ID

    Returns:
        Persisted ChatSession with generated ID
    """
    db_obj = ChatSession(
        user_id=user_id,
        session_type=session_type,
        business_id=business_id,
        idea_id=idea_id,
        conversation_summary_json={},
    )
    db.add(db_obj)
    await db.flush()   # Obtain ID before commit
    await db.commit()
    await db.refresh(db_obj)
    logger.info(
        "Created chat session (async)",
        extra={"session_id": str(db_obj.id), "user_id": str(user_id)},
    )
    return db_obj


async def update_chat_session_async(
    db: AsyncSession,
    db_obj: ChatSession,
    obj_in: Any,
) -> ChatSession:
    """Partially update a chat session (async).

    Args:
        db: AsyncSession
        db_obj: Existing ChatSession to update
        obj_in: Dict, Pydantic model, or object with update data

    Returns:
        Updated ChatSession
    """
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    logger.info("Updated chat session (async)", extra={"session_id": str(db_obj.id)})
    return db_obj


async def delete_chat_session_async(
    db: AsyncSession,
    id: UUID,
) -> Optional[ChatSession]:
    """Delete a chat session and its messages (async).

    Args:
        db: AsyncSession
        id: ChatSession UUID to delete

    Returns:
        Deleted ChatSession or None if not found
    """
    db_obj = await get_chat_session_async(db, id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    logger.info("Deleted chat session (async)", extra={"session_id": str(id)})
    return db_obj
