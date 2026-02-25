from fastapi import APIRouter, Depends

from app.api.v1.users import user
from app.api.v1.users import user_profile
from app.api.v1.users import admin_action_log
from app.api.v1.partners import partner_profile
from app.api.v1.partners import partner_request
from app.api.v1.ideation import idea
from app.api.v1.ideation import idea_version
from app.api.v1.ideation import idea_metric
from app.api.v1.ideation import experiment
from app.api.v1.business import business
from app.api.v1.business import business_collaborator
from app.api.v1.business import business_invite
from app.api.v1.business import business_invite_idea
from app.api.v1.ideation import idea_access
from app.api.v1.business import business_roadmap
from app.api.v1.business import roadmap_stage
from app.api.v1.ai import agent
from app.api.v1.ai import agent_run
from app.api.v1.ai import validation_log
from app.api.v1.ai import embedding
from app.api.v1.chat import chat_session
from app.api.v1.chat import chat_message
from app.api.v1.chat import chat_ws
from app.api.v1.billing import plan
from app.api.v1.billing import subscription
from app.api.v1.billing import payment_method
from app.api.v1.billing import payment
from app.api.v1.billing import usage
from app.api.v1.billing import stripe_webhook
from app.api.v1.billing import checkout
from app.api.v1.core import file
from app.api.v1.core import notification
from app.api.v1.core import share_link
from app.api.v1.ideation import idea_comparison
from app.api.v1.ideation import comparison_item
from app.api.v1.ideation import comparison_metric
from app.api.v1 import auth
from app.core.dependencies import get_current_active_user

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])


api_router.include_router(user.router, prefix="/users", tags=["User"])
api_router.include_router(
    user_profile.router,
    prefix="/user_profiles",
    tags=["UserProfile"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    admin_action_log.router,
    prefix="/admin_action_logs",
    tags=["AdminActionLog"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    partner_profile.router,
    prefix="/partner_profiles",
    tags=["PartnerProfile"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    partner_request.router,
    prefix="/partner_requests",
    tags=["PartnerRequest"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(idea.router, prefix="/ideas", tags=["Idea"])
api_router.include_router(
    idea_version.router,
    prefix="/idea_versions",
    tags=["IdeaVersion"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    idea_metric.router,
    prefix="/idea_metrics",
    tags=["IdeaMetric"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    experiment.router,
    prefix="/experiments",
    tags=["Experiment"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(business.router, prefix="/businesses", tags=["Business"])
api_router.include_router(
    business_collaborator.router,
    prefix="/business_collaborators",
    tags=["BusinessCollaborator"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    business_invite.router,
    prefix="/business_invites",
    tags=["BusinessInvite"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    business_invite_idea.router,
    prefix="/business_invite_ideas",
    tags=["BusinessInviteIdea"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    idea_access.router,
    prefix="/idea_access",
    tags=["IdeaAccess"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    business_roadmap.router,
    prefix="/business_roadmaps",
    tags=["BusinessRoadmap"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    roadmap_stage.router,
    prefix="/roadmap_stages",
    tags=["RoadmapStage"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    agent.router,
    prefix="/agents",
    tags=["Agent"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    agent_run.router,
    prefix="/agent_runs",
    tags=["AgentRun"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    validation_log.router,
    prefix="/validation_logs",
    tags=["ValidationLog"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    embedding.router,
    prefix="/embeddings",
    tags=["Embedding"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    chat_session.router,
    prefix="/chat_sessions",
    tags=["ChatSession"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    chat_message.router,
    prefix="/chat_messages",
    tags=["ChatMessage"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    chat_ws.router,
    prefix="/chat",
    tags=["Chat Real-Time"],
)
api_router.include_router(
    plan.router,
    prefix="/plans",
    tags=["Plan"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    subscription.router,
    prefix="/subscriptions",
    tags=["Subscription"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    payment_method.router,
    prefix="/payment_methods",
    tags=["PaymentMethod"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    payment.router,
    prefix="/payments",
    tags=["Payment"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    usage.router,
    prefix="/usages",
    tags=["Usage"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    file.router,
    prefix="/files",
    tags=["File"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    notification.router,
    prefix="/notifications",
    tags=["Notification"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    share_link.router,
    prefix="/share_links",
    tags=["ShareLink"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    idea_comparison.router,
    prefix="/idea_comparisons",
    tags=["IdeaComparison"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    comparison_item.router,
    prefix="/comparison_items",
    tags=["ComparisonItem"],
    dependencies=[Depends(get_current_active_user)],
)
api_router.include_router(
    comparison_metric.router,
    prefix="/comparison_metrics",
    tags=["ComparisonMetric"],
    dependencies=[Depends(get_current_active_user)],
)


api_router.include_router(
    stripe_webhook.router,
    prefix="/billing/webhooks",
    tags=["Stripe Webhooks"],
)

# Stripe Checkout - requires auth
api_router.include_router(
    checkout.router,
    prefix="/billing",
    tags=["Stripe Checkout"],
    dependencies=[Depends(get_current_active_user)],
)
