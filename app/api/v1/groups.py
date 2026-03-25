import logging
import uuid
from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.group_member import GroupMemberStatus, GroupMember
from app.schemas.group import (
    GroupCreate,
    GroupResponse,
    GroupUpdate,
    HandleJoinRequest,
    GroupInviteCreate,
    GroupInviteResponse,
    GroupMemberResponse,
    GroupMemberUpdate,
)
from app.schemas.group_message import GroupMessageResponse, GroupMessageCreate
from app.services.group_service import GroupService
from app.services.group_message_service import GroupMessageService
from app.sockets.group_manager import group_manager
from app.services.user_service import UserService
from app.models.group import Group
from jose import jwt, JWTError
from app.core.config import settings
from app.services.user_service import UserService
from fastapi import status

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/groups", response_model=GroupResponse)
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates a group for the authenticated user without requiring a business ID.
    """
    return GroupService.create_team(db, current_user.id, data)

@router.get("/groups", response_model=List[GroupResponse])
def get_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieves all groups owned by or shared with the authenticated user.
    """
    return GroupService.get_user_teams(db, current_user.id)

@router.patch("/groups/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: uuid.UUID,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return GroupService.update_group(db, group_id, current_user.id, data)

@router.delete("/groups/{group_id}")
def delete_group(
    group_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    GroupService.delete_group(db, group_id, current_user.id)
    return {"message": "Group deleted successfully"}

@router.post("/groups/{group_id}/invites")
def create_invite(
    group_id: uuid.UUID,
    data: GroupInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return GroupService.create_invite(db, group_id, current_user.id, data.email, data.role, data.idea_ids)

@router.post("/groups/invites/accept")
async def process_invite(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return await GroupService.process_invite(db, token, current_user.id, background_tasks)

@router.post("/groups/{group_id}/join-requests")
def create_join_request(
    group_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return GroupService.create_join_request(db, group_id, current_user.id)

@router.post("/groups/join-requests/{request_id}/handle")
async def handle_join_request(
    request_id: uuid.UUID,
    data: HandleJoinRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return await GroupService.handle_join_request(
        db, request_id, current_user.id, data.is_approved, data.role, data.idea_ids, background_tasks
    )

@router.get("/groups/{group_id}/members", response_model=List[GroupMemberResponse])
def get_members(
    group_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    members = GroupService.get_group_members(db, group_id, current_user.id)
    result = []
    for m in members:
        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "group_id": m.group_id,
            "email": m.user.email,
            "role": m.role,
            "status": m.status,
            "accessible_ideas": m.accessible_ideas,
            "joined_at": m.joined_at
        })
    return result

@router.patch("/groups/members/{member_id}", response_model=GroupMemberResponse)
def update_member(
    member_id: uuid.UUID,
    data: GroupMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    m = GroupService.update_group_member(db, member_id, current_user.id, data.role, data.idea_ids)
    return {
        "id": m.id,
        "user_id": m.user_id,
        "group_id": m.group_id,
        "email": m.user.email,
        "role": m.role,
        "status": m.status,
        "accessible_ideas": m.accessible_ideas,
        "joined_at": m.joined_at
    }

@router.delete("/groups/members/{member_id}")
def remove_member(
    member_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    GroupService.remove_group_member(db, member_id, current_user.id)
    return {"message": "Member removed successfully"}

@router.get("/groups/{group_id}/messages", response_model=List[GroupMessageResponse])
def get_group_messages(
    group_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not group.is_chat_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat is disabled for this group")
        
    members = GroupService.get_group_members(db, group_id, current_user.id)
    return GroupMessageService.get_group_messages(db, group_id, limit, offset)

@router.post("/groups/{group_id}/messages", response_model=GroupMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_group_message(
    group_id: uuid.UUID,
    data: GroupMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not group.is_chat_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat is disabled for this group")

    GroupService.get_group_members(db, group_id, current_user.id)

    saved_msg = GroupMessageService.create_message(db, group_id, current_user.id, data.content)

    broadcast_data = {
        "id": str(saved_msg.id),
        "group_id": str(group_id),
        "sender_id": str(current_user.id),
        "sender_name": current_user.full_name or current_user.email,
        "content": saved_msg.content,
        "created_at": saved_msg.created_at.isoformat()
    }

    await group_manager.broadcast_to_group(group_id, broadcast_data)

    return saved_msg

@router.websocket("/groups/{group_id}/ws")
async def group_chat_websocket(
    websocket: WebSocket,
    group_id: uuid.UUID,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise JWTError("Invalid token")
            user_id = uuid.UUID(user_id_str)
        except JWTError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user = UserService.get_user_by_id(db, user_id)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        g = db.query(Group).filter(Group.id == group_id).first()
        if not g or not g.is_chat_enabled:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        is_authorized = False
        member_check = db.query(GroupMember).filter(
            GroupMember.group_id == group_id, 
            GroupMember.user_id == user.id,
            GroupMember.status == GroupMemberStatus.ACTIVE
        ).first()
        
        if member_check:
            is_authorized = True
        elif g.business.owner_id == user.id:
            is_authorized = True
                
        if not is_authorized:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await group_manager.connect(websocket, group_id, user.id)
        
        try:
            while True:
                data = await websocket.receive_text()
                saved_msg = GroupMessageService.create_message(db, group_id, user.id, data)
                
                broadcast_data = {
                    "id": str(saved_msg.id),
                    "group_id": str(group_id),
                    "sender_id": str(user.id),
                    "sender_name": user.full_name or user.email,
                    "content": data,
                    "created_at": saved_msg.created_at.isoformat()
                }
                
                await group_manager.broadcast_to_group(group_id, broadcast_data)
                
        except WebSocketDisconnect:
            group_manager.disconnect(group_id, user.id)
            
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
