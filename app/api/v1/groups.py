from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.repositories.group_repo import group_repo
from app.schemas.group import (
    GroupCreate,
    GroupInviteCreate,
    GroupInviteResponse,
    GroupJoinRequestResponse,
    GroupMemberResponse,
    GroupMemberSkillRoleUpdate,
    GroupMemberUpdate,
    GroupResponse,
    GroupUpdate,
    HandleJoinRequest,
)
from app.schemas.group_message import GroupMessageCreate, GroupMessageResponse
from app.services.group_message_service import GroupMessageService
from app.services.group_service import GroupService
from app.services.notification_service import NotificationService
from app.services.user_service import UserService
from app.sockets.group_manager import group_manager

router = APIRouter()


def _build_member_response(member: Any) -> dict[str, Any]:
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
        "skill_role": getattr(member, "skill_role", None),
    }


@router.post("/groups", response_model=GroupResponse)
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    """Create a group for the authenticated user."""
    return GroupService.create_team(db, current_user.id, data)


@router.get("/groups", response_model=list[GroupResponse])
def get_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GroupResponse]:
    """Return groups owned by or shared with the authenticated user."""
    return GroupService.get_user_teams(db, current_user.id)


@router.get("/groups/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    """Return a single group the user can access."""
    group = group_repo.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    is_owner = group.business.owner_id == current_user.id
    is_member = group_repo.is_active_member(db, group_id, current_user.id)
    if not is_owner and not is_member:
        raise HTTPException(status_code=403, detail="Access denied")
    return group


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
) -> dict[str, str]:
    """Delete a group the user can manage."""
    GroupService.delete_group(db, group_id, current_user.id)
    return {"message": "Group deleted successfully"}


@router.post("/groups/{group_id}/invites")
def create_invite(
    group_id: UUID,
    data: GroupInviteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create an invite for a group."""
    return GroupService.create_invite(
        db,
        group_id,
        current_user.id,
        data.email,
        data.role,
        data.idea_ids,
        background_tasks,
    )


@router.post("/groups/invites/accept")
async def process_invite(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Accept a group invite."""
    return await GroupService.process_invite(db, token, current_user.id, background_tasks)


@router.post("/groups/{group_id}/join-requests")
def create_join_request(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a join request for a group."""
    return GroupService.create_join_request(db, group_id, current_user.id)


@router.post("/groups/join-requests/{request_id}/handle")
async def handle_join_request(
    request_id: UUID,
    data: HandleJoinRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
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


@router.get("/groups/{group_id}/members", response_model=list[GroupMemberResponse])
def get_members(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GroupMemberResponse]:
    """Return active members for a group."""
    members = GroupService.get_group_members(db, group_id, current_user.id)
    return [_build_member_response(member) for member in members]


@router.get("/groups/{group_id}/members/{member_id}", response_model=GroupMemberResponse)
def get_member(
    group_id: UUID,
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMemberResponse:
    """Return a single group member."""
    group = group_repo.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    GroupService.get_group_members(db, group_id, current_user.id)
    member = group_repo.get_member_by_id(db, member_id)
    if not member or member.group_id != group_id:
        raise HTTPException(status_code=404, detail="Member not found")
    return _build_member_response(member)


@router.get("/groups/{group_id}/invites", response_model=list[GroupInviteResponse])
def get_group_invites(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GroupInviteResponse]:
    """Return all invites for a group (admin only)."""
    group = group_repo.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    GroupService._ensure_group_admin(group, current_user.id)
    return group_repo.get_group_invites(db, group_id)


@router.get("/groups/{group_id}/join-requests", response_model=list[GroupJoinRequestResponse])
def get_group_join_requests(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GroupJoinRequestResponse]:
    """Return all join requests for a group (admin only)."""
    group = group_repo.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    GroupService._ensure_group_admin(group, current_user.id)
    requests = group_repo.get_group_join_requests(db, group_id)
    return [
        {
            "id": r.id,
            "group_id": r.group_id,
            "user_id": r.user_id,
            "email": r.user.email,
            "role": r.role,
            "status": r.status,
            "created_at": r.created_at,
            "accessible_ideas": r.accessible_ideas or [],
        }
        for r in requests
    ]


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


@router.patch("/groups/{group_id}/members/{member_id}/skill-role", response_model=GroupMemberResponse)
async def assign_skill_role(
    group_id: UUID,
    member_id: UUID,
    data: GroupMemberSkillRoleUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMemberResponse:
    """Assign a skill-gap role to a team member. Only the group owner can do this."""
    group = group_repo.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    GroupService._ensure_group_admin(group, current_user.id)

    member = group_repo.get_member_by_id(db, member_id)
    if not member or str(member.group_id) != str(group_id):
        raise HTTPException(status_code=404, detail="Member not found")

    member.skill_role = data.skill_role
    db.add(member)
    db.commit()
    db.refresh(member)

    await NotificationService.notify_user(
        db=db,
        user_id=member.user_id,
        title="New role assigned",
        content=(
            f"{current_user.full_name or current_user.email} assigned you the role "
            f'"{data.skill_role}" in team "{group.name}".'
        ),
        notify_type="team_update",
        background_tasks=background_tasks,
    )

    return _build_member_response(member)


@router.delete("/groups/members/{member_id}")
def remove_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Remove a member from a group."""
    GroupService.remove_group_member(db, member_id, current_user.id)
    return {"message": "Member removed successfully"}


@router.get("/groups/{group_id}/messages", response_model=list[GroupMessageResponse])
def get_group_messages(
    group_id: UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GroupMessageResponse]:
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
