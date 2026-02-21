import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENTREPRENEUR = "entrepreneur"
    MENTOR = "mentor"
    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"

class PartnerType(str, enum.Enum):
    MENTOR = "mentor"
    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class IdeaStatus(str, enum.Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    CONVERTED = "converted"

class BusinessStage(str, enum.Enum):
    EARLY = "early"
    BUILDING = "building"
    SCALING = "scaling"

class CollaboratorRole(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class StageType(str, enum.Enum):
    READINESS = "readiness"
    RESEARCH = "research"
    STRATEGY = "strategy"
    MARKET = "market"
    FUNCTIONS = "functions"
    ECONOMICS = "economics"
    LEGAL = "legal"
    MVP = "mvp"
    BRANDING = "branding"
    GTM = "gtm"
    OPERATIONS = "operations"

class RoadmapStageStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"

class PartnerRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class AgentRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"

class ChatSessionType(str, enum.Enum):
    IDEA_CHAT = "idea_chat"
    BUSINESS_CHAT = "business_chat"
    STAGE_CHAT = "stage_chat"
    GENERAL = "general"

class ChatRole(str, enum.Enum):
    USER = "user"
    AI = "ai"

class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
