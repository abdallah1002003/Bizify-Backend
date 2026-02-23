from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession
from app.models.enums import ChatRole, ChatSessionType

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# ChatSession
# ----------------------------

def get_chat_session(db: Session, id: UUID) -> Optional[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.id == id).first()


def get_chat_sessions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatSession]:
    query = db.query(ChatSession)
    if user_id is not None:
        query = query.filter(ChatSession.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def get_chat_sessions_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_chat_session(
    db: Session,
    user_id: UUID,
    session_type: ChatSessionType,
    business_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
) -> ChatSession:
    db_obj = ChatSession(
        user_id=user_id,
        session_type=session_type,
        business_id=business_id,
        idea_id=idea_id,
        conversation_summary_json={},
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_chat_session(db: Session, db_obj: ChatSession, obj_in: Any) -> ChatSession:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_chat_session(db: Session, id: UUID) -> Optional[ChatSession]:
    db_obj = get_chat_session(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# ChatMessage
# ----------------------------

def get_chat_message(db: Session, id: UUID) -> Optional[ChatMessage]:
    return db.query(ChatMessage).filter(ChatMessage.id == id).first()


def get_chat_messages(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[ChatMessage]:
    query = db.query(ChatMessage)
    if user_id is not None:
        query = query.join(ChatSession, ChatMessage.session_id == ChatSession.id).filter(ChatSession.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def add_message(db: Session, session_id: UUID, role: ChatRole, content: str) -> ChatMessage:
    db_obj = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_chat_message(db: Session, db_obj: ChatMessage, obj_in: Any) -> ChatMessage:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_chat_message(db: Session, id: UUID) -> Optional[ChatMessage]:
    db_obj = get_chat_message(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def get_session_history(db: Session, session_id: UUID, limit: int = 50) -> List[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )





def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "chat_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("chat_service reset_internal_state called")
