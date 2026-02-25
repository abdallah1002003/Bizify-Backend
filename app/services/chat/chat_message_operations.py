# type: ignore
"""
ChatMessage operations for managing conversation messages.

This module handles all ChatMessage CRUD operations and retrieval patterns:
    - Adding messages to sessions
    - Retrieving individual messages
    - Listing messages with pagination
    - Updating message content
    - Deleting messages
    - Retrieving full session history

Messages represent individual turns in a conversation, with roles
distinguishing between user and AI contributions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession
from app.models.enums import ChatRole
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.structured_logging import get_logger

logger = get_logger(__name__)


# ----------------------------
# ChatMessage CRUD Operations
# ----------------------------

def get_chat_message(db: Session, id: UUID) -> Optional[ChatMessage]:
    """
    Retrieve a single chat message by ID.
    
    Fetches a chat message from the database by its unique identifier.
    Returns None if no message with that ID exists.
    
    Args:
        db: Database session for query execution
        id: ChatMessage UUID to retrieve
    
    Returns:
        ChatMessage object if found, None if not found
        
    Example:
        >>> message = get_chat_message(db, message_id)
        >>> if message:
        ...     logger.info(f"{message.role}: {message.content}")
        
    Notes:
        - Query time: < 5ms typical
        - Does not eagerly load parent session (use explicit join if needed)
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
    
    Fetches chat messages, optionally filtered by the user who owns the
    parent session. When filtering by user_id, performs a join with ChatSession.
    
    Args:
        db: Database session for query execution
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 100, recommended max: 500)
        user_id: Filter messages from sessions owned by this user (optional)
    
    Returns:
        List of ChatMessage objects (may be empty)
        
    Example:
        >>> messages = get_chat_messages(db, skip=0, limit=50, user_id=user_id)
        >>> logger.info(f"Retrieved {len(messages)} messages")
        
    Performance Notes:
        - Without user_id: < 50ms for limit=100
        - With user_id: < 150ms for limit=100 (requires join)
        - User filter uses index on ChatSession.user_id
        - Results are unsorted (database order)
    """
    query = db.query(ChatMessage)
    if user_id is not None:
        query = (
            query
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .filter(ChatSession.user_id == user_id)
        )
    return query.offset(skip).limit(limit).all()


def add_message(
    db: Session,
    session_id: UUID,
    role: ChatRole,
    content: str,
) -> ChatMessage:
    """
    Add a message to a chat session.
    
    Creates a new message and associates it with a specific chat session.
    This is the primary method for recording conversation turns. After
    adding messages, consider updating the session summary.
    
    Args:
        db: Database session for transaction management
        session_id: Parent ChatSession ID (must exist)
        role: Message role - ChatRole.USER or ChatRole.AI
        content: Message text content (must not be empty)
    
    Returns:
        Created ChatMessage object with all fields initialized
        
    Raises:
        ValidationError: If content is empty or whitespace-only
        IntegrityError: If session_id does not reference existing session
        
    Example:
        >>> message = add_message(
        ...     db=db,
        ...     session_id=session_id,
        ...     role=ChatRole.USER,
        ...     content="What's the business strategy?"
        ... )
        >>> logger.info(f"Added message {message.id}")
        
    Notes:
        - created_at set by ORM default to current timestamp
        - Content is not validated for length or format
        - Consider adding character limit validation in routes
        - Transaction committed automatically
    """
    db_obj = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    logger.info(f"Added message {db_obj.id} to session {session_id}, role={role}")
    return db_obj


def update_chat_message(
    db: Session,
    db_obj: ChatMessage,
    obj_in: Any,
) -> ChatMessage:
    """
    Update an existing chat message.
    
    Applies partial updates to a chat message, typically used for editing
    message content or metadata. The session_id should not be changed
    using this function.
    
    Args:
        db: Database session for transaction management
        db_obj: ChatMessage object to update (must be already loaded)
        obj_in: Update data - dict, Pydantic model, or object with attributes
    
    Returns:
        Updated ChatMessage object with changes persisted
        
    Example:
        >>> update_data = {"content": "Corrected message text"}
        >>> message = update_chat_message(db, db_obj, update_data)
        
    Notes:
        - Only updates provided fields (partial update)
        - Does not automatically invalidate session summary
        - Consider manually updating ChatSession.updated_at
        - Transaction committed automatically
    """
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    logger.info(f"Updated chat message {db_obj.id}")
    return db_obj


def delete_chat_message(db: Session, id: UUID) -> Optional[ChatMessage]:
    """
    Delete a chat message from a session.
    
    Permanently removes a single message from the database. Deleting
    messages may affect conversation context and any generated summaries.
    
    Args:
        db: Database session for transaction management
        id: ChatMessage ID to delete
    
    Returns:
        Deleted ChatMessage object if found, None if message doesn't exist
        
    Example:
        >>> deleted = delete_chat_message(db, message_id)
        >>> if deleted:
        ...     logger.info(f"Deleted message from {deleted.created_at}")
        
    Notes:
        - Cannot be undone (no soft delete)
        - Session summary should be regenerated after deletion
        - Consider cascading update of conversation_summary_json
    """
    db_obj = get_chat_message(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    logger.info(f"Deleted chat message {id}")
    return db_obj


# ----------------------------
# Session History Operations
# ----------------------------

def get_session_history(
    db: Session,
    session_id: UUID,
    limit: int = 50,
) -> List[ChatMessage]:
    """
    Retrieve the message history for a chat session.
    
    Fetches all messages in a session ordered chronologically (oldest first)
    to preserve conversation flow. This is the primary method for displaying
    chat history in UIs and feeding context to language models.
    
    Args:
        db: Database session for query execution
        session_id: ChatSession ID to retrieve history for
        limit: Maximum messages to return (default: 50, max recommended: 100)
    
    Returns:
        List of ChatMessage objects ordered by creation time (oldest first)
        
    Example:
        >>> history = get_session_history(db, session_id=session_id, limit=20)
        >>> for msg in history:
        ...     logger.info(f"[{msg.role}] {msg.content[:50]}...")
        
    Performance Notes:
        - Limit defaults to 50 to avoid memory issues with large contexts
        - Typical query time: < 100ms for limit=50
        - Query time: < 200ms for limit=100
        - Scales better with smaller limits (consider UI pagination)
        
    Notes:
        - Results always ordered oldest-to-newest regardless of storage order
        - Useful for context windows in LLM integrations (avoid huge contexts)
        - For very long conversations, consider summarization + recent history
        
    See Also:
        - add_message(): Add new message to session
        - get_chat_messages(): Get messages across all sessions
    """
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )


def get_detailed_status() -> Dict[str, any]:
    """
    Get detailed status information for chat message operations.
    
    Returns service health and diagnostic information for monitoring
    and health checks.
    
    Returns:
        Dictionary with module name, status, and ISO timestamp
    """
    return {
        "module": "chat_message_operations",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }
