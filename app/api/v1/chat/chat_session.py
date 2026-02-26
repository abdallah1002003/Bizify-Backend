from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.ext.asyncio import AsyncSession
import app.models as models
from app.core.dependencies import get_current_active_user, get_async_db
from app.schemas.chat.chat_session import ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse
from app.services.chat import chat_service as service

router = APIRouter()


def _ensure_chat_session_owner(session: models.ChatSession, current_user: models.User) -> None:
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[ChatSessionResponse])
async def read_chat_sessions(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_chat_sessions(db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=ChatSessionResponse)
async def create_chat_session(
    item_in: ChatSessionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Elite API: Registers a context-aware chat session."""
    return await service.create_chat_session(
        db,
        user_id=current_user.id,
        session_type=item_in.session_type,
        business_id=item_in.business_id,
        idea_id=item_in.idea_id,
    )

@router.get("/{id}", response_model=ChatSessionResponse)
async def read_chat_session(
    id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_chat_session(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ChatSession not found")
    _ensure_chat_session_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=ChatSessionResponse)
async def update_chat_session(
    id: UUID,
    item_in: ChatSessionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_chat_session(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ChatSession not found")
    _ensure_chat_session_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
    return await service.update_chat_session(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=ChatSessionResponse)
async def delete_chat_session(
    id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_chat_session(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ChatSession not found")
    _ensure_chat_session_owner(db_obj, current_user)
    return await service.delete_chat_session(db, id=id)
