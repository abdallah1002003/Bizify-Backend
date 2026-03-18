import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.database import SessionLocal
from app.core.mail import send_join_request_status_email, send_team_invite_email
from app.models.admin_action_log import AdminActionLog
from app.models.business import Business
from app.models.business_collaborator import BusinessCollaborator, CollaboratorRole, CollaboratorStatus
from app.models.business_invite import BusinessInvite, InviteStatus
from app.models.business_join_request import BusinessJoinRequest, JoinRequestStatus
from app.models.idea import Idea
from app.models.idea_comparison import IdeaComparison
from app.models.security_log import SecurityLog
from app.models.user import User
from app.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


class TeamService:
    """
    Service class for managing team invitations and collaborators.
    Handles the lifecycle of invites, join requests, and member management.
    """

    @staticmethod
    def get_invite_by_token(db: Session, token: str) -> BusinessInvite:
        """
        Retrieves a pending business invitation by its token.
        Updates status to EXPIRED if time limits are exceeded.
        """
        invite = db.query(BusinessInvite).filter(BusinessInvite.token == token).first()
        
        if not invite:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Invitation not found"
            )
        
        if invite.status != InviteStatus.PENDING:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = f"Invitation is already {invite.status}"
            )
        
        if invite.expires_at < datetime.now(timezone.utc):
            invite.status = InviteStatus.EXPIRED
            db.commit()
            
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Invitation has expired"
            )
            
        return invite

    @staticmethod
    async def accept_invitation(
        db: Session, 
        token: str, 
        user_id: uuid.UUID,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Accepts an invitation. 
        Creates a Join Request if approval is required, otherwise adds user directly.
        """
        invite = TeamService.get_invite_by_token(db, token)
        
        is_existing_member = db.query(BusinessCollaborator).filter(
            BusinessCollaborator.business_id == invite.business_id,
            BusinessCollaborator.user_id == user_id
        ).first()
        
        if is_existing_member:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "You are already a member of this team"
            )

        if invite.requires_approval:
            is_pending_request = db.query(BusinessJoinRequest).filter(
                BusinessJoinRequest.business_id == invite.business_id,
                BusinessJoinRequest.user_id == user_id,
                BusinessJoinRequest.status == JoinRequestStatus.PENDING
            ).first()
            
            if is_pending_request:
                return {
                    "message": "Your join request is already pending approval", 
                    "status": "pending"
                }

            join_request = BusinessJoinRequest(
                business_id = invite.business_id,
                user_id = user_id,
                status = JoinRequestStatus.PENDING,
                role = invite.role
            )
            
            if invite.accessible_ideas:
                join_request.accessible_ideas = list(invite.accessible_ideas)
                
            db.add(join_request)
            db.commit()
            
            return {
                "message": "Join request sent! The project owner needs to approve your access.",
                "status": "request_sent",
                "accessible_ideas": [i.id for i in join_request.accessible_ideas]
            }

        collaborator = BusinessCollaborator(
            business_id = invite.business_id,
            user_id = user_id,
            role = invite.role
        )
        
        if invite.accessible_ideas:
            collaborator.accessible_ideas = list(invite.accessible_ideas)
            
        db.add(collaborator)
        
        if invite.email:
            invite.status = InviteStatus.ACCEPTED
            
        db.commit()
        
        # UC_15: Notify Owner about direct join
        new_member = db.query(User).filter(User.id == user_id).first()
        await NotificationService.notify_user(
            db = db,
            user_id = invite.business.owner_id,
            title = "New Team Member",
            content = f"{new_member.email} has joined your project {invite.business.name}",
            notify_type = "TEAM_JOIN",
            background_tasks = background_tasks
        )

        await TeamService.notify_team_sync(db, invite.business_id, background_tasks)
        
        return {
            "message": "Success! You are now part of the team",
            "business_id": invite.business_id,
            "status": "accepted",
            "accessible_ideas": [i.id for i in collaborator.accessible_ideas]
        }

    @staticmethod
    async def handle_join_request(
        db: Session, 
        request_id: uuid.UUID, 
        owner_id: uuid.UUID, 
        is_approved: bool,
        background_tasks: BackgroundTasks,
        role: CollaboratorRole = CollaboratorRole.VIEWER,
        idea_ids: Optional[List[uuid.UUID]] = None
    ) -> Dict[str, Any]:
        """
        Processes a join request by approving or rejecting it.
        Allows setting specific roles and idea access upon approval.
        """
        request = db.query(BusinessJoinRequest).filter(BusinessJoinRequest.id == request_id).first()
        
        if not request:
            raise HTTPException(status_code = 404, detail = "Join request not found")
        
        if request.business.owner_id != owner_id:
            raise HTTPException(status_code = 403, detail = "Only the project owner can approve requests")
        
        if is_approved:
            request.status = JoinRequestStatus.APPROVED
            
            final_role = role if role != CollaboratorRole.VIEWER or request.role == CollaboratorRole.VIEWER else request.role
            final_idea_ids = idea_ids if idea_ids is not None else [i.id for i in request.accessible_ideas]
            
            TeamService.add_collaborator(
                db, 
                request.business_id, 
                request.user_id, 
                final_role,
                final_idea_ids
            )
            
            message = f"Request approved. User is now a {final_role.value}."
        else:
            request.status = JoinRequestStatus.REJECTED
            message = "Request rejected."
        
        db.commit()

        status_text = "Access granted to" if is_approved else "Access denied to"
        
        await NotificationService.notify_user(
            db = db,
            user_id = request.user_id,
            title = "Join Request Status",
            content = f"{status_text} your request to join {request.business.name}",
            notify_type = "TEAM_RESPONSE",
            background_tasks = background_tasks
        )

        if is_approved:
            await NotificationService.notify_user(
                db = db,
                user_id = owner_id,
                title = "New Team Member",
                content = f"You approved {request.user.email} to join {request.business.name}",
                notify_type = "TEAM_JOIN",
                background_tasks = background_tasks
            )

        send_join_request_status_email(request.user.email, request.business.name, request.status.value)

        # Trigger real-time sync
        await TeamService.notify_team_sync(db, request.business_id, background_tasks)

        return {"message": message, "status": request.status}

    @staticmethod
    def add_collaborator(
        db: Session,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        role: CollaboratorRole = CollaboratorRole.VIEWER,
        idea_ids: Optional[List[uuid.UUID]] = None
    ) -> BusinessCollaborator:
        """
        Internal utility to add or update a collaborator in a business.
        """
        existing = db.query(BusinessCollaborator).filter(
            BusinessCollaborator.business_id == business_id,
            BusinessCollaborator.user_id == user_id
        ).first()
        
        if existing:
            existing.role = role
            
            if idea_ids is not None:
                existing.accessible_ideas = []
                
                if idea_ids:
                    ideas = db.query(Idea).filter(Idea.id.in_(idea_ids)).all()
                    existing.accessible_ideas = ideas
                    
            return existing

        collaborator = BusinessCollaborator(
            business_id = business_id,
            user_id = user_id,
            role = role
        )
        
        if idea_ids:
            ideas = db.query(Idea).filter(Idea.id.in_(idea_ids)).all()
            collaborator.accessible_ideas = ideas
            
        db.add(collaborator)
        
        return collaborator

    @staticmethod
    async def remove_collaborator(
        db: Session, 
        business_id: uuid.UUID, 
        user_id: uuid.UUID, 
        owner_id: uuid.UUID,
        background_tasks: BackgroundTasks,
        new_owner_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Removes a collaborator from the team. 
        If they own resources, transfers them to new_owner_id or project owner.
        Uses background tasks for large resource transfers (AF_A4).
        """
        collaborator = db.query(BusinessCollaborator).filter(
            BusinessCollaborator.business_id == business_id,
            BusinessCollaborator.user_id == user_id
        ).first()
        
        if not collaborator:
            raise HTTPException(status_code = 404, detail = "Collaborator not found")
            
        business = collaborator.business
        if business.owner_id != owner_id:
            raise HTTPException(status_code = 403, detail = "Only the project owner can remove members")

        if user_id == business.owner_id:
            raise HTTPException(status_code = 400, detail = "Cannot remove the project owner from the team")

        has_ideas = db.query(Idea).filter(Idea.owner_id == user_id, Idea.business_id == business_id).first()
        has_comparisons = db.query(IdeaComparison).filter(IdeaComparison.user_id == user_id).first() # Simplified check

        if (has_ideas or has_comparisons) and not new_owner_id:
            raise HTTPException(
                status_code = 400, 
                detail = "User owns active resources. Please provide a new_owner_id to reassign them."
            )

        if new_owner_id:
            is_valid_owner = db.query(BusinessCollaborator).filter(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.user_id == new_owner_id,
                BusinessCollaborator.status == CollaboratorStatus.ACTIVE
            ).first()

            if not is_valid_owner and new_owner_id != business.owner_id:
                raise HTTPException(status_code = 400, detail = "New owner must be a valid member of this team")

        collaborator.status = CollaboratorStatus.REMOVAL_PENDING
        db.commit()

        background_tasks.add_task(
            TeamService.finalize_collaborator_removal,
            str(business_id),
            str(user_id),
            str(owner_id),
            str(new_owner_id) if new_owner_id else None
        )

        return {
            "message": "Removal process initiated. Ownership transfer and session revocation are being processed in the background.",
            "status": "pending_removal"
        }

    @staticmethod
    async def finalize_collaborator_removal(
        business_id_str: str,
        user_id_str: str,
        owner_id_str: str,
        new_owner_id_str: Optional[str] = None
    ) -> None:
        """
        Background task to transfer ownership, delete collaborator, log audit, and revoke session (AF_A4, AF_A5, AF_F2).
        """
        db = SessionLocal()
        try:
            business_id = uuid.UUID(business_id_str)
            user_id = uuid.UUID(user_id_str)
            owner_id = uuid.UUID(owner_id_str)
            new_owner_id = uuid.UUID(new_owner_id_str) if new_owner_id_str else owner_id

            db.query(Idea).filter(
                Idea.owner_id == user_id, 
                Idea.business_id == business_id
            ).update({"owner_id": new_owner_id}, synchronize_session = False)

            db.query(IdeaComparison).filter(
                IdeaComparison.user_id == user_id
            ).update({"user_id": new_owner_id}, synchronize_session = False)

            db.query(BusinessCollaborator).filter(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.user_id == user_id
            ).delete()

            user = db.query(User).filter(User.id == user_id).first()
            
            if user:
                user.revoked_at = datetime.now(timezone.utc)

            audit_log = AdminActionLog(
                admin_id = owner_id,
                action_type = "TEAM_MEMBER_REMOVAL",
                target_entity = "User",
                target_id = user_id
            )
            db.add(audit_log)

            sec_log = SecurityLog(
                user_id = user_id,
                event_type = "SESSION_REVOKED_BY_ADMIN",
                details = {"reason": "Removed from team", "admin_id": owner_id_str}
            )
            db.add(sec_log)

            # Invalidate cache after removal
            TeamService.invalidate_team_cache(business_id)

            db.commit()

            bg_tasks = BackgroundTasks()

            biz = db.query(Business).filter(Business.id == business_id).first()
            
            await NotificationService.notify_user(
                db = db,
                user_id = user_id,
                title = "Removal from Project",
                content = f"You have been removed from the project '{biz.name}' by the owner. Your access has been revoked.",
                notify_type = "TEAM_REMOVAL",
                background_tasks = bg_tasks,
                should_force_email = True
            )

            # Trigger real-time sync
            await TeamService.notify_team_sync(db, business_id, bg_tasks)
            

        except Exception as e:
            db.rollback()
            logger.error(f"FAILED finalize_collaborator_removal: {str(e)}")
            error_log = SecurityLog(
                user_id = uuid.UUID(owner_id_str),
                event_type = "MEMBER_REMOVAL_FAILURE",
                details = {"target_user": user_id_str, "error": str(e)}
            )
            db.add(error_log)
            db.commit()
        finally:
            db.close()

    @staticmethod
    def create_share_link(
        db: Session,
        business_id: uuid.UUID,
        invited_by: uuid.UUID,
        email: Optional[str] = None,
        is_approval_required: bool = True,
        role: CollaboratorRole = CollaboratorRole.VIEWER,
        idea_ids: Optional[List[uuid.UUID]] = None
    ) -> Dict[str, Any]:
        """
        Generates a secure, shareable invitation link.
        Handles direct email invitations and multi-idea permission scoping.
        """
        business = db.query(Business).filter(Business.id == business_id).first()
        
        if not business or business.owner_id != invited_by:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN, 
                detail = "Only the project owner can create share links"
            )

        if email:
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                is_member = db.query(BusinessCollaborator).filter(
                    BusinessCollaborator.business_id == business_id,
                    BusinessCollaborator.user_id == user.id
                ).first()
                
                if is_member:
                    raise HTTPException(
                        status_code = 400, 
                        detail = f"User with email {email} is already a member of this team"
                    )

            is_duplicate_invite = db.query(BusinessInvite).filter(
                BusinessInvite.business_id == business_id,
                BusinessInvite.email == email,
                BusinessInvite.status == InviteStatus.PENDING,
                BusinessInvite.expires_at > datetime.now(timezone.utc)
            ).first()
            
            if is_duplicate_invite:
                raise HTTPException(
                    status_code = 400, 
                    detail = f"There is already a pending invitation for {email}"
                )

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days = 7)
        
        invite = BusinessInvite(
            business_id = business_id,
            token = token,
            invited_by = invited_by,
            role = role,
            expires_at = expires_at,
            email = email,
            requires_approval = is_approval_required
        )
        
        if idea_ids:
            ideas = db.query(Idea).filter(Idea.id.in_(idea_ids)).all()
            invite.accessible_ideas = ideas
        
        db.add(invite)
        db.commit()
        db.refresh(invite)
        
        if email:
            
            inviter = db.query(User).filter(User.id == invited_by).first()
            inviter_name = inviter.email if inviter else "Someone"
            
            invite_url = f"https://bizify.app/join-team?token={token}"
            business_name = business.converted_idea.title if business.converted_idea else "Your Business"
            send_team_invite_email(email, business_name, inviter_name, invite_url)

        return {
            "token": token,
            "invite_url": f"https://bizify.app/join-team?token={token}",
            "requires_approval": is_approval_required,
            "role": role.value,
            "email": email,
            "accessible_ideas": [i.id for i in invite.accessible_ideas]
        }

    @staticmethod
    async def update_collaborator(
        db: Session,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        owner_id: uuid.UUID,
        background_tasks: BackgroundTasks,
        role: Optional[CollaboratorRole] = None,
        idea_ids: Optional[List[uuid.UUID]] = None,
        reassign_to_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Updates an existing collaborator's permissions or role.
        Handles owner protection, resource reassignment, and session revocation.
        """
        collaborator = db.query(BusinessCollaborator).filter(
            BusinessCollaborator.business_id == business_id,
            BusinessCollaborator.user_id == user_id
        ).first()

        if not collaborator:
            raise HTTPException(
                status_code = 404,
                detail = "Collaborator not found"
            )

        business = collaborator.business
        
        if business.owner_id != owner_id:
            raise HTTPException(
                status_code = 403,
                detail = "Only the project owner can update member permissions"
            )

        if collaborator.role == CollaboratorRole.OWNER:
            raise HTTPException(
                status_code = 400,
                detail = "Cannot change the role of a project owner"
            )

        try:
            old_role = collaborator.role

            if role is not None:
                if old_role == CollaboratorRole.EDITOR and role == CollaboratorRole.VIEWER:
                    has_ideas = db.query(Idea).filter(
                        Idea.owner_id == user_id,
                        Idea.business_id == business_id
                    ).first()
                    
                    has_comparisons = db.query(IdeaComparison).filter(
                        IdeaComparison.user_id == user_id
                    ).first()

                    if has_ideas or has_comparisons:
                        target_owner_id = reassign_to_id or business.owner_id
                        
                        if reassign_to_id:
                            is_valid_target = db.query(BusinessCollaborator).filter(
                                BusinessCollaborator.business_id == business_id,
                                BusinessCollaborator.user_id == reassign_to_id,
                                BusinessCollaborator.status == CollaboratorStatus.ACTIVE
                            ).first()
                            
                            if not is_valid_target and reassign_to_id != business.owner_id:
                                raise HTTPException(
                                    status_code = 400,
                                    detail = "Reassignment target must be a valid member of this team"
                                )

                        db.query(Idea).filter(
                            Idea.owner_id == user_id,
                            Idea.business_id == business_id
                        ).update({"owner_id": target_owner_id}, synchronize_session = False)

                        db.query(IdeaComparison).filter(
                            IdeaComparison.user_id == user_id
                        ).update({"user_id": target_owner_id}, synchronize_session = False)

                collaborator.role = role

            if idea_ids is not None:
                collaborator.accessible_ideas = []
                
                if idea_ids:
                    ideas = db.query(Idea).filter(Idea.id.in_(idea_ids)).all()
                    collaborator.accessible_ideas = ideas

            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.revoked_at = datetime.now(timezone.utc)

            audit_log = AdminActionLog(
                admin_id = owner_id,
                action_type = f"ROLE_CHANGE: {old_role.value if old_role else 'None'} -> {role.value if role else 'None'}",
                target_entity = "User",
                target_id = user_id
            )
            db.add(audit_log)

            # Invalidate cache after role/permission change
            TeamService.invalidate_team_cache(business_id)

            db.commit()

            # Trigger real-time sync
            await TeamService.notify_team_sync(db, business_id, background_tasks)

            return {
                "message": "Collaborator updated successfully. Session revoked for security.",
                "role": collaborator.role.value,
                "accessible_ideas": [i.id for i in collaborator.accessible_ideas]
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"FAILED update_collaborator: {str(e)}")
            raise HTTPException(
                status_code = 500,
                detail = "An internal error occurred while updating the collaborator"
            )

    @staticmethod
    def get_collaborators(
        db: Session,
        business_id: uuid.UUID,
        requester_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a paginated list of team members for a business (UC_19).
        Implements dynamic masking for VIEWERS and sorts by role hierarchy.
        Uses Redis for high-performance retrieval.
        """
        # 1. Authorization: Must be a member (BF_02)
        requester = db.query(BusinessCollaborator).filter(
            BusinessCollaborator.business_id == business_id,
            BusinessCollaborator.user_id == requester_id,
            BusinessCollaborator.status == CollaboratorStatus.ACTIVE
        ).first()

        business = db.query(Business).filter(Business.id == business_id).first()
        is_owner = business and business.owner_id == requester_id

        if not requester and not is_owner:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "You are not a member of this team"
            )

        requester_role = CollaboratorRole.OWNER if is_owner else requester.role
        is_viewer = requester_role == CollaboratorRole.VIEWER

        # 2. Caching: Check Redis (Team members are read-heavy)
        cache_key = f"team_members:{business_id}:{is_viewer}:{skip}:{limit}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        try:
            # 3. Sorting logic: OWNER > EDITOR > VIEWER (BF_07)
            role_order = case(
                (BusinessCollaborator.role == CollaboratorRole.OWNER, 10),
                (BusinessCollaborator.role == CollaboratorRole.EDITOR, 5),
                (BusinessCollaborator.role == CollaboratorRole.VIEWER, 1),
                else_ = 0
            )

            # 4. Retrieval with sorting and pagination
            query = db.query(BusinessCollaborator).filter(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.status == CollaboratorStatus.ACTIVE,
                BusinessCollaborator.user_id != requester_id  # Exclude self based on AF_A4 logic (other members)
            ).order_by(role_order.desc(), BusinessCollaborator.added_at.asc())

            members = query.offset(skip).limit(limit).all()

            # 5. Dynamic Serialization & Masking (AF_A3)
            result = []
            for member in members:
                # Calculate dynamic permission flags for the requester (BF_07)
                can_remove = False
                can_change_role = False

                if requester_role == CollaboratorRole.OWNER:
                    can_remove = True
                    can_change_role = True
                elif requester_role == CollaboratorRole.EDITOR:
                    # Editors might have limited manager roles in future, for now only owner
                    pass

                member_data = {
                    "id": str(member.id),
                    "user_id": str(member.user_id),
                    "email": member.user.email if not is_viewer else "********",  # Masking (AF_A3)
                    "role": member.role.value,
                    "status": member.status.value,
                    "added_at": member.added_at.isoformat(),
                    "can_remove": can_remove,
                    "can_change_role": can_change_role
                }
                result.append(member_data)

            # 6. Cache the result for 10 minutes
            cache.set(cache_key, result, expire_seconds = 600)
            
            return result

        except Exception as e:
            logger.error(f"Failed to retrieve team members for {business_id}: {str(e)}")
            raise HTTPException(
                status_code = 500,
                detail = "Database retrieval failure. Please try again."
            )

    @staticmethod
    def invalidate_team_cache(business_id: uuid.UUID) -> None:
        """
        Invalidates all cached member lists for a business.
        Called after UC_16/UC_17 operations.
        """
        cache.delete_pattern(f"team_members:{business_id}:*")

    @staticmethod
    async def notify_team_sync(db: Session, business_id: uuid.UUID, background_tasks: BackgroundTasks) -> None:
        """
        Triggers a TEAM_SYNC notification for all active members (AF_A5).
        """
        try:
            members = db.query(BusinessCollaborator).filter(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.status == CollaboratorStatus.ACTIVE
            ).all()
            
            business = db.query(Business).filter(Business.id == business_id).first()
            
            user_ids = {m.user_id for m in members}
            if business:
                user_ids.add(business.owner_id)
                
            for user_id in user_ids:
                await NotificationService.notify_user(
                    db = db,
                    user_id = user_id,
                    title = "Team Updated",
                    content = "The team member list has changed.",
                    notify_type = "TEAM_SYNC",
                    background_tasks = background_tasks
                )
        except Exception as e:
            logger.error(f"Failed to notify team sync for {business_id}: {str(e)}")
