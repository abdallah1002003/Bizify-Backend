"""API-layer dependency providers for service classes.

Keeps FastAPI-specific wiring outside the service layer.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db

from app.services.ai.ai_service import AIService
from app.services.auth.auth_service import AuthService, get_auth_service as _build_auth_service
from app.services.billing.payment_method import PaymentMethodService
from app.services.billing.payment_service import PaymentService
from app.services.billing.plan_service import PlanService, get_plan_service as _build_plan_service
from app.services.billing.stripe_webhook_service import StripeWebhookService
from app.services.billing.subscription_service import SubscriptionService
from app.services.billing.usage_service import UsageService
from app.services.business.business_collaborator import (
    BusinessCollaboratorService,
    get_business_collaborator_service as _build_business_collaborator_service,
)
from app.services.business.business_invite import BusinessInviteService
from app.services.business.business_roadmap import (
    BusinessRoadmapService,
    get_business_roadmap_service as _build_business_roadmap_service,
)
from app.services.business.business_service import (
    BusinessService,
    get_business_service as _build_business_service,
)
from app.services.chat.chat_service import ChatService
from app.services.core.file_service import FileService
from app.services.core.notification_service import NotificationService
from app.services.core.share_link_service import ShareLinkService
from app.services.ideation.idea_access import (
    IdeaAccessService,
    get_idea_access_service as _build_idea_access_service,
)
from app.services.ideation.idea_comparison import (
    IdeaComparisonService,
    get_idea_comparison_service as _build_idea_comparison_service,
)
from app.services.ideation.idea_comparison_item import (
    ComparisonItemService,
    get_comparison_item_service as _build_comparison_item_service,
)
from app.services.ideation.idea_comparison_metric import (
    ComparisonMetricService,
    get_comparison_metric_service as _build_comparison_metric_service,
)
from app.services.ideation.idea_experiment import (
    IdeaExperimentService,
    get_idea_experiment_service as _build_idea_experiment_service,
)
from app.services.ideation.idea_metric import (
    IdeaMetricService,
    get_idea_metric_service as _build_idea_metric_service,
)
from app.services.ideation.idea_service import IdeaService, get_idea_service as _build_idea_service
from app.services.ideation.idea_version import (
    IdeaVersionService,
    get_idea_version_service as _build_idea_version_service,
)
from app.services.partners.partner_profile import PartnerProfileService
from app.services.partners.partner_request import PartnerRequestService
from app.services.users.user_service import UserService, get_user_service as _build_user_service


async def get_user_service(db: AsyncSession = Depends(get_async_db)) -> UserService:
    return await _build_user_service(db)


async def get_auth_service(
    db: AsyncSession = Depends(get_async_db),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return await _build_auth_service(db, user_service=user_service)


async def get_ai_service(db: AsyncSession = Depends(get_async_db)) -> AIService:
    return AIService(db)


async def get_plan_service(db: AsyncSession = Depends(get_async_db)) -> PlanService:
    return await _build_plan_service(db)


async def get_payment_service(db: AsyncSession = Depends(get_async_db)) -> PaymentService:
    return PaymentService(db)


async def get_payment_method_service(db: AsyncSession = Depends(get_async_db)) -> PaymentMethodService:
    return PaymentMethodService(db)


async def get_subscription_service(db: AsyncSession = Depends(get_async_db)) -> SubscriptionService:
    return SubscriptionService(db)


async def get_usage_service(db: AsyncSession = Depends(get_async_db)) -> UsageService:
    return UsageService(db)


async def get_stripe_webhook_service(db: AsyncSession = Depends(get_async_db)) -> StripeWebhookService:
    return StripeWebhookService(db)


async def get_business_collaborator_service(
    db: AsyncSession = Depends(get_async_db),
) -> BusinessCollaboratorService:
    return await _build_business_collaborator_service(db)


async def get_business_roadmap_service(
    db: AsyncSession = Depends(get_async_db),
) -> BusinessRoadmapService:
    return await _build_business_roadmap_service(db)


async def get_business_service(
    db: AsyncSession = Depends(get_async_db),
    roadmap: BusinessRoadmapService = Depends(get_business_roadmap_service),
    collaborator: BusinessCollaboratorService = Depends(get_business_collaborator_service),
) -> BusinessService:
    return await _build_business_service(db, roadmap=roadmap, collaborator=collaborator)


async def get_business_invite_service(
    db: AsyncSession = Depends(get_async_db),
) -> BusinessInviteService:
    return BusinessInviteService(db)


async def get_idea_access_service(db: AsyncSession = Depends(get_async_db)) -> IdeaAccessService:
    return await _build_idea_access_service(db)


async def get_idea_version_service(db: AsyncSession = Depends(get_async_db)) -> IdeaVersionService:
    return await _build_idea_version_service(db)


async def get_idea_service(
    db: AsyncSession = Depends(get_async_db),
    access: IdeaAccessService = Depends(get_idea_access_service),
    version: IdeaVersionService = Depends(get_idea_version_service),
) -> IdeaService:
    return await _build_idea_service(db, access=access, version=version)


async def get_idea_comparison_service(db: AsyncSession = Depends(get_async_db)) -> IdeaComparisonService:
    return await _build_idea_comparison_service(db)


async def get_comparison_item_service(db: AsyncSession = Depends(get_async_db)) -> ComparisonItemService:
    return await _build_comparison_item_service(db)


async def get_comparison_metric_service(
    db: AsyncSession = Depends(get_async_db),
) -> ComparisonMetricService:
    return await _build_comparison_metric_service(db)


async def get_idea_experiment_service(db: AsyncSession = Depends(get_async_db)) -> IdeaExperimentService:
    return await _build_idea_experiment_service(db)


async def get_idea_metric_service(db: AsyncSession = Depends(get_async_db)) -> IdeaMetricService:
    return await _build_idea_metric_service(db)


async def get_chat_service(db: AsyncSession = Depends(get_async_db)) -> ChatService:
    return ChatService(db)


async def get_file_service(db: AsyncSession = Depends(get_async_db)) -> FileService:
    return FileService(db)


async def get_notification_service(db: AsyncSession = Depends(get_async_db)) -> NotificationService:
    return NotificationService(db)


async def get_share_link_service(db: AsyncSession = Depends(get_async_db)) -> ShareLinkService:
    return ShareLinkService(db)


async def get_partner_profile_service(db: AsyncSession = Depends(get_async_db)) -> PartnerProfileService:
    return PartnerProfileService(db)


async def get_partner_request_service(db: AsyncSession = Depends(get_async_db)) -> PartnerRequestService:
    return PartnerRequestService(db)
