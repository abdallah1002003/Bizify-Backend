# ruff: noqa: E402
from __future__ import annotations
from typing import Any, List, Optional, Protocol, runtime_checkable, Dict
from uuid import UUID
from sqlalchemy.orm import Session
import app.models as models

@runtime_checkable
class IUserService(Protocol):
    db: Session
    def get_user(self, id: UUID) -> Optional[models.User]: ...
    def get_user_by_email(self, email: str) -> Optional[models.User]: ...
    def create_user(self, obj_in: Any) -> models.User: ...
    def update_user(self, db_obj: models.User, obj_in: Any) -> models.User: ...
    def delete_user(self, id: UUID) -> Optional[models.User]: ...

@runtime_checkable
class IIdeaAccessService(Protocol):
    db: Session
    def check_idea_access(self, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool: ...
    def grant_access(self, idea_id: UUID, user_id: UUID, permission: str = "view") -> models.IdeaAccess: ...

@runtime_checkable
class IIdeaVersionService(Protocol):
    db: Session
    def create_idea_snapshot(self, idea: Any, created_by: Optional[UUID] = None) -> models.IdeaVersion: ...
    def get_idea_versions(self, idea_id: UUID) -> List[models.IdeaVersion]: ...

@runtime_checkable
class IIdeaService(Protocol):
    db: Session
    access: IIdeaAccessService
    version: IIdeaVersionService
    def get_idea(self, id: UUID, user_id: Optional[UUID] = None) -> Optional[models.Idea]: ...
    def create_idea(self, obj_in: Any) -> models.Idea: ...
    def update_idea(self, db_obj: models.Idea, obj_in: Any, performer_id: Optional[UUID] = None) -> models.Idea: ...

@runtime_checkable
class IBusinessRoadmapService(Protocol):
    db: Session
    def get_roadmap(self, roadmap_id: Optional[UUID] = None, business_id: Optional[UUID] = None) -> Optional[models.BusinessRoadmap]: ...
    def init_default_roadmap(self, business_id: UUID) -> models.BusinessRoadmap: ...

@runtime_checkable
class IBusinessCollaboratorService(Protocol):
    db: Session
    def add_collaborator(self, business_id: UUID, user_id: UUID, role: Any) -> models.BusinessCollaborator: ...

@runtime_checkable
class IBusinessService(Protocol):
    db: Session
    roadmap: IBusinessRoadmapService
    collaborator: IBusinessCollaboratorService
    def get_business(self, id: UUID) -> Optional[models.Business]: ...
    def create_business(self, obj_in: Any) -> models.Business: ...

@runtime_checkable
class IBillingService(Protocol):
    db: Session
    def check_usage_limit(self, user_id: UUID, resource_type: str) -> bool: ...
    def record_usage(self, user_id: UUID, resource_type: str, quantity: int = 1) -> models.Usage: ...

@runtime_checkable
class ISubscriptionService(Protocol):
    db: Session
    def get_subscription(self, id: UUID) -> Optional[models.Subscription]: ...

@runtime_checkable
class IAgentService(Protocol):
    db: Session
    def get_agent(self, id: UUID) -> Optional[models.Agent]: ...

@runtime_checkable
class IAgentRunService(Protocol):
    db: Session
    billing: IBillingService
    def get_agent_run(self, id: UUID) -> Optional[models.AgentRun]: ...
    def initiate_agent_run(self, agent_id: UUID, user_id: Optional[UUID], stage_id: UUID, input_data: Optional[Dict[str, Any]] = None) -> models.AgentRun: ...

@runtime_checkable
class IEmbeddingService(Protocol):
    db: Session
    def create_embedding(self, obj_in: Any) -> models.Embedding: ...

@runtime_checkable
class IEmailService(Protocol):
    async def send_verification_email(self, email: str, token: str) -> None: ...
    async def send_password_reset_email(self, email: str, token: str) -> None: ...
