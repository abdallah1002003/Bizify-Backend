from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import ChatRole
from app.services.chat import chat_service


def add_message_with_ai_response(db: Session, session_id, content: str):
    user_msg = chat_service.add_message(db, session_id=session_id, role=ChatRole.USER, content=content)
    ai_msg = chat_service.add_message(
        db,
        session_id=session_id,
        role=ChatRole.AI,
        content=f"AI response to: {content}",
    )
    return [user_msg, ai_msg]
