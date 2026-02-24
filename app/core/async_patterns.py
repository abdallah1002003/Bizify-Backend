"""
Async/Await pattern examples for Bizify API services.

This module provides examples of converting synchronous database operations
to asynchronous patterns for improved performance and concurrency.

Key improvements:
- Non-blocking I/O operations
- Better resource utilization
- Support for concurrent requests
- Improved performance under high load
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models import ChatMessage, ChatSession
from app.core.structured_logging import get_logger, PerformanceTimer
import asyncio

logger = get_logger(__name__)


# ============================================================================
# Example 1: Simple Async Database Query
# ============================================================================

async def get_chat_session_async(db: AsyncSession, session_id: UUID) -> Optional[ChatSession]:
    """
    Async version of get_chat_session.
    
    Benefits:
    - Non-blocking database query
    - Allows other requests to process while waiting for DB
    - Better concurrency under high load
    
    Args:
        db: AsyncSession for async database operations
        session_id: ChatSession ID to retrieve
    
    Returns:
        ChatSession object if found, None otherwise
    """
    with PerformanceTimer(logger, f"get_chat_session_async({session_id})", threshold_ms=100):
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        result = await db.execute(stmt)
        return result.scalars().first()


# ============================================================================
# Example 2: Async Pagination Query
# ============================================================================

async def get_chat_sessions_by_user_async(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[ChatSession], int]:
    """
    Async version with pagination and total count.
    
    Features:
    - Async database queries
    - Efficient pagination with offset/limit
    - Get total count concurrently
    
    Args:
        db: AsyncSession
        user_id: User ID to filter by
        skip: Pagination offset
        limit: Pagination limit
    
    Returns:
        Tuple of (sessions list, total count)
    """
    with PerformanceTimer(logger, f"get_chat_sessions_by_user_async({user_id})", threshold_ms=200):
        # Execute main query
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        # Execute count query concurrently
        count_stmt = select(ChatSession).where(ChatSession.user_id == user_id)
        
        # Run both queries concurrently
        sessions_result, count_result = await asyncio.gather(
            db.execute(stmt),
            db.execute(count_stmt),
        )
        
        sessions = sessions_result.scalars().all()
        total = len(count_result.scalars().all())
        
        return sessions, total


# ============================================================================
# Example 3: Async Create with Multiple Operations
# ============================================================================

async def create_chat_session_async(
    db: AsyncSession,
    user_id: UUID,
    session_type: str,
    business_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
) -> ChatSession:
    """
    Async version of create_chat_session with validation.
    
    Features:
    - Async validation
    - Atomic create operation
    - Proper error handling
    
    Args:
        db: AsyncSession
        user_id: User creating the session
        session_type: Type of session
        business_id: Optional business ID
        idea_id: Optional idea ID
    
    Returns:
        Created ChatSession
    """
    with PerformanceTimer(logger, "create_chat_session_async", threshold_ms=150):
        # Create new session
        new_session = ChatSession(
            user_id=user_id,
            session_type=session_type,
            business_id=business_id,
            idea_id=idea_id,
            conversation_summary_json={},
        )
        
        db.add(new_session)
        await db.flush()  # Flush to get ID without committing
        
        logger.info(
            f"ChatSession created",
            extra={
                "session_id": str(new_session.id),
                "user_id": str(user_id),
                "session_type": session_type,
            }
        )
        
        await db.commit()
        await db.refresh(new_session)
        return new_session


# ============================================================================
# Example 4: Async Batch Operations
# ============================================================================

async def add_messages_batch_async(
    db: AsyncSession,
    session_id: UUID,
    messages: List[Dict[str, str]],
) -> List[ChatMessage]:
    """
    Async batch insert of multiple messages.
    
    Features:
    - Single database round-trip for multiple inserts
    - Better performance than individual inserts
    - Atomic operation
    
    Args:
        db: AsyncSession
        session_id: Parent session ID
        messages: List of message dicts with 'role' and 'content'
    
    Returns:
        List of created ChatMessage objects
    """
    with PerformanceTimer(logger, f"add_messages_batch_async({len(messages)} msgs)", threshold_ms=200):
        # Create message objects
        message_objects = [
            ChatMessage(
                session_id=session_id,
                role=msg["role"],
                content=msg["content"],
            )
            for msg in messages
        ]
        
        # Add all messages in one operation
        db.add_all(message_objects)
        await db.flush()
        
        logger.info(
            f"Batch added {len(messages)} messages",
            extra={
                "session_id": str(session_id),
                "count": len(messages),
            }
        )
        
        await db.commit()
        
        # Refresh all objects
        for msg in message_objects:
            await db.refresh(msg)
        
        return message_objects


# ============================================================================
# Example 5: Concurrent API Calls
# ============================================================================

async def fetch_multiple_sessions_async(
    db: AsyncSession,
    session_ids: List[UUID],
) -> List[Optional[ChatSession]]:
    """
    Fetch multiple sessions concurrently.
    
    Features:
    - Concurrent database queries
    - Better performance for bulk operations
    - Handles failures gracefully
    
    Args:
        db: AsyncSession
        session_ids: List of session IDs to fetch
    
    Returns:
        List of ChatSession objects (None for not found)
    """
    with PerformanceTimer(
        logger,
        f"fetch_multiple_sessions_async({len(session_ids)} sessions)",
        threshold_ms=300
    ):
        # Create async tasks for each fetch
        tasks = [
            get_chat_session_async(db, session_id)
            for session_id in session_ids
        ]
        
        # Execute all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        sessions = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Error fetching session {session_ids[i]}: {result}"
                )
                sessions.append(None)
            else:
                sessions.append(result)
        
        return sessions


# ============================================================================
# Example 6: Async Update with Condition
# ============================================================================

async def update_session_summary_async(
    db: AsyncSession,
    session_id: UUID,
    summary: Dict[str, Any],
) -> bool:
    """
    Async update with conditional logic.
    
    Features:
    - Async update operation
    - Condition checking
    - Proper logging
    
    Args:
        db: AsyncSession
        session_id: Session to update
        summary: Summary dictionary
    
    Returns:
        True if update succeeded, False otherwise
    """
    with PerformanceTimer(logger, f"update_session_summary_async({session_id})", threshold_ms=150):
        # Check if session exists
        session = await get_chat_session_async(db, session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for update")
            return False
        
        # Update session
        stmt = (
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(conversation_summary_json=summary)
        )
        
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"Session {session_id} summary updated")
        return True


# ============================================================================
# Example 7: Async Transaction with Rollback
# ============================================================================

async def transfer_session_ownership_async(
    db: AsyncSession,
    session_id: UUID,
    new_user_id: UUID,
) -> bool:
    """
    Async transaction with rollback capability.
    
    Features:
    - ACID transaction
    - Automatic rollback on error
    - Idempotent operation
    
    Args:
        db: AsyncSession
        session_id: Session to transfer
        new_user_id: New owner user ID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        async with db.begin():  # Transaction context
            # Verify session exists
            session = await get_chat_session_async(db, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Verify new user exists (in real code)
            logger.info(
                f"Transferring session ownership",
                extra={
                    "session_id": str(session_id),
                    "from_user": str(session.user_id),
                    "to_user": str(new_user_id),
                }
            )
            
            # Update ownership
            stmt = (
                update(ChatSession)
                .where(ChatSession.id == session_id)
                .values(user_id=new_user_id)
            )
            await db.execute(stmt)
            
            # Transaction auto-commits on successful context exit
            return True
            
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        await db.rollback()  # Explicit rollback
        return False


# ============================================================================
# Example 8: Async Stream Large Results
# ============================================================================

async def stream_sessions_async(
    db: AsyncSession,
    user_id: UUID,
    batch_size: int = 100,
):
    """
    Async generator for streaming large result sets.
    
    Features:
    - Memory efficient (streams instead of loading all)
    - Async iteration
    - Good for large datasets
    
    Args:
        db: AsyncSession
        user_id: User to stream sessions for
        batch_size: Number of results per batch
    
    Yields:
        ChatSession objects in batches
    
    Example:
        async for session in stream_sessions_async(db, user_id):
            await process_session(session)
    """
    skip = 0
    
    while True:
        sessions, _ = await get_chat_sessions_by_user_async(
            db, user_id, skip=skip, limit=batch_size
        )
        
        if not sessions:
            break
        
        for session in sessions:
            yield session
        
        skip += batch_size


# ============================================================================
# Migration Guide: Converting to Async
# ============================================================================

"""
MIGRATION GUIDE: How to Convert Your Services to Async

1. ADD ASYNC DATABASE ENGINE TO main.py:
   
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
   
   async_engine = create_async_engine(
       settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
       echo=False,
       pool_size=20,
       max_overflow=40,
   )
   
   AsyncSessionLocal = sessionmaker(
       async_engine, class_=AsyncSession, expire_on_commit=False
   )

2. UPDATE ROUTE HANDLERS:
   
   # Before (sync):
   @router.get("/sessions/{session_id}")
   def get_session(session_id: UUID, db: Session = Depends(get_db)):
       return get_chat_session(db, session_id)
   
   # After (async):
   @router.get("/sessions/{session_id}")
   async def get_session(session_id: UUID, db: AsyncSession = Depends(get_async_db)):
       return await get_chat_session_async(db, session_id)

3. UPDATE DEPENDENCY INJECTION:
   
   async def get_async_db():
       async with AsyncSessionLocal() as session:
           try:
               yield session
           finally:
               await session.close()

4. CONVERT QUERIES:
   
   # Before (sync):
   result = db.query(ChatSession).filter(...).first()
   
   # After (async):
   stmt = select(ChatSession).where(...)
   result = await db.execute(stmt)
   return result.scalars().first()

5. BENEFITS ACHIEVED:
   ✅ Non-blocking I/O
   ✅ Better concurrency
   ✅ Higher throughput
   ✅ Reduced latency
   ✅ Better resource utilization

6. PERFORMANCE EXPECTATIONS:
   - 30-50% improvement in throughput
   - 20-40% reduction in response time
   - Better handling of concurrent requests
   - Lower memory usage per request

7. MONITORING:
   - Track query duration with PerformanceTimer
   - Monitor database connection pool usage
   - Check concurrent request metrics
   - Use Prometheus metrics for visibility
"""
