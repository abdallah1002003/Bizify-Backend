import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.async_patterns import (
    get_chat_session_async,
    get_chat_sessions_by_user_async,
    create_chat_session_async,
    add_messages_batch_async,
    fetch_multiple_sessions_async,
    update_session_summary_async,
    transfer_session_ownership_async,
    stream_sessions_async
)
from app.models.enums import ChatSessionType
from app.models import ChatSession, ChatMessage

@pytest.mark.asyncio
async def test_get_chat_session_async():
    db = AsyncMock()
    session_id = uuid.uuid4()
    mock_session = MagicMock(spec=ChatSession)
    
    # Mock result.scalars().first()
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = mock_session
    db.execute.return_value = mock_result
    
    result = await get_chat_session_async(db, session_id)
    assert result == mock_session
    db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_chat_sessions_by_user_async():
    db = AsyncMock()
    user_id = uuid.uuid4()
    mock_sessions = [MagicMock(spec=ChatSession), MagicMock(spec=ChatSession)]
    
    # Mock result.scalars().all()
    mock_sessions_result = MagicMock()
    mock_sessions_result.scalars().all.return_value = mock_sessions
    
    mock_count_result = MagicMock()
    mock_count_result.scalars().all.return_value = mock_sessions # total count is len of all
    
    db.execute.side_effect = [mock_sessions_result, mock_count_result]
    
    sessions, total = await get_chat_sessions_by_user_async(db, user_id)
    assert sessions == mock_sessions
    assert total == 2
    assert db.execute.call_count == 2

@pytest.mark.asyncio
async def test_create_chat_session_async():
    db = AsyncMock()
    user_id = uuid.uuid4()
    session_type = ChatSessionType.GENERAL
    
    result = await create_chat_session_async(db, user_id, session_type)
    
    assert isinstance(result, ChatSession)
    assert result.user_id == user_id
    assert result.session_type == session_type
    db.add.assert_called_once()
    db.flush.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_add_messages_batch_async():
    db = AsyncMock()
    session_id = uuid.uuid4()
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"}
    ]
    
    result = await add_messages_batch_async(db, session_id, messages)
    
    assert len(result) == 2
    assert all(isinstance(m, ChatMessage) for m in result)
    assert result[0].content == "hello"
    db.add_all.assert_called_once()
    db.commit.assert_called_once()
    assert db.refresh.call_count == 2

@pytest.mark.asyncio
async def test_fetch_multiple_sessions_async():
    db = AsyncMock()
    ids = [uuid.uuid4(), uuid.uuid4()]
    mock_session = MagicMock(spec=ChatSession)
    
    # Mock get_chat_session_async directly since it's called internally
    with patch("app.core.async_patterns.get_chat_session_async", side_effect=[mock_session, Exception("fail")]):
        results = await fetch_multiple_sessions_async(db, ids)
        assert len(results) == 2
        assert results[0] == mock_session
        assert results[1] is None

@pytest.mark.asyncio
async def test_update_session_summary_async():
    db = AsyncMock()
    session_id = uuid.uuid4()
    summary = {"key": "value"}
    
    # Session not found
    with patch("app.core.async_patterns.get_chat_session_async", return_value=None):
        res = await update_session_summary_async(db, session_id, summary)
        assert res is False
    
    # Session found and updated
    with patch("app.core.async_patterns.get_chat_session_async", return_value=MagicMock()):
        res = await update_session_summary_async(db, session_id, summary)
        assert res is True
        db.execute.assert_called_once()
        db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_transfer_session_ownership_async_success():
    from sqlalchemy.ext.asyncio import AsyncSession
    db = MagicMock(spec=AsyncSession)
    db.begin.return_value = AsyncMock()
    db.execute = AsyncMock()
    db.rollback = AsyncMock()
    
    session_id = uuid.uuid4()
    new_user_id = uuid.uuid4()
    mock_session = MagicMock(user_id=uuid.uuid4())
    
    with patch("app.core.async_patterns.get_chat_session_async", return_value=mock_session):
        res = await transfer_session_ownership_async(db, session_id, new_user_id)
        assert res is True
        db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_transfer_session_ownership_async_not_found():
    from sqlalchemy.ext.asyncio import AsyncSession
    db = MagicMock(spec=AsyncSession)
    db.begin.return_value = AsyncMock()
    db.rollback = AsyncMock()
    
    session_id = uuid.uuid4()
    new_user_id = uuid.uuid4()
    
    with patch("app.core.async_patterns.get_chat_session_async", return_value=None):
        res = await transfer_session_ownership_async(db, session_id, new_user_id)
        assert res is False
        db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_transfer_session_ownership_async_exception():
    from sqlalchemy.ext.asyncio import AsyncSession
    db = MagicMock(spec=AsyncSession)
    db.begin.side_effect = Exception("db error")
    db.rollback = AsyncMock()
    
    res = await transfer_session_ownership_async(db, uuid.uuid4(), uuid.uuid4())
    assert res is False
    db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_stream_sessions_async():
    db = AsyncMock()
    user_id = uuid.uuid4()
    mock_sessions = [MagicMock(spec=ChatSession)]
    
    with patch("app.core.async_patterns.get_chat_sessions_by_user_async", side_effect=[(mock_sessions, 1), ([], 0)]):
        generator = stream_sessions_async(db, user_id, batch_size=1)
        results = []
        async for s in generator:
            results.append(s)
        
        assert len(results) == 1
        assert results[0] == mock_sessions[0]
