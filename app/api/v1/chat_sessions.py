import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.api.dependencies import get_current_user, get_db
from app.models.ai.chat_message import ChatMessage, MessageRole
from app.models.ai.chat_session import ChatSession, SessionType
from app.models.user import User

router = APIRouter()


# ─── Request / Response schemas ───────────────────────────────────────────────

class SessionCreate(BaseModel):
    section_slug: Optional[str] = None   # None → general chat
    idea_id: Optional[uuid.UUID] = None
    title: Optional[str] = None


class MessageIn(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class MessagesIn(BaseModel):
    messages: list[MessageIn]


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class SessionOut(BaseModel):
    id: str
    section_slug: Optional[str]
    title: str
    preview: str
    created_at: str


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _session_out(s: ChatSession) -> dict:
    meta: dict = s.conversation_summary_json or {}
    return {
        "id": str(s.id),
        "section_slug": meta.get("section"),
        "idea_id": str(s.idea_id) if s.idea_id else None,
        "title": meta.get("title", "New conversation"),
        "preview": meta.get("preview", ""),
        "created_at": s.created_at.isoformat() if s.created_at else "",
    }


def _message_out(m: ChatMessage) -> dict:
    return {
        "id": str(m.id),
        "role": "user" if m.role == MessageRole.USER else "assistant",
        "content": m.content,
        "created_at": m.created_at.isoformat() if m.created_at else "",
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/sessions", tags=["Chat Sessions"])
def list_sessions(
    section_slug: Optional[str] = Query(default=None),
    idea_id: Optional[uuid.UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
    if idea_id:
        q = q.filter(ChatSession.idea_id == idea_id)
    sessions = q.order_by(ChatSession.created_at.desc()).all()
    # Filter by section_slug in Python (stored in JSON field)
    if section_slug is not None:
        sessions = [s for s in sessions if (s.conversation_summary_json or {}).get("section") == section_slug]
    return [_session_out(s) for s in sessions]


@router.post("/sessions", status_code=status.HTTP_201_CREATED, tags=["Chat Sessions"])
def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    title = body.title or (
        f"{body.section_slug.replace('-', ' ').title()} Chat"
        if body.section_slug
        else "New conversation"
    )
    meta: dict[str, Any] = {"title": title, "preview": "", "section": body.section_slug}

    session = ChatSession(
        user_id=current_user.id,
        idea_id=body.idea_id,
        session_type=SessionType.GENERAL,
        conversation_summary_json=meta,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_out(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chat Sessions"])
def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()


@router.get("/sessions/{session_id}/messages", tags=["Chat Sessions"])
def get_messages(
    session_id: uuid.UUID,
    limit: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    q = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    messages = q.all()
    if limit > 0:
        messages = messages[-limit:]
    return [_message_out(m) for m in messages]


@router.post("/sessions/{session_id}/messages", tags=["Chat Sessions"])
def save_messages(
    session_id: uuid.UUID,
    body: MessagesIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    saved = []
    for msg in body.messages:
        role = MessageRole.USER if msg.role.lower() == "user" else MessageRole.AI
        m = ChatMessage(session_id=session_id, role=role, content=msg.content)
        db.add(m)
        saved.append(m)

    # Update preview in session metadata
    last_user = next((m for m in reversed(body.messages) if m.role.lower() == "user"), None)
    if last_user:
        meta = dict(session.conversation_summary_json or {})
        meta["preview"] = last_user.content[:80]
        session.conversation_summary_json = meta
        flag_modified(session, "conversation_summary_json")

    db.commit()
    for m in saved:
        db.refresh(m)
    return [_message_out(m) for m in saved]
