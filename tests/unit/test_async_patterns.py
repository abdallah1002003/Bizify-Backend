import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
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
from app.models import ChatSession
from app.models.enums import ChatSessionType

@pytest.mark.asyncio
async def test_get_chat_session_async():
    db = AsyncMock()
    session_id = uuid4()
    mock_session = ChatSession(id=session_id)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_session
    db.execute.return_value = mock_result
    
    result = await get_chat_session_async(db, session_id)
    assert result == mock_session
    db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_chat_sessions_by_user_async():
    db = AsyncMock()
    user_id = uuid4()
    mock_sessions = [ChatSession(id=uuid4(), user_id=user_id) for _ in range(3)]
    
    # Mock for sessions query
    mock_sessions_result = MagicMock()
    mock_sessions_result.scalars.return_value.all.return_value = mock_sessions
    
    # Mock for count query
    mock_count_result = MagicMock()
    mock_count_result.scalars.return_value.all.return_value = mock_sessions # Simply reusing for len()
    
    db.execute.side_effect = [mock_sessions_result, mock_count_result]
    
    sessions, total = await get_chat_sessions_by_user_async(db, user_id)
    assert len(sessions) == 3
    assert total == 3

@pytest.mark.asyncio
async def test_create_chat_session_async():
    db = AsyncMock()
    user_id = uuid4()
    
    session = await create_chat_session_async(db, user_id, ChatSessionType.GENERAL)
    assert session.user_id == user_id
    db.add.assert_called_once()
    db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_add_messages_batch_async():
    db = AsyncMock()
    session_id = uuid4()
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"}
    ]
    
    result = await add_messages_batch_async(db, session_id, messages)
    assert len(result) == 2
    assert result[0].content == "hello"
    db.add_all.assert_called_once()
    db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_multiple_sessions_async():
    db = AsyncMock()
    ids = [uuid4(), uuid4()]
    
    mock_session = ChatSession(id=ids[0])
    
    # Mock execute for get_chat_session_async calls
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_session
    db.execute.return_value = mock_result
    
    results = await fetch_multiple_sessions_async(db, ids)
    assert len(results) == 2
    assert results[0] == mock_session

@pytest.mark.asyncio
async def test_update_session_summary_async():
    db = AsyncMock()
    session_id = uuid4()
    
    # Mock session exists
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = ChatSession(id=session_id)
    db.execute.return_value = mock_result
    
    success = await update_session_summary_async(db, session_id, {"summary": "done"})
    assert success is True
    assert db.execute.call_count == 2 # 1 for get, 1 for update
    db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_transfer_session_ownership_async():
    db = MagicMock()
    cm = AsyncMock()
    db.begin.return_value = cm
    
    session_id = uuid4()
    new_user_id = uuid4()
    
    mock_session = ChatSession(id=session_id, user_id=uuid4())
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_session
    db.execute = AsyncMock(return_value=mock_result)
    db.rollback = AsyncMock()
    
    success = await transfer_session_ownership_async(db, session_id, new_user_id)
    assert success is True
    db.rollback.assert_not_called()

@pytest.mark.asyncio
async def test_transfer_session_ownership_not_found():
    db = MagicMock()
    cm = AsyncMock()
    db.begin.return_value = cm
    db.rollback = AsyncMock()
    
    session_id = uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    
    success = await transfer_session_ownership_async(db, session_id, uuid4())
    assert success is False
    db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_stream_sessions_async():
    db = AsyncMock()
    user_id = uuid4()
    
    mock_sessions = [ChatSession(id=uuid4()) for _ in range(2)]
    
    mock_res1 = MagicMock()
    mock_res1.scalars.return_value.all.return_value = mock_sessions
    
    mock_count = MagicMock()
    mock_count.scalars.return_value.all.return_value = mock_sessions
    
    mock_res2 = MagicMock()
    mock_res2.scalars.return_value.all.return_value = []
    
    db.execute.side_effect = [mock_res1, mock_count, mock_res2, mock_res2]
    
    collected = []
    async for session in stream_sessions_async(db, user_id, batch_size=2):
        collected.append(session)
    
    assert len(collected) == 2
