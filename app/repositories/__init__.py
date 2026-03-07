<<<<<<< HEAD
"""Repository package — provides reusable CRUD infrastructure.

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# Import the required repository class in each service to delegate DB access.
"""

from app.repositories.base_repository import GenericRepository
from app.repositories.user_repository import UserRepository
from app.repositories.auth_repository import (
    RefreshTokenRepository,
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
)
from app.repositories.business_repository import (
    BusinessRepository,
    BusinessCollaboratorRepository,
    BusinessInviteRepository,
    BusinessInviteIdeaRepository,
    BusinessRoadmapRepository,
    RoadmapStageRepository,
)
from app.repositories.idea_repository import (
    IdeaRepository,
    IdeaVersionRepository,
    IdeaMetricRepository,
    ExperimentRepository,
    IdeaAccessRepository,
    IdeaComparisonRepository,
    ComparisonItemRepository,
    ComparisonMetricRepository,
)
from app.repositories.billing_repository import (
    PlanRepository,
    SubscriptionRepository,
    PaymentMethodRepository,
    PaymentRepository,
    UsageRepository,
)
from app.repositories.partner_repository import (
    PartnerProfileRepository,
    PartnerRequestRepository,
)
from app.repositories.core_repository import (
    FileRepository,
    NotificationRepository,
    ShareLinkRepository,
)
from app.repositories.chat_repository import (
    ChatSessionRepository,
    ChatMessageRepository,
)

__all__ = [
    "GenericRepository",
    "UserRepository",
    # Auth
    "RefreshTokenRepository",
    "EmailVerificationTokenRepository",
    "PasswordResetTokenRepository",
    # Business
    "BusinessRepository",
    "BusinessCollaboratorRepository",
    "BusinessInviteRepository",
    "BusinessInviteIdeaRepository",
    "BusinessRoadmapRepository",
    "RoadmapStageRepository",
    # Ideation
    "IdeaRepository",
    "IdeaVersionRepository",
    "IdeaMetricRepository",
    "ExperimentRepository",
    "IdeaAccessRepository",
    "IdeaComparisonRepository",
    "ComparisonItemRepository",
    "ComparisonMetricRepository",
    # Billing
    "PlanRepository",
    "SubscriptionRepository",
    "PaymentMethodRepository",
    "PaymentRepository",
    "UsageRepository",
    # Partners
    "PartnerProfileRepository",
    "PartnerRequestRepository",
    # Core
    "FileRepository",
    "NotificationRepository",
    "ShareLinkRepository",
    # Chat
    "ChatSessionRepository",
    "ChatMessageRepository",
]
=======
"""Repository package — provides reusable CRUD infrastructure."""

from app.repositories.base_repository import GenericRepository

__all__ = ["GenericRepository"]
>>>>>>> origin/main
