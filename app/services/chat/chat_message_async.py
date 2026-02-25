"""
Async ChatMessage operations using SQLAlchemy AsyncSession.

Mirrors chat_message_operations.py with non-blocking async equivalents.
Use these functions in async FastAPI routes with `get_async_db()`.

All sync variants in chat_message_operations.py remain unchanged
and can coexist with these async functions.
"""

from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage, ChatSession
from app.models.enums import ChatRole
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.structured_logging import get_logger

logger = get_logger(__name__)


async def get_chat_message_async(
    db: AsyncSession,
    id: UUID,
) -> Optional[ChatMessage]:
    """Retrieve a single chat message by ID (async).

    Args:
        db: AsyncSession
        id: ChatMessage UUID

    Returns:
        ChatMessage if found, None otherwise
    """
    stmt = select(ChatMessage).where(ChatMessage.id == id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def add_message_async(
    db: AsyncSession,
    session_id: UUID,
    role: ChatRole,
    content: str,
) -> ChatMessage:
    """Add a message to a chat session (async).

    Args:
        db: AsyncSession
        session_id: Parent ChatSession ID
        role: ChatRole.USER or ChatRole.AI
        content: Message text content

    Returns:
        Created ChatMessage object
    """
    db_obj = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    logger.info(
        "Added message (async)",
        extra={"message_id": str(db_obj.id), "session_id": str(session_id), "role": role.value},
    )
    return db_obj


async def get_session_history_async(
    db: AsyncSession,
    session_id: UUID,
    limit: int = 50,
) -> List[ChatMessage]:
    """Retrieve message history for a chat session (async).

    Args:
        db: AsyncSession
        session_id: ChatSession ID
        limit: Maximum messages to return

    Returns:
        List of ChatMessage objects ordered oldest-to-newest
    """
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_chat_message_async(
    db: AsyncSession,
    db_obj: ChatMessage,
    obj_in: Any,
) -> ChatMessage:
    """Update an existing chat message (async).

    Args:
        db: AsyncSession
        db_obj: Existing ChatMessage
        obj_in: Update data

    Returns:
        Updated ChatMessage
    """
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    logger.info("Updated chat message (async)", extra={"message_id": str(db_obj.id)})
    return db_obj


async def delete_chat_message_async(
    db: AsyncSession,
    id: UUID,
) -> Optional[ChatMessage]:
    """Delete a chat message (async).

    Args:
        db: AsyncSession
        id: ChatMessage ID to delete

    Returns:
        Deleted ChatMessage or None
    """
    db_obj = await get_chat_message_async(db, id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    logger.info("Deleted chat message (async)", extra={"message_id": str(id)})
    return db_obj
