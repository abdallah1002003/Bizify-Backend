from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.chat import chat_service


def create_chat_session(db: Session, obj_in):
    return chat_service.create_chat_session(
        db,
        user_id=obj_in.user_id,
        business_id=obj_in.business_id,
        idea_id=obj_in.idea_id,
        session_type=obj_in.session_type,
    )


def get_chat_sessions_by_user(db: Session, user_id):
    return chat_service.get_chat_sessions_by_user(db, user_id)
