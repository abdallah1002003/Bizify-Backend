import pytest
from sqlalchemy.orm import Session
from app.models.enums import ChatSessionType, ChatRole
from app.schemas.chat.chat_session import ChatSessionCreate
from app.services.chat.chat_session_service import create_chat_session, get_chat_sessions_by_user
from app.services.chat.chat_message_service import add_message_with_ai_response

@pytest.fixture
def test_chat_session(db: Session, test_user):
    obj_in = ChatSessionCreate(
        user_id=test_user.id,
        session_type=ChatSessionType.IDEA_CHAT
    )
    session = create_chat_session(db, obj_in)
    return session

def test_chat_session_retrieval(db: Session, test_user, test_chat_session):
    sessions = get_chat_sessions_by_user(db, test_user.id)
    assert len(sessions) >= 1
    assert sessions[0].id == test_chat_session.id

def test_chat_message_flow(db: Session, test_chat_session):
    # 1. Add user message and get AI response
    messages = add_message_with_ai_response(
        db, 
        session_id=test_chat_session.id, 
        content="How do I start a business?"
    )
    
    assert len(messages) == 2
    assert messages[0].role == ChatRole.USER
    assert messages[1].role == ChatRole.AI
    assert "How do I start a business?" in messages[1].content
    
    # 2. Verify persistence in session
    db.refresh(test_chat_session)
    assert len(test_chat_session.messages) == 2
