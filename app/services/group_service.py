import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.mail import send_team_invite_email
from app.models.group import Group
from app.models.group_invite import GroupInvite, GroupInviteStatus
from app.models.group_join_request import GroupJoinRequest, GroupJoinRequestStatus
from app.models.group_member import GroupMember, GroupMemberStatus, GroupRole
from app.repositories.business_repo import business_repo
from app.repositories.group_repo import group_repo
from app.repositories.idea_repo import idea_repo
from app.repositories.user_repo import user_repo


class GroupService:
    """Group, invite, and membership workflows."""

    @staticmethod
    def _is_group_admin(group: Group, requester_id: uuid.UUID) -> bool:
        """Return whether the requester can administer the group."""
        if group.business.owner_id == requester_id:
            return True

        for member in group.members:
            if (
                member.user_id == requester_id
                and member.role == GroupRole.OWNER
                and member.status == GroupMemberStatus.ACTIVE
            ):
                return True

        return False

    @staticmethod
    def _ensure_group_admin(group: Group, requester_id: uuid.UUID) -> None:
        """Raise when the requester is not allowed to manage the group."""
        if not GroupService._is_group_admin(group, requester_id):
            raise HTTPException(
                status_code=403,
                detail="Only group admins can manage this group",
            )

    @staticmethod
    def create_team(db: Session, creator_id: uuid.UUID, data: Any) -> Group:
        """Create a lightweight team backed by a new business container."""
        business = business_repo.create(
            db,
            obj_in={"owner_id": creator_id},
            commit=False,
            refresh=False,
        )
        group = group_repo.create(
            db,
            obj_in={
                "business_id": business.id,
                "name": data.name,
                "description": data.description,
                "default_role": data.default_role,
                "is_chat_enabled": data.is_chat_enabled,
            },
            commit=False,
            refresh=False,
        )
        db.commit()
        db.refresh(group)
        GroupService.invalidate_group_cache(business.id)
        return group

    @staticmethod
    def create_group(
        db: Session,
        business_id: uuid.UUID,
        creator_id: uuid.UUID,
        data: Any,
    ) -> Group:
        """Create a group inside a business owned by the requester."""
        business = business_repo.get(db, business_id)
        if not business or business.owner_id != creator_id:
            raise HTTPException(
                status_code=403,
                detail="Only the business owner can create groups",
            )

        group = group_repo.create(
            db,
            obj_in={
                "business_id": business_id,
                "name": data.name,
                "description": data.description,
                "default_role": data.default_role,
                "is_chat_enabled": data.is_chat_enabled,
            },
        )
        GroupService.invalidate_group_cache(business_id)
        return group

    @staticmethod
    def update_group(
        db: Session,
        group_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: Any,
    ) -> Group:
        """Update a group's editable fields."""
        group = group_repo.get_by_id(db, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        GroupService._ensure_group_admin(group, requester_id)

        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.description is not None:
            update_data["description"] = data.description
        if data.default_role is not None:
            update_data["default_role"] = data.default_role
        if data.is_chat_enabled is not None:
            update_data["is_chat_enabled"] = data.is_chat_enabled

        group = group_repo.update(db, db_obj=group, obj_in=update_data)
        GroupService.invalidate_group_cache(group.business_id)
        return group

    @staticmethod
    def delete_group(db: Session, group_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        """Delete a group managed by the requester."""
        group = group_repo.get_by_id(db, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        GroupService._ensure_group_admin(group, requester_id)

        business_id = group.business_id
        group_repo.remove(db, id=group_id)
        GroupService.invalidate_group_cache(business_id)

    @staticmethod
    def invalidate_group_cache(business_id: uuid.UUID) -> None:
        """Clear cached group and membership views."""
        cache.delete_pattern(f"groups:{business_id}:*")
        cache.delete_pattern("group_members:*")

    @staticmethod
    def get_groups(db: Session, business_id: uuid.UUID, requester_id: uuid.UUID) -> List[Group]:
        """Return all groups inside a business the requester can access."""
        business = business_repo.get(db, business_id)
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        is_owner = business.owner_id == requester_id
        is_member = group_repo.is_member_of_business(db, business_id, requester_id)
        if not is_owner and not is_member:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this business",
            )

        return group_repo.get_by_business_id(db, business_id)

    @staticmethod
    def get_chat_group_for_user(db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> Group:
        """Return a chat-enabled group when the user has access."""
        group = group_repo.get_by_id(db, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        if not group.is_chat_enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chat is disabled for this group",
            )

        is_authorized = group.business.owner_id == user_id or group_repo.is_active_member(
            db,
            group_id,
            user_id,
        )
        if not is_authorized:
            raise HTTPException(status_code=403, detail="Access denied")

        return group

    @staticmethod
    def get_user_teams(db: Session, user_id: uuid.UUID) -> List[Group]:
        """Return teams the user owns or actively belongs to."""
        owned_groups = group_repo.get_user_owned_groups(db, user_id)
        member_groups = group_repo.get_user_member_groups(db, user_id)
        unique_groups = {group.id: group for group in owned_groups + member_groups}
        return list(unique_groups.values())

    @staticmethod
    def create_invite(
        db: Session,
        group_id: uuid.UUID,
        invited_by: uuid.UUID,
        email: str,
        role: Optional[GroupRole] = None,
        idea_ids: Optional[List[uuid.UUID]] = None,
    ) -> Dict[str, Any]:
        """Create an invite for a group member."""
        group = group_repo.get_by_id(db, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        GroupService._ensure_group_admin(group, invited_by)

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invite = GroupInvite(
            group_id=group_id,
            email=email,
            token=token,
            invited_by=invited_by,
            expires_at=expires_at,
            role=role or group.default_role,
        )

        if idea_ids:
            ideas = idea_repo.get_by_ids_in_business(db, idea_ids, group.business_id)
            invite.accessible_ideas.extend(ideas)

        group_repo.create_invite(db, invite)

        inviter = user_repo.get(db, invited_by)
        inviter_email = inviter.email if inviter else "Bizify"
        send_team_invite_email(
            email,
            group.name,
            inviter_email,
            f"https://bizify.app/join-group?token={token}",
        )

        return {
            "message": "Invite generated successfully",
            "token": token,
            "email": email,
        }

    @staticmethod
    async def process_invite(
        db: Session,
        token: str,
        user_id: uuid.UUID,
        _background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Accept a pending group invite."""
        invite = group_repo.get_pending_invite_by_token(db, token)
        if not invite or invite.expires_at < datetime.now(timezone.utc):
            if invite:
                invite.status = GroupInviteStatus.EXPIRED
                group_repo.save_invite(db, invite)
            raise HTTPException(status_code=400, detail="Invalid or expired invitation")

        existing_member = group_repo.get_member_by_user_and_group(db, invite.group_id, user_id)
        if existing_member:
            raise HTTPException(status_code=400, detail="User already in this group")

        member = GroupMember(group_id=invite.group_id, user_id=user_id, role=invite.role)
        member.accessible_ideas.extend(invite.accessible_ideas)
        invite.status = GroupInviteStatus.ACCEPTED

        group_repo.create_member(db, member, commit=False)
        group_repo.save_invite(db, invite, commit=False)
        db.commit()
        db.refresh(member)
        GroupService.invalidate_group_cache(invite.group.business_id)

        return {"message": "Successfully joined the group", "group_id": invite.group_id}

    @staticmethod
    def create_join_request(db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        """Create a join request for a group."""
        group = group_repo.get_by_id(db, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        existing_member = group_repo.get_member_by_user_and_group(db, group_id, user_id)
        if existing_member:
            raise HTTPException(status_code=400, detail="Already a member")

        join_request = GroupJoinRequest(
            group_id=group_id,
            user_id=user_id,
            status=GroupJoinRequestStatus.PENDING,
        )
        group_repo.create_join_request(db, join_request)
        return {"message": "Request sent successfully"}

    @staticmethod
    async def handle_join_request(
        db: Session,
        request_id: uuid.UUID,
        owner_id: uuid.UUID,
        is_approved: bool,
        role: Optional[GroupRole] = None,
        idea_ids: Optional[List[uuid.UUID]] = None,
        _background_tasks: Optional[BackgroundTasks] = None,
    ) -> Dict[str, Any]:
        """Approve or reject a pending join request."""
        join_request = group_repo.get_pending_join_request(db, request_id)
        if not join_request:
            raise HTTPException(status_code=404, detail="Request not found or already processed")

        GroupService._ensure_group_admin(join_request.group, owner_id)

        if is_approved:
            join_request.status = GroupJoinRequestStatus.APPROVED
            member = GroupMember(
                group_id=join_request.group_id,
                user_id=join_request.user_id,
                role=role or join_request.group.default_role,
            )
            if idea_ids:
                ideas = idea_repo.get_by_ids_in_business(
                    db,
                    idea_ids,
                    join_request.group.business_id,
                )
                member.accessible_ideas.extend(ideas)
            group_repo.create_member(db, member, commit=False)
        else:
            join_request.status = GroupJoinRequestStatus.REJECTED

        group_repo.save_join_request(db, join_request, commit=False)
        db.commit()
        GroupService.invalidate_group_cache(join_request.group.business_id)
        return {
            "message": f"Request {join_request.status.value}",
            "status": join_request.status,
        }

    @staticmethod
    def get_group_members(
        db: Session,
        group_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> List[GroupMember]:
        """Return active group members when the requester has access."""
        group = group_repo.get_by_id(db, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        is_owner = group.business.owner_id == requester_id
        is_member = group_repo.is_active_member(db, group_id, requester_id)
        if not is_owner and not is_member:
            raise HTTPException(status_code=403, detail="Access denied")

        return group_repo.get_active_members(db, group_id)

    @staticmethod
    def update_group_member(
        db: Session,
        member_id: uuid.UUID,
        requester_id: uuid.UUID,
        role: Optional[GroupRole] = None,
        idea_ids: Optional[List[uuid.UUID]] = None,
    ) -> GroupMember:
        """Update a member's role or scoped idea access."""
        member = group_repo.get_member_by_id(db, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        GroupService._ensure_group_admin(member.group, requester_id)

        if role is not None:
            member.role = role

        if idea_ids is not None:
            ideas = idea_repo.get_by_ids_in_business(db, idea_ids, member.group.business_id)
            member.accessible_ideas = ideas

        updated_member = group_repo.save_member(db, member)
        GroupService.invalidate_group_cache(member.group.business_id)
        return updated_member

    @staticmethod
    def remove_group_member(db: Session, member_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        """Remove a member from the group."""
        member = group_repo.get_member_by_id(db, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        GroupService._ensure_group_admin(member.group, requester_id)
        group_repo.remove_member(db, member)
        GroupService.invalidate_group_cache(member.group.business_id)
