import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.models import ChatMessage, ChatSession
from app.models.enums import ChatRole, ChatSessionType
<<<<<<< HEAD
from app.services.chat.chat_session_operations import ChatSessionService
from app.services.chat.chat_message_operations import ChatMessageService

@pytest.mark.asyncio
class TestChatSessionAsync:
    async def test_get_chat_session(self):
=======
from app.services.chat.chat_session_async import (
    get_chat_session_async,
    create_chat_session_async,
    get_chat_sessions_by_user_async,
)
from app.services.chat.chat_message_async import (
    get_chat_message_async,
    add_message_async,
    get_session_history_async,
)

@pytest.mark.asyncio
class TestChatSessionAsync:
    async def test_get_chat_session_async(self):
>>>>>>> origin/main
        db = AsyncMock()
        session_id = uuid.uuid4()
        mock_session = ChatSession(id=session_id)
        
        # Mocking sqlalchemy execute
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_session
        db.execute.return_value = mock_result
        
<<<<<<< HEAD
        service = ChatSessionService(db)
        result = await service.get_chat_session(session_id)
        assert result == mock_session
        db.execute.assert_called_once()

    async def test_create_chat_session(self):
=======
        result = await get_chat_session_async(db, session_id)
        assert result == mock_session
        db.execute.assert_called_once()

    async def test_create_chat_session_async(self):
>>>>>>> origin/main
        db = AsyncMock()
        db.add = MagicMock()
        user_id = uuid.uuid4()
        
        # We need to simulate the flush/refresh setting the ID
        def mock_flush():
            pass
        db.flush = AsyncMock(side_effect=mock_flush)
            
<<<<<<< HEAD
        service = ChatSessionService(db)
        result = await service.create_chat_session(
            user_id, ChatSessionType.GENERAL
=======
        result = await create_chat_session_async(
            db, user_id, ChatSessionType.GENERAL
>>>>>>> origin/main
        )
        
        assert result.user_id == user_id
        assert result.session_type == ChatSessionType.GENERAL
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

<<<<<<< HEAD
    async def test_get_chat_sessions_by_user(self):
=======
    async def test_get_chat_sessions_by_user_async(self):
>>>>>>> origin/main
        db = AsyncMock()
        user_id = uuid.uuid4()
        
        mock_sessions = [ChatSession(id=uuid.uuid4()) for _ in range(3)]
        
        mock_data_result = MagicMock()
        mock_data_result.scalars().all.return_value = mock_sessions
        
<<<<<<< HEAD
        db.execute.return_value = mock_data_result
        
        service = ChatSessionService(db)
        sessions = await service.get_chat_sessions_by_user(user_id)
        
        assert len(sessions) == 3
        assert db.execute.call_count == 1

@pytest.mark.asyncio
class TestChatMessageAsync:
    async def test_get_chat_message(self):
=======
        mock_count_result = MagicMock()
        mock_count_result.scalars().all.return_value = mock_sessions # len=3
        
        db.execute.side_effect = [mock_data_result, mock_count_result]
        
        sessions, total = await get_chat_sessions_by_user_async(db, user_id)
        
        assert len(sessions) == 3
        assert total == 3
        assert db.execute.call_count == 2

@pytest.mark.asyncio
class TestChatMessageAsync:
    async def test_get_chat_message_async(self):
>>>>>>> origin/main
        db = AsyncMock()
        msg_id = uuid.uuid4()
        mock_msg = ChatMessage(id=msg_id)
        
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_msg
        db.execute.return_value = mock_result
        
<<<<<<< HEAD
        service = ChatMessageService(db)
        result = await service.get_chat_message(msg_id)
        assert result == mock_msg

    async def test_add_message(self):
=======
        result = await get_chat_message_async(db, msg_id)
        assert result == mock_msg

    async def test_add_message_async(self):
>>>>>>> origin/main
        db = AsyncMock()
        db.add = MagicMock()
        session_id = uuid.uuid4()
        
<<<<<<< HEAD
        service = ChatMessageService(db)
        result = await service.add_message(
            session_id, ChatRole.USER, "Hello"
=======
        result = await add_message_async(
            db, session_id, ChatRole.USER, "Hello"
>>>>>>> origin/main
        )
        
        assert result.session_id == session_id
        assert result.content == "Hello"
        assert result.role == ChatRole.USER
        db.add.assert_called_once()
        db.commit.assert_called_once()

<<<<<<< HEAD
    async def test_get_session_history(self):
=======
    async def test_get_session_history_async(self):
>>>>>>> origin/main
        db = AsyncMock()
        session_id = uuid.uuid4()
        
        mock_msgs = [ChatMessage(id=uuid.uuid4()) for _ in range(5)]
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = mock_msgs
        db.execute.return_value = mock_result
        
<<<<<<< HEAD
        service = ChatMessageService(db)
        result = await service.get_session_history(session_id)
=======
        result = await get_session_history_async(db, session_id)
>>>>>>> origin/main
        assert len(result) == 5
        db.execute.assert_called_once()
