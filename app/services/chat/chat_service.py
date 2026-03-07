from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.structured_logging import get_logger
from app.core.crud_utils import _utc_now
from app.services.base_service import BaseService

from app.services.chat.chat_session_operations import ChatSessionService
from app.services.chat.chat_message_operations import ChatMessageService

logger = get_logger(__name__)


class ChatService(BaseService):
    """
    Unified chat service facade that combines session and message operations.
    Delegates to ChatSessionService and ChatMessageService.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._session_svc = ChatSessionService(db)
        self._message_svc = ChatMessageService(db)

    # --- Session shortcuts ---
    async def get_chat_session(self, id):
        return await self._session_svc.get_chat_session(id)

    async def get_chat_sessions(self, skip=0, limit=100, user_id=None):
        return await self._session_svc.get_chat_sessions(skip, limit, user_id)

    async def get_chat_sessions_by_user(self, user_id, skip=0, limit=100):
        return await self._session_svc.get_chat_sessions_by_user(user_id, skip, limit)

    async def create_chat_session(self, user_id, session_type, business_id=None, idea_id=None):
        return await self._session_svc.create_chat_session(user_id, session_type, business_id, idea_id)

    async def update_chat_session(self, db_obj, obj_in):
        return await self._session_svc.update_chat_session(db_obj, obj_in)

    async def delete_chat_session(self, id):
        return await self._session_svc.delete_chat_session(id)

    # --- Message shortcuts ---
    async def get_chat_message(self, id):
        return await self._message_svc.get_chat_message(id)

    async def get_chat_messages(self, skip=0, limit=100, user_id=None):
        return await self._message_svc.get_chat_messages(skip, limit, user_id)

    async def add_message(self, session_id, role, content):
        return await self._message_svc.add_message(session_id, role, content)

    async def update_chat_message(self, db_obj, obj_in):
        return await self._message_svc.update_chat_message(db_obj, obj_in)

    async def delete_chat_message(self, id):
        return await self._message_svc.delete_chat_message(id)

    async def get_session_history(self, session_id, limit=50):
        return await self._message_svc.get_session_history(session_id, limit)

    def get_detailed_status(self) -> Dict[str, Any]:
        return {
            "module": "chat_service",
            "status": "operational",
            "timestamp": _utc_now().isoformat(),
            "submodules": ["chat_session_operations", "chat_message_operations"],
        }

    def reset_internal_state(self) -> None:
        logger.info("chat_service reset_internal_state called")
