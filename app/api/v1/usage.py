from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.billing_repo import subscription_repo
from app.repositories.usage_repo import usage_repo

router = APIRouter()


@router.get("", summary="Get AI token usage for the current user", tags=["Usage"])
def get_my_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Return the authenticated user's AI token usage:
    - used       : tokens consumed this billing cycle
    - limit      : total token budget (-1 = unlimited)
    - remaining  : tokens left (-1 = unlimited)
    - percentage : % consumed (0 if unlimited)
    - unlimited  : true for plans with no token cap
    - plan_name  : name of the active plan (or "Free" if none)
    """
    sub = subscription_repo.get_active_by_user(db, current_user.id)
    features: dict = {}
    plan_name = "Free"
    if sub and sub.plan and sub.plan.features_json:
        features = sub.plan.features_json
        plan_name = sub.plan.name

    plan_limit: Optional[int] = features.get("ai_tokens")

    info = usage_repo.get_usage_info(db, current_user.id, plan_limit)
    info["plan_name"] = plan_name
    info["is_ppf"] = bool(features.get("is_ppf"))

    # PPF credit balance
    record = usage_repo.get_or_create(db, current_user.id)
    ppf_purchased = record.ppf_purchased or 0
    ppf_used      = record.ppf_used or 0
    info["ppf_purchased"] = ppf_purchased
    info["ppf_used"]      = ppf_used
    info["ppf_remaining"] = max(ppf_purchased - ppf_used, 0)

    return info
