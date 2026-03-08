# Register all models here so that Alembic and SQLAlchemy can discover them
from app.db.database import Base

# Enums (Optional to import here, but good for completeness)
from .enums import *  # noqa: F403

# Users
from .users.user import User, UserProfile, AdminActionLog, RefreshToken, PasswordResetToken, EmailVerificationToken

# Partners
from .partners.partner import PartnerProfile, PartnerRequest

# Ideation
from .ideation.idea import Idea, IdeaVersion, IdeaMetric, Experiment, IdeaAccess
from .ideation.comparison import IdeaComparison, ComparisonItem, ComparisonMetric

# Business
from .business.business import (
    Business, BusinessCollaborator, BusinessInvite, BusinessInviteIdea,
    BusinessRoadmap, RoadmapStage
)

# AI & Agents
from .ai.agent import Agent, AgentRun, ValidationLog, Embedding

# Chat
from .chat.chat import ChatSession, ChatMessage

# Billing
from .billing.billing import Plan, Subscription, PaymentMethod, Payment, Usage
from .billing.processed_event import ProcessedEvent

# Core / Shared
from .core.core import File, Notification, ShareLink

# This ensures Base.metadata.create_all(bind=engine) will create all tables
__all__ = [
    "Base", "User", "UserProfile", "AdminActionLog", "RefreshToken",
    "PasswordResetToken", "EmailVerificationToken",
    "PartnerProfile", "PartnerRequest",
    "Idea", "IdeaVersion", "IdeaMetric", "Experiment", "IdeaAccess",
    "IdeaComparison", "ComparisonItem", "ComparisonMetric",
    "Business", "BusinessCollaborator", "BusinessInvite", "BusinessInviteIdea",
    "BusinessRoadmap", "RoadmapStage",
    "Agent", "AgentRun", "ValidationLog", "Embedding",
    "ChatSession", "ChatMessage",
    "Plan", "Subscription", "PaymentMethod", "Payment", "Usage", "ProcessedEvent",
    "File", "Notification", "ShareLink"
]
