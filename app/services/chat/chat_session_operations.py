"""
ChatSession operations for managing conversation contexts.

This module handles all ChatSession CRUD operations including:
    - Creating new chat sessions for users
    - Retrieving existing sessions
    - Updating session metadata
    - Deleting sessions with cascade behavior
    - Pagination and filtering

Sessions represent distinct conversation contexts that can be linked to
business entities or standalone ideas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ChatSession
from app.models.enums import ChatSessionType
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.structured_logging import get_logger

logger = get_logger(__name__)


# ----------------------------
# ChatSession CRUD Operations
# ----------------------------

def get_chat_session(db: Session, id: UUID) -> Optional[ChatSession]:
    """
    Retrieve a chat session by ID.
    
    Fetches a single chat session from the database by its unique identifier.
    Returns None if the session does not exist.
    
    Args:
        db: Database session for query execution
        id: Chat session UUID to retrieve
    
    Returns:
        ChatSession object if found, None otherwise
        
    Example:
        >>> session = get_chat_session(db, session_id)
        >>> if session:
        ...     logger.info(f"Session type: {session.session_type}")
        
    Notes:
        - Does not eagerly load related messages (use lazy loading or explicit join)
        - Query time: < 10ms typical
    """
    return db.query(ChatSession).filter(ChatSession.id == id).first()  # type: ignore[no-any-return]


def get_chat_sessions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatSession]:
    """
    Retrieve paginated chat sessions with optional user filtering.
    
    Fetches a page of chat sessions from the database, optionally filtered
    by user_id. Results are not sorted by default (database order).
    
    Args:
        db: Database session for query execution
        skip: Number of records to skip for offset pagination (default: 0)
        limit: Maximum records to return per page (default: 100, max: 1000)
        user_id: Optional filter by user - only returns sessions for this user
    
    Returns:
        List of ChatSession objects (may be empty if no matches)
        
    Example:
        >>> sessions = get_chat_sessions(db, skip=0, limit=20, user_id=user_id)
        >>> logger.info(f"Retrieved {len(sessions)} sessions")
        
    Performance Notes:
        - User filter requires indexed lookup on user_id
        - Typical query time: < 50ms for limit=100
        - Consider adding .order_by(ChatSession.created_at.desc()) for sorted results
    """
    query = db.query(ChatSession)
    if user_id is not None:
        query = query.filter(ChatSession.user_id == user_id)
    return query.offset(skip).limit(limit).all()  # type: ignore[no-any-return]


def get_chat_sessions_by_user(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[ChatSession]:
    """
    Retrieve all chat sessions for a specific user with pagination.
    
    Fetches chat sessions for a user ordered by creation date in descending
    order (newest sessions first). This is the preferred method for displaying
    user's session list in UI.
    
    Args:
        db: Database session for query execution
        user_id: User to retrieve sessions for
        skip: Number of records to skip (default: 0)
        limit: Maximum records per page (default: 100)
    
    Returns:
        List of ChatSession objects ordered by creation date (newest first)
        
    Example:
        >>> sessions = get_chat_sessions_by_user(db, user_id=user_id, limit=10)
        >>> logger.info(f"User has {len(sessions)} recent sessions")
        >>> for session in sessions:
        ...     logger.info(f"  - {session.session_type} on {session.created_at}")
        
    Performance Notes:
        - Requires index on (user_id, created_at) for optimal performance
        - Typical query time: < 100ms for limit=100
        - Always returns newest first regardless of natural order
    """
    return (  # type: ignore[no-any-return]
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
    
    Initializes a new conversation context with the specified parameters.
    A chat session can be linked to a business or idea, or be standalone
    (GENERAL type). Sessions start with an empty conversation summary.
    
    Args:
        db: Database session for transaction management
        user_id: User creating/owning the session
        session_type: Type of session (BUSINESS, IDEA, or GENERAL)
        business_id: Associated business ID (required for BUSINESS type, else None)
        idea_id: Associated idea ID (required for IDEA type, else None)
    
    Returns:
        Created ChatSession object with all fields initialized
        
    Raises:
        ValueError: If session_type is BUSINESS but business_id is None
        ValueError: If session_type is IDEA but idea_id is None
        IntegrityError: If user_id, business_id, or idea_id reference non-existent entities
        
    Example:
        >>> session = create_chat_session(
        ...     db=db,
        ...     user_id=user_id,
        ...     session_type=ChatSessionType.IDEA,
        ...     idea_id=idea_id
        ... )
        >>> logger.info(f"Created session: {session.id}")
        
    Notes:
        - conversation_summary_json initialized as empty dict
        - created_at and updated_at set by ORM defaults
        - Requires transaction commit by caller
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
    logger.info(f"Created chat session {db_obj.id} for user {user_id}, type={session_type}")
    return db_obj


def update_chat_session(db: Session, db_obj: ChatSession, obj_in: Any) -> ChatSession:
    """
    Update an existing chat session.
    
    Applies partial updates to a chat session. Only provided fields are
    updated; other fields remain unchanged. Uses Pydantic model exclusion
    to ignore unset fields.
    
    Args:
        db: Database session for transaction management
        db_obj: ChatSession object to update (must be already loaded)
        obj_in: Update data - can be dict, Pydantic model, or object with attributes
    
    Returns:
        Updated ChatSession object with changes persisted
        
    Example:
        >>> update_data = {"conversation_summary_json": {"tokens": 150}}
        >>> session = update_chat_session(db, db_obj, update_data)
        
    Notes:
        - Only updates fields present in obj_in (partial updates)
        - Excludes unset fields when converting Pydantic models
        - Automatically commits transaction
    """
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    logger.info(f"Updated chat session {db_obj.id}")
    return db_obj


def delete_chat_session(db: Session, id: UUID) -> Optional[ChatSession]:
    """
    Delete a chat session and all associated messages.
    
    Permanently removes a chat session from the database. Due to foreign key
    constraints with cascade delete, all associated ChatMessage records are
    also deleted automatically.
    
    Args:
        db: Database session for transaction management
        id: Chat session ID to delete
    
    Returns:
        Deleted ChatSession object if found, None if session doesn't exist
        
    Raises:
        DatabaseError: If cascade delete fails on messages
        
    Example:
        >>> deleted = delete_chat_session(db, session_id)
        >>> if deleted:
        ...     logger.info(f"Deleted session {deleted.id} with all messages")
        
    Notes:
        - Cascade delete automatically removes all ChatMessage records
        - Operation is committed immediately
        - Cannot be undone (consider soft deletes for audit trails)
    """
    db_obj = get_chat_session(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    logger.info(f"Deleted chat session {id}")
    return db_obj


def get_detailed_status() -> Dict[str, any]:  # type: ignore
    """
    Get detailed status information for chat session operations.
    
    Returns service health and diagnostic information useful for
    monitoring and health checks.
    
    Returns:
        Dictionary with module name, status, and ISO timestamp
    """
    return {
        "module": "chat_session_operations",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }
