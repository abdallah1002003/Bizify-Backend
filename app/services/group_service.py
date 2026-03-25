import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.database import SessionLocal
from app.models.business import Business
from app.models.group import Group
from app.models.group_member import GroupMember, GroupRole, GroupMemberStatus
from app.models.group_invite import GroupInvite, GroupInviteStatus
from app.models.group_join_request import GroupJoinRequest, GroupJoinRequestStatus
from app.models.idea import Idea
from app.models.user import User
from app.services.notification_service import NotificationService
from app.core.mail import send_team_invite_email, send_join_request_status_email

logger = logging.getLogger(__name__)

class GroupService:
    """
    Unified service for managing Groups, Group Members, Invites, and Join Requests.
    Replaces the legacy 'Collaborator' and 'Team' services into a single unified architecture.
    """

    @staticmethod
    def _is_group_admin(group: Group, requester_id: uuid.UUID) -> bool:
        if group.business.owner_id == requester_id:
            return True
        for member in group.members:
            if member.user_id == requester_id and member.role == GroupRole.OWNER and member.status == GroupMemberStatus.ACTIVE:
                return True
        return False

    @staticmethod
    def create_team(db: Session, creator_id: uuid.UUID, data: Any) -> Group:
        """
        Creates a new team for the authenticated user without requiring a pre-existing business.
        A lightweight business container is created automatically to satisfy the current schema.
        """
        business = Business(owner_id = creator_id)
        db.add(business)
        db.flush()

        group = Group(
            business_id = business.id,
            name = data.name,
            description = data.description,
            default_role = data.default_role,
            is_chat_enabled = data.is_chat_enabled,
        )
        db.add(group)
        db.commit()
        db.refresh(group)

        GroupService.invalidate_group_cache(business.id)

        return group

    @staticmethod
    def create_group(db: Session, business_id: uuid.UUID, creator_id: uuid.UUID, data: Any) -> Group:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business or business.owner_id != creator_id:
            raise HTTPException(status_code=403, detail="Only the business owner can create groups")

        group = Group(
            business_id = business_id,
            name = data.name,
            description = data.description,
            default_role = data.default_role,
            is_chat_enabled = data.is_chat_enabled,
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        
        # Invalidate cache if needed
        GroupService.invalidate_group_cache(business_id)
        
        return group

    @staticmethod
    def update_group(db: Session, group_id: uuid.UUID, requester_id: uuid.UUID, data: Any) -> Group:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
            
        if not GroupService._is_group_admin(group, requester_id):
            raise HTTPException(status_code=403, detail="Only group admins can update the group")
            
        if data.name is not None:
            group.name = data.name
        if data.description is not None:
            group.description = data.description
        if data.default_role is not None:
            group.default_role = data.default_role
        if data.is_chat_enabled is not None:
            group.is_chat_enabled = data.is_chat_enabled
            
        db.commit()
        db.refresh(group)
        GroupService.invalidate_group_cache(group.business_id)
        return group

    @staticmethod
    def delete_group(db: Session, group_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Only the business owner or GroupRole.OWNER can delete a group
        if not GroupService._is_group_admin(group, requester_id):
            raise HTTPException(status_code=403, detail="Only group admins can delete the group")
            
        business_id = group.business_id
        db.delete(group)
        db.commit()
        
        GroupService.invalidate_group_cache(business_id)

    @staticmethod
    def invalidate_group_cache(business_id: uuid.UUID) -> None:
        cache.delete_pattern(f"groups:{business_id}:*")
        cache.delete_pattern(f"group_members:*")

    @staticmethod
    def get_groups(db: Session, business_id: uuid.UUID, requester_id: uuid.UUID) -> List[Group]:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        is_owner = business.owner_id == requester_id
        is_member = db.query(GroupMember).join(Group).filter(
            Group.business_id == business_id,
            GroupMember.user_id == requester_id,
            GroupMember.status == GroupMemberStatus.ACTIVE
        ).first()

        if not is_owner and not is_member:
            raise HTTPException(status_code=403, detail="You do not have access to this business")

        return db.query(Group).filter(Group.business_id == business_id).all()

    @staticmethod
    def get_user_teams(db: Session, user_id: uuid.UUID) -> List[Group]:
        """
        Returns all teams the user owns or is an active member of.
        """
        owned_groups = db.query(Group).join(Business).filter(Business.owner_id == user_id).all()
        member_groups = db.query(Group).join(GroupMember).filter(
            GroupMember.user_id == user_id,
            GroupMember.status == GroupMemberStatus.ACTIVE
        ).all()

        unique_groups = {group.id: group for group in owned_groups + member_groups}

        return list(unique_groups.values())

    @staticmethod
    def create_invite(
        db: Session, 
        group_id: uuid.UUID, 
        invited_by: uuid.UUID, 
        email: str,
        role: Optional[GroupRole] = None,
        idea_ids: Optional[List[uuid.UUID]] = None
    ) -> Dict[str, Any]:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
            
        if not GroupService._is_group_admin(group, invited_by):
            raise HTTPException(status_code=403, detail="Only group admins can invite members")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        invite = GroupInvite(
            group_id=group_id,
            email=email,
            token=token,
            invited_by=invited_by,
            expires_at=expires_at,
            role=role if role else group.default_role,
        )
        
        if idea_ids:
            ideas = db.query(Idea).filter(Idea.id.in_(idea_ids), Idea.business_id == group.business_id).all()
            invite.accessible_ideas.extend(ideas)
            
        db.add(invite)
        db.commit()
        
        # Send Email
        inviter = db.query(User).filter(User.id == invited_by).first()
        send_team_invite_email(email, group.name, inviter.email, f"https://bizify.app/join-group?token={token}")
        
        return {"message": "Invite generated successfully", "token": token, "email": email}

    @staticmethod
    async def process_invite(db: Session, token: str, user_id: uuid.UUID, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        invite = db.query(GroupInvite).filter(GroupInvite.token == token, GroupInvite.status == GroupInviteStatus.PENDING).first()
        
        if not invite or invite.expires_at < datetime.now(timezone.utc):
            if invite:
                invite.status = GroupInviteStatus.EXPIRED
                db.commit()
            raise HTTPException(status_code=400, detail="Invalid or expired invitation")
            
        # Check if already in group
        existing = db.query(GroupMember).filter(GroupMember.group_id == invite.group_id, GroupMember.user_id == user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already in this group")
            
        member = GroupMember(
            group_id=invite.group_id,
            user_id=user_id,
            role=invite.role,
        )
        
        # Transfer ideas from invite
        member.accessible_ideas.extend(invite.accessible_ideas)
        
        invite.status = GroupInviteStatus.ACCEPTED
        db.add(member)
        db.commit()
        
        GroupService.invalidate_group_cache(invite.group.business_id)
        
        return {"message": "Successfully joined the group", "group_id": invite.group_id}

    @staticmethod
    def create_join_request(db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
            
        existing = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Already a member")
            
        req = GroupJoinRequest(group_id=group_id, user_id=user_id, status=GroupJoinRequestStatus.PENDING)
        db.add(req)
        db.commit()
        
        return {"message": "Request sent successfully"}

    @staticmethod
    async def handle_join_request(
        db: Session, request_id: uuid.UUID, owner_id: uuid.UUID, 
        is_approved: bool, role: Optional[GroupRole] = None, idea_ids: Optional[List[uuid.UUID]] = None,
        background_tasks: BackgroundTasks = None
    ) -> Dict[str, Any]:
        req = db.query(GroupJoinRequest).filter(GroupJoinRequest.id == request_id).first()
        if not req or req.status != GroupJoinRequestStatus.PENDING:
            raise HTTPException(status_code=404, detail="Request not found or already processed")
            
        if not GroupService._is_group_admin(req.group, owner_id):
            raise HTTPException(status_code=403, detail="Only group admins can handle requests")
            
        if is_approved:
            req.status = GroupJoinRequestStatus.APPROVED
            member = GroupMember(
                group_id=req.group_id,
                user_id=req.user_id,
                role=role if role else req.group.default_role
            )
            if idea_ids:
                ideas = db.query(Idea).filter(Idea.id.in_(idea_ids), Idea.business_id == req.group.business_id).all()
                member.accessible_ideas.extend(ideas)
            db.add(member)
        else:
            req.status = GroupJoinRequestStatus.REJECTED
            
        db.commit()
        GroupService.invalidate_group_cache(req.group.business_id)
        return {"message": f"Request {req.status.value}", "status": req.status}

    @staticmethod
    def get_group_members(db: Session, group_id: uuid.UUID, requester_id: uuid.UUID) -> List[GroupMember]:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
            
        # Optional: Auth check
        is_owner = group.business.owner_id == requester_id
        is_member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == requester_id).first()
        
        if not is_owner and not is_member:
            raise HTTPException(status_code=403, detail="Access denied")
            
        return db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.status == GroupMemberStatus.ACTIVE).all()

    @staticmethod
    def update_group_member(
        db: Session, 
        member_id: uuid.UUID, 
        requester_id: uuid.UUID, 
        role: Optional[GroupRole] = None, 
        idea_ids: Optional[List[uuid.UUID]] = None
    ) -> GroupMember:
        member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
            
        if not GroupService._is_group_admin(member.group, requester_id):
            raise HTTPException(status_code=403, detail="Only group admins can update member permissions")
            
        if role is not None:
            member.role = role
            
        if idea_ids is not None:
            # Clear old and set new
            ideas = db.query(Idea).filter(Idea.id.in_(idea_ids), Idea.business_id == member.group.business_id).all()
            member.accessible_ideas = ideas
            
        db.commit()
        db.refresh(member)
        GroupService.invalidate_group_cache(member.group.business_id)
        return member

    @staticmethod
    def remove_group_member(db: Session, member_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
            
        if not GroupService._is_group_admin(member.group, requester_id):
            raise HTTPException(status_code=403, detail="Only group admins can remove members")
            
        member.status = GroupMemberStatus.REMOVAL_PENDING
        db.delete(member)
        db.commit()
        GroupService.invalidate_group_cache(member.group.business_id)
