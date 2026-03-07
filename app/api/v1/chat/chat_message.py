from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
import app.models as models
from app.api.v1.service_dependencies import get_chat_service
from app.core.dependencies import get_current_active_user
from app.schemas.chat.chat_message import ChatMessageCreate, ChatMessageUpdate, ChatMessageResponse
from app.services.chat.chat_service import ChatService

router = APIRouter()


def _ensure_chat_session_owner(session: models.ChatSession, current_user: models.User) -> None:
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


async def _resolve_owned_session(
    service: ChatService,
    session_id: UUID,
    current_user: models.User,
) -> models.ChatSession:
    session = await service.get_chat_session(id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="ChatSession not found")
    _ensure_chat_session_owner(session, current_user)
    from typing import cast
    return cast(models.ChatSession, session)


@router.get("/", response_model=List[ChatMessageResponse])
async def read_chat_messages(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: ChatService = Depends(get_chat_service),
    current_user: models.User = Depends(get_current_active_user),
) -> List[ChatMessageResponse]:
    from typing import cast
    return cast(List[ChatMessageResponse], await service.get_chat_messages(skip=skip, limit=limit, user_id=current_user.id))

@router.post("/", response_model=ChatMessageResponse)
async def create_chat_message(
    item_in: ChatMessageCreate,
    service: ChatService = Depends(get_chat_service),
    current_user: models.User = Depends(get_current_active_user),
):
    """Elite API: Appends a message to an active chat thread."""
    await _resolve_owned_session(service, session_id=item_in.session_id, current_user=current_user)
    return await service.add_message(
        session_id=item_in.session_id,
        role=item_in.role,
        content=item_in.content,
    )

@router.get("/{id}", response_model=ChatMessageResponse)
async def read_chat_message(
    id: UUID,
    service: ChatService = Depends(get_chat_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_chat_message(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ChatMessage not found")
    await _resolve_owned_session(service, session_id=db_obj.session_id, current_user=current_user)
    return db_obj

@router.put("/{id}", response_model=ChatMessageResponse)
async def update_chat_message(
    id: UUID,
    item_in: ChatMessageUpdate,
    service: ChatService = Depends(get_chat_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_chat_message(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ChatMessage not found")
    await _resolve_owned_session(service, session_id=db_obj.session_id, current_user=current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("session_id", None)
    return await service.update_chat_message(db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=ChatMessageResponse)
async def delete_chat_message(
    id: UUID,
    service: ChatService = Depends(get_chat_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_chat_message(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ChatMessage not found")
    await _resolve_owned_session(service, session_id=db_obj.session_id, current_user=current_user)
    return await service.delete_chat_message(id=id)
