import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.enums import UserRole, ChatSessionType
from app.models.users.user import User
from app.models.chat.chat import ChatSession
from app.core.security import get_password_hash
from app.api.v1.chat.chat_ws import manager


def create_test_user_for_ws(db: Session, prefix: str) -> User:
    user = User(
        name=f"{prefix}-user",
        email=f"{prefix}_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_chat_session(db: Session, user_id: uuid.UUID) -> ChatSession:
    chat_session = ChatSession(
        user_id=user_id,
        session_type=ChatSessionType.GENERAL
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session

@pytest.mark.asyncio
async def test_connection_manager():
    # We can mock a websocket easily or just use None since the async code just creates lists
    class MockWebsocket:
        async def accept(self): pass
        async def send_text(self, data): self.data = data
        
    ws1 = MockWebsocket()
    ws2 = MockWebsocket()
    sid = uuid.uuid4()
    
    await manager.connect(ws1, sid)
    assert len(manager.active_connections[sid]) == 1
    
    await manager.connect(ws2, sid)
    assert len(manager.active_connections[sid]) == 2
    
    await manager.send_personal_message("hello", ws1)
    assert getattr(ws1, 'data', None) == "hello"
    
    await manager.broadcast("broad", sid)
    assert getattr(ws1, 'data', None) == "broad"
    assert getattr(ws2, 'data', None) == "broad"
    
    manager.disconnect(ws1, sid)
    assert len(manager.active_connections[sid]) == 1
    
    manager.disconnect(ws2, sid)
    assert sid not in manager.active_connections

def test_websocket_endpoint_unauthorized(client: TestClient):
    from starlette.websockets import WebSocketDisconnect
    # Invalid token
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/api/v1/chat/ws/{uuid.uuid4()}?token=invalid") as websocket:
            websocket.receive_text()
    assert excinfo.value.code == 1008

def test_websocket_endpoint_not_owner(client: TestClient, db: Session):
    from starlette.websockets import WebSocketDisconnect
    user1 = create_test_user_for_ws(db, "usr1")
    user2 = create_test_user_for_ws(db, "usr2")
    session1 = create_test_chat_session(db, user1.id)
    
    token2 = create_access_token(str(user2.id), timedelta(minutes=10))
    
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/api/v1/chat/ws/{session1.id}?token={token2}") as websocket:
            websocket.receive_text()
    assert excinfo.value.code == 1008

def test_websocket_endpoint_success(client: TestClient, db: Session):
    user = create_test_user_for_ws(db, "success")
    session = create_test_chat_session(db, user.id)
    token = create_access_token(str(user.id), timedelta(minutes=10))
    
    with client.websocket_connect(f"/api/v1/chat/ws/{session.id}?token={token}") as websocket:
        # Send raw string
        websocket.send_text("Hello AI")
        response = websocket.receive_json()
        assert response["role"] == "ai"
        assert "Hello AI" in response["content"]
        assert response["session_id"] == str(session.id)
        
        # Send JSON string
        websocket.send_json({"content": "Second message"})
        response = websocket.receive_json()
        assert response["role"] == "ai"
        assert "Second message" in response["content"]

        # Send empty message (should be ignored)
        websocket.send_json({"content": ""})
        # If we expect no response, we can just close the socket, but let's just send another to verify it didn't crash
        websocket.send_text("Third message")
        response = websocket.receive_json()
        assert response["role"] == "ai"
        assert "Third message" in response["content"]
