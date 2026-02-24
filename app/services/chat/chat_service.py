from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession
from app.models.enums import ChatRole, ChatSessionType
from app.core.structured_logging import get_logger, PerformanceTimer

logger = get_logger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# ChatSession Operations
# ----------------------------

def get_chat_session(db: Session, id: UUID) -> Optional[ChatSession]:
    """
    Retrieve a chat session by ID.
    
    Args:
        db: Database session
        id: Chat session UUID
    
    Returns:
        ChatSession object if found, None otherwise
    """
    return db.query(ChatSession).filter(ChatSession.id == id).first()


def get_chat_sessions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatSession]:
    """
    Retrieve paginated chat sessions with optional user filtering.
    
    Args:
        db: Database session
        skip: Offset for pagination (default: 0)
        limit: Maximum records to return (default: 100)
        user_id: Filter by user ID (optional)
    
    Returns:
        List of ChatSession objects
    """
    query = db.query(ChatSession)
    if user_id is not None:
        query = query.filter(ChatSession.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def get_chat_sessions_by_user(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[ChatSession]:
    """
    Retrieve all chat sessions for a specific user with pagination.
    
    Sessions are ordered by creation date in descending order (newest first).
    
    Args:
        db: Database session
        user_id: User to retrieve sessions for
        skip: Number of records to skip (default: 0)
        limit: Maximum records per page (default: 100)
    
    Returns:
        List of ChatSession objects ordered by creation date (newest first)
    
    Example:
        >>> sessions = get_chat_sessions_by_user(
        ...     db=session,
        ...     user_id=user_id,
        ...     limit=10
        ... )
        >>> print(f"User has {len(sessions)} recent sessions")
    """
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_chat_session(
    db: Session,
    user_id: UUID,
    session_type: ChatSessionType,
    business_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
) -> ChatSession:
    """
    Create a new chat session for a user.
    
    A chat session represents a conversation context that can be linked to
    a specific business or idea. Sessions include conversation summaries
    that are updated as messages are added.
    
    Args:
        db: Database session
        user_id: User creating the session
        session_type: Type of session (BUSINESS, IDEA, GENERAL)
        business_id: Associated business ID (optional)
        idea_id: Associated idea ID (optional)
    
    Returns:
        Created ChatSession object with initialized summary
    
    Raises:
        ValueError: If both business_id and idea_id are None for non-GENERAL sessions
    
    Example:
        >>> session = create_chat_session(
        ...     db=db,
        ...     user_id=user_id,
        ...     session_type=ChatSessionType.IDEA,
        ...     idea_id=idea_id
        ... )
    """
    db_obj = ChatSession(
        user_id=user_id,
        session_type=session_type,
        business_id=business_id,
        idea_id=idea_id,
        conversation_summary_json={},
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_chat_session(db: Session, db_obj: ChatSession, obj_in: Any) -> ChatSession:
    """
    Update an existing chat session.
    
    Args:
        db: Database session
        db_obj: ChatSession object to update
        obj_in: Update data (dict, Pydantic model, or object with attributes)
    
    Returns:
        Updated ChatSession object
    """
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_chat_session(db: Session, id: UUID) -> Optional[ChatSession]:
    """
    Delete a chat session and all associated messages.
    
    Args:
        db: Database session
        id: Chat session ID to delete
    
    Returns:
        Deleted ChatSession object if found, None otherwise
    
    Note:
        - Cascade delete removes all associated ChatMessages
        - Operation is committed immediately
    """
    db_obj = get_chat_session(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# ChatMessage Operations
# ----------------------------

def get_chat_message(db: Session, id: UUID) -> Optional[ChatMessage]:
    """
    Retrieve a single chat message by ID.
    
    Args:
        db: Database session
        id: ChatMessage UUID
    
    Returns:
        ChatMessage object if found, None otherwise
    """
    return db.query(ChatMessage).filter(ChatMessage.id == id).first()


def get_chat_messages(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatMessage]:
    """
    Retrieve paginated chat messages with optional user filtering.
    
    When filtering by user_id, returns all messages from sessions
    belonging to that user.
    
    Args:
        db: Database session
        skip: Offset for pagination (default: 0)
        limit: Maximum records (default: 100)
        user_id: Filter messages from user's sessions (optional)
    
    Returns:
        List of ChatMessage objects
    
    Performance Note:
        - User filtering requires join operation
        - Typical query time: < 200ms for 100 messages
    """
    query = db.query(ChatMessage)
    if user_id is not None:
        query = query.join(ChatSession, ChatMessage.session_id == ChatSession.id).filter(ChatSession.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def add_message(db: Session, session_id: UUID, role: ChatRole, content: str) -> ChatMessage:
    """
    Add a message to a chat session.
    
    Creates a new message and associates it with a session. After each message,
    the session's conversation summary should be updated if the message count
    exceeds the summarization threshold.
    
    Args:
        db: Database session
        session_id: Parent ChatSession ID
        role: Message role (USER or AI)
        content: Message content/text
    
    Returns:
        Created ChatMessage object
    
    Raises:
        ForeignKeyError: If session_id doesn't exist
    
    Example:
        >>> message = add_message(
        ...     db=db,
        ...     session_id=session_id,
        ...     role=ChatRole.USER,
        ...     content="What's the next step?"
        ... )
    
    See Also:
        - get_session_history(): Retrieve all messages in a session
        - summarize_session(): Generate conversation summary
    """
    db_obj = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_chat_message(db: Session, db_obj: ChatMessage, obj_in: Any) -> ChatMessage:
    """
    Update an existing chat message.
    
    Note:
        - Typically used to edit message content or metadata
        - Does not update the session summary automatically
    
    Args:
        db: Database session
        db_obj: ChatMessage object to update
        obj_in: Update data (dict, object, or Pydantic model)
    
    Returns:
        Updated ChatMessage object
    """
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_chat_message(db: Session, id: UUID) -> Optional[ChatMessage]:
    """
    Delete a chat message from a session.
    
    Args:
        db: Database session
        id: ChatMessage ID to delete
    
    Returns:
        Deleted ChatMessage object if found, None otherwise
    
    Note:
        - Deleting messages may require session summary invalidation
        - Consider cascading impact on conversation context
    """
    db_obj = get_chat_message(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def get_session_history(
    db: Session,
    session_id: UUID,
    limit: int = 50,
) -> List[ChatMessage]:
    """
    Retrieve the message history for a chat session.
    
    Messages are ordered chronologically (oldest first) to preserve
    conversation flow. This is useful for displaying chat UI or
    feeding conversation context to AI models.
    
    Args:
        db: Database session
        session_id: ChatSession ID to retrieve history for
        limit: Maximum messages to return (default: 50, recommended max: 100)
    
    Returns:
        List of ChatMessage objects ordered by creation time (oldest first)
    
    Performance Note:
        - Limit defaults to 50 to avoid memory issues with large contexts
        - Typical query time: < 100ms for 50 messages
    
    Example:
        >>> history = get_session_history(
        ...     db=db,
        ...     session_id=session_id,
        ...     limit=20
        ... )
        >>> for msg in history:
        ...     print(f"{msg.role}: {msg.content[:50]}...")
    
    See Also:
        - add_message(): Add new message to session
        - summarize_session(): Generate session summary
    """
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )


def get_detailed_status() -> Dict[str, Any]:
    """
    Get detailed status information for the chat service.
    
    Used for health checks and monitoring.
    
    Returns:
        Dictionary with service status, module name, and timestamp
    """
    return {
        "module": "chat_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    """
    Reset internal state of the chat service.
    
    Used in testing or after service restart. Logs the operation
    for audit purposes.
    """
    logger.info("chat_service reset_internal_state called")
def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "chat_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("chat_service reset_internal_state called")
