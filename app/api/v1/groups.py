from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.group import (
    GroupCreate,
    GroupInviteCreate,
    GroupMemberResponse,
    GroupMemberUpdate,
    GroupResponse,
    GroupUpdate,
    HandleJoinRequest,
)
from app.schemas.group_message import GroupMessageCreate, GroupMessageResponse
from app.services.group_message_service import GroupMessageService
from app.services.group_service import GroupService
from app.services.user_service import UserService
from app.sockets.group_manager import group_manager

router = APIRouter()


def _build_member_response(member: Any) -> Dict[str, Any]:
    """Serialize a group member model into the response shape."""
    return {
        "id": member.id,
        "user_id": member.user_id,
        "group_id": member.group_id,
        "email": member.user.email,
        "role": member.role,
        "status": member.status,
        "accessible_ideas": member.accessible_ideas,
        "joined_at": member.joined_at,
    }


@router.post("/groups", response_model=GroupResponse)
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    """Create a group for the authenticated user."""
    return GroupService.create_team(db, current_user.id, data)


@router.get("/groups", response_model=List[GroupResponse])
def get_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[GroupResponse]:
    """Return groups owned by or shared with the authenticated user."""
    return GroupService.get_user_teams(db, current_user.id)


@router.patch("/groups/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: UUID,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    """Update a group the user can manage."""
    return GroupService.update_group(db, group_id, current_user.id, data)


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a group the user can manage."""
    GroupService.delete_group(db, group_id, current_user.id)
    return {"message": "Group deleted successfully"}


@router.post("/groups/{group_id}/invites")
def create_invite(
    group_id: UUID,
    data: GroupInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create an invite for a group."""
    return GroupService.create_invite(
        db,
        group_id,
        current_user.id,
        data.email,
        data.role,
        data.idea_ids,
    )


@router.post("/groups/invites/accept")
async def process_invite(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Accept a group invite."""
    return await GroupService.process_invite(db, token, current_user.id, background_tasks)


@router.post("/groups/{group_id}/join-requests")
def create_join_request(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a join request for a group."""
    return GroupService.create_join_request(db, group_id, current_user.id)


@router.post("/groups/join-requests/{request_id}/handle")
async def handle_join_request(
    request_id: UUID,
    data: HandleJoinRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Approve or reject a join request."""
    return await GroupService.handle_join_request(
        db,
        request_id,
        current_user.id,
        data.is_approved,
        data.role,
        data.idea_ids,
        background_tasks,
    )


@router.get("/groups/{group_id}/members", response_model=List[GroupMemberResponse])
def get_members(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[GroupMemberResponse]:
    """Return active members for a group."""
    members = GroupService.get_group_members(db, group_id, current_user.id)
    return [_build_member_response(member) for member in members]


@router.patch("/groups/members/{member_id}", response_model=GroupMemberResponse)
def update_member(
    member_id: UUID,
    data: GroupMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMemberResponse:
    """Update a member's role or accessible ideas."""
    member = GroupService.update_group_member(
        db,
        member_id,
        current_user.id,
        data.role,
        data.idea_ids,
    )
    return _build_member_response(member)


@router.delete("/groups/members/{member_id}")
def remove_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Remove a member from a group."""
    GroupService.remove_group_member(db, member_id, current_user.id)
    return {"message": "Member removed successfully"}


@router.get("/groups/{group_id}/messages", response_model=List[GroupMessageResponse])
def get_group_messages(
    group_id: UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[GroupMessageResponse]:
    """Return paginated messages for a group chat."""
    GroupService.get_chat_group_for_user(db, group_id, current_user.id)
    return GroupMessageService.get_group_messages(db, group_id, limit, offset)


@router.post(
    "/groups/{group_id}/messages",
    response_model=GroupMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_group_message(
    group_id: UUID,
    data: GroupMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMessageResponse:
    """Create and broadcast a group message."""
    GroupService.get_chat_group_for_user(db, group_id, current_user.id)
    saved_message = GroupMessageService.create_message(
        db,
        group_id,
        current_user.id,
        data.content,
    )

    broadcast_data = {
        "id": str(saved_message.id),
        "group_id": str(group_id),
        "sender_id": str(current_user.id),
        "sender_name": current_user.full_name or current_user.email,
        "content": saved_message.content,
        "created_at": saved_message.created_at.isoformat(),
    }
    await group_manager.broadcast_to_group(group_id, broadcast_data)
    return saved_message


@router.websocket("/groups/{group_id}/ws")
async def group_chat_websocket(
    websocket: WebSocket,
    group_id: UUID,
    token: str,
    db: Session = Depends(get_db),
) -> None:
    """Handle the group chat websocket lifecycle."""
    try:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise JWTError("Invalid token")
            user_id = UUID(user_id_str)
        except JWTError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user = UserService.get_user_by_id(db, user_id)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            GroupService.get_chat_group_for_user(db, group_id, user.id)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await group_manager.connect(websocket, group_id, user.id)
        try:
            while True:
                message_content = await websocket.receive_text()
                saved_message = GroupMessageService.create_message(
                    db,
                    group_id,
                    user.id,
                    message_content,
                )
                broadcast_data = {
                    "id": str(saved_message.id),
                    "group_id": str(group_id),
                    "sender_id": str(user.id),
                    "sender_name": user.full_name or user.email,
                    "content": message_content,
                    "created_at": saved_message.created_at.isoformat(),
                }
                await group_manager.broadcast_to_group(group_id, broadcast_data)
        except WebSocketDisconnect:
            group_manager.disconnect(group_id, user.id)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
