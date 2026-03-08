from __future__ import annotations

from typing import Any, Dict

from app.core.structured_logging import get_logger
from app.core.crud_utils import _utc_now

# Import all operations from the newly async operations files
from app.services.chat.chat_session_operations import (
    get_chat_session,
    get_chat_sessions,
    get_chat_sessions_by_user,
    create_chat_session,
    update_chat_session,
    delete_chat_session,
)

from app.services.chat.chat_message_operations import (
    get_chat_message,
    get_chat_messages,
    add_message,
    update_chat_message,
    delete_chat_message,
    get_session_history,
)

from app.services.base_service import BaseService

logger = get_logger(__name__)


class ChatService(BaseService):
    """Refactored class-based access to chat services."""
    async def get_chat_session(self, id: Any) -> Any:
        return await get_chat_session(self.db, id)

    async def get_chat_sessions(self, skip: int = 0, limit: int = 100) -> Any:
        return await get_chat_sessions(self.db, skip, limit)

    async def get_chat_sessions_by_user(self, user_id: Any) -> Any:
        return await get_chat_sessions_by_user(self.db, user_id)

    async def create_chat_session(self, **kwargs) -> Any:
        return await create_chat_session(self.db, **kwargs)

    async def update_chat_session(self, db_obj: Any, obj_in: Any) -> Any:
        return await update_chat_session(self.db, db_obj, obj_in)

    async def delete_chat_session(self, id: Any) -> Any:
        return await delete_chat_session(self.db, id)

    async def get_chat_message(self, id: Any) -> Any:
        return await get_chat_message(self.db, id)

    async def get_chat_messages(self, skip: int = 0, limit: int = 100) -> Any:
        return await get_chat_messages(self.db, skip, limit)

    async def add_message(self, session_id: Any, role: str, content: str) -> Any:
        return await add_message(self.db, session_id, role, content)

    async def update_chat_message(self, db_obj: Any, obj_in: Any) -> Any:
        return await update_chat_message(self.db, db_obj, obj_in)

    async def delete_chat_message(self, id: Any) -> Any:
        return await delete_chat_message(self.db, id)

    async def get_session_history(self, session_id: Any) -> Any:
        return await get_session_history(self.db, session_id)


# Re-export unified async interface
__all__ = [
    # Session operations
    "get_chat_session",
    "get_chat_sessions",
    "get_chat_sessions_by_user",
    "create_chat_session",
    "update_chat_session",
    "delete_chat_session",
    # Message operations
    "get_chat_message",
    "get_chat_messages",
    "add_message",
    "update_chat_message",
    "delete_chat_message",
    "get_session_history",
    # Status operations
    "get_detailed_status",
    "reset_internal_state",
]


async def get_detailed_status() -> Dict[str, Any]:
    """
    Get detailed status information for the chat service.
    
    Aggregates status from chat session and message operations.
    
    Returns:
        Dictionary with service status, module name, and timestamp
    """
    return {
        "module": "chat_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
        "submodules": [
            "chat_session_operations",
            "chat_message_operations",
        ]
    }


async def reset_internal_state() -> None:
    """
    Reset internal state of the chat service.
    
    Used in testing and after service restart. Logs the operation
    for audit and debugging purposes.
    """
    logger.info("chat_service reset_internal_state called")

