from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.billing_repo import subscription_repo
from app.repositories.usage_repo import usage_repo, CHAT_DAILY_LIMIT

router = APIRouter()


@router.get("", summary="Get AI usage and credit balance for the current user", tags=["Usage"])
def get_my_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Returns the authenticated user's credit balance, plan info, and chat limits.

    Response fields:
      credits_used      : credits spent this billing period
      credits_limit     : total credit allowance for this period
      credits_remaining : credits left
      period_start      : ISO date when the current billing period started
      plan_name         : "Free" | "Pro" | "Premium" | "Pay-Per-Feature"
      plan_type         : "free" | "pro" | "premium" | "payg"
      is_ppf            : true when on Pay-As-You-Go
      ppf_purchased     : total PAYG feature runs ever bought
      ppf_used          : PAYG runs consumed
      ppf_remaining     : PAYG runs available
      chat_turns_today  : general-chat turns used today (Free/PAYG only)
      chat_daily_limit  : daily turn cap (20 for Free/PAYG; -1 = unlimited for subscribers)
    """
    sub = subscription_repo.get_active_by_user(db, current_user.id)
    features: dict = {}
    plan_name = "Free"
    if sub and sub.plan:
        plan_name = sub.plan.name
        if sub.plan.features_json:
            features = sub.plan.features_json

    is_ppf = bool(features.get("is_ppf"))
    plan_type_raw = plan_name.lower()
    if is_ppf:
        plan_type = "payg"
    elif plan_type_raw in ("pro", "premium"):
        plan_type = plan_type_raw
    else:
        plan_type = "free"

    # Grant monthly renewal before returning balance (so the UI shows the refreshed amount)
    if plan_type == "free":
        usage_repo.maybe_grant_free_monthly_credits(db, current_user.id)

    credit_info = usage_repo.get_credit_info(db, current_user.id)

    record = usage_repo.get_or_create(db, current_user.id)
    ppf_purchased = record.ppf_purchased or 0
    ppf_used      = record.ppf_used or 0

    # Chat turn info
    is_subscriber = plan_type in ("pro", "premium")
    chat_turns_remaining = -1 if is_subscriber else usage_repo.get_chat_turns_remaining(db, current_user.id)
    chat_daily_limit = -1 if is_subscriber else CHAT_DAILY_LIMIT

    return {
        **credit_info,
        "plan_name":            plan_name,
        "plan_type":            plan_type,
        "is_ppf":               is_ppf,
        "ppf_purchased":        ppf_purchased,
        "ppf_used":             ppf_used,
        "ppf_remaining":        max(ppf_purchased - ppf_used, 0),
        "chat_turns_today":     -1 if is_subscriber else (record.chat_turns_today or 0),
        "chat_turns_remaining": chat_turns_remaining,
        "chat_daily_limit":     chat_daily_limit,
        # Legacy fields kept so existing frontend components don't break
        "used":       record.used or 0,
        "limit":      record.limit_value or 0,
        "remaining":  max((record.limit_value or 0) - (record.used or 0), 0),
        "percentage": 0.0,
        "unlimited":  False,
    }
