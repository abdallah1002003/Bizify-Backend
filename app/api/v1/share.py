import asyncio
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.ai.idea import Idea
from app.models.share_link import ShareLink
from app.models.user import User
from app.schemas.share_link import ShareItem, ShareRequest, ShareResponse, SharedIdeaRead

logger = logging.getLogger(__name__)

router = APIRouter()
public_router = APIRouter()

FRONTEND_BASE = "https://bizify-v2.vercel.app"

# (frontend field, AI pipeline path, response key returned by the pipeline)
_ANALYSIS_SECTIONS: list[tuple[str, str, str]] = [
    # Core
    ("problems",          "problems",          "problems"),
    ("customers",         "customers",         "customers"),
    ("competition",       "competition",       "competition"),
    ("market_potential",  "market-potential",  "market_potential"),
    ("idea_strategy",     "idea-strategy",     "idea_strategy"),
    ("business_model",    "business-model",    "business_model"),
    ("functions_list",    "functions-list",    "functions_list"),
    ("mvp_planning",      "mvp-planning",      "mvp_planning"),
    ("unit_economics",    "unit-economics",    "unit_economics"),
    ("go_to_market",      "go-to-market",      "go_to_market"),
    # Marketing
    ("customer_research", "customer-research", "customer_research"),
    ("copywriting",       "copywriting",       "copywriting"),
    ("pricing",           "marketing-pricing", "pricing"),
    ("launch_strategy",   "launch-strategy",   "launch_strategy"),
    ("ad_creative",       "ad-creative",       "ad_creative"),
    ("social_media",      "social-media",      "social_media"),
    ("marketing_ideas",   "marketing-ideas",   "marketing_ideas"),
]

_AI_REQUEST_TIMEOUT_SECONDS = 30

# Share links expire after this many days unless the caller asks for less/more.
DEFAULT_SHARE_TTL_DAYS = 90
MIN_SHARE_TTL_DAYS = 1
MAX_SHARE_TTL_DAYS = 365


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _resolve_expiry(expires_in_days: Optional[int]) -> datetime:
    """Clamp the requested TTL and return an absolute expiry timestamp."""
    ttl = expires_in_days if expires_in_days is not None else DEFAULT_SHARE_TTL_DAYS
    ttl = max(MIN_SHARE_TTL_DAYS, min(MAX_SHARE_TTL_DAYS, ttl))
    return datetime.utcnow() + timedelta(days=ttl)


async def _fetch_section(
    client: httpx.AsyncClient,
    path: str,
    user_id: str,
    idea_id: str,
    response_key: str,
) -> Optional[Any]:
    """Fetch one analysis section from the AI pipeline. Returns None on failure."""
    if not settings.AI_PIPELINE_API_KEY:
        return None
    url = f"{settings.AI_PIPELINE_BASE_URL}/pipeline/{path}/{user_id}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY}
    try:
        response = await client.get(url, headers=headers, params={"idea_id": idea_id})
        if response.status_code != 200:
            return None
        data = response.json()
        if not isinstance(data, dict):
            return None
        return data.get(response_key)
    except (httpx.RequestError, ValueError) as exc:
        logger.warning("Failed to fetch section %s: %s", path, exc)
        return None


@router.post("/ideas/share", response_model=ShareResponse)
def create_share_links(
    payload: ShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShareResponse:
    """Create public share links for a set of ideas owned by the current user."""
    if not payload.idea_ids:
        raise HTTPException(status_code=400, detail="At least one idea ID is required")

    items: list[ShareItem] = []
    expires_at = _resolve_expiry(payload.expires_in_days)

    for idea_id in payload.idea_ids:
        idea: Idea | None = db.query(Idea).filter(Idea.id == idea_id).first()
        if not idea:
            raise HTTPException(status_code=404, detail=f"Idea {idea_id} not found")
        if idea.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail=f"Not authorized to share idea {idea_id}",
            )

        token = _generate_token()
        link = ShareLink(
            id=uuid.uuid4(),
            idea_id=idea_id,
            created_by=current_user.id,
            token=token,
            is_public=True,
            expires_at=expires_at,
        )
        db.add(link)
        items.append(
            ShareItem(
                idea_id=idea_id,
                idea_title=idea.title or "Untitled idea",
                token=token,
                share_url=f"{FRONTEND_BASE}/share/{token}",
                expires_at=expires_at,
            )
        )

    db.commit()
    return ShareResponse(items=items)


@router.delete("/ideas/share/{token}", status_code=204)
def revoke_share_link(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Revoke a share link the current user owns (makes it immediately inaccessible)."""
    link: ShareLink | None = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    if link.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this link")

    link.is_public = False
    db.add(link)
    db.commit()


@public_router.get("/share/{token}", response_model=SharedIdeaRead)
async def get_shared_idea(token: str, db: Session = Depends(get_db)) -> SharedIdeaRead:
    """Public endpoint — no auth required. Returns the idea plus its full AI analysis."""
    link: ShareLink | None = (
        db.query(ShareLink)
        .filter(ShareLink.token == token, ShareLink.is_public == True)  # noqa: E712
        .first()
    )
    if not link or not link.idea_id:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    # Reject expired links (treated the same as not-found so no info leaks).
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    idea: Idea | None = db.query(Idea).filter(Idea.id == link.idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea no longer exists")

    # Fetch all analysis sections from the AI pipeline in parallel using the owner's id.
    sections: dict[str, Any] = {field: None for field, _, _ in _ANALYSIS_SECTIONS}
    if settings.AI_PIPELINE_API_KEY:
        async with httpx.AsyncClient(timeout=_AI_REQUEST_TIMEOUT_SECONDS) as client:
            results = await asyncio.gather(
                *(
                    _fetch_section(client, path, str(idea.owner_id), str(idea.id), key)
                    for _, path, key in _ANALYSIS_SECTIONS
                ),
                return_exceptions=True,
            )
        for (field, _, _), value in zip(_ANALYSIS_SECTIONS, results):
            sections[field] = value if not isinstance(value, Exception) else None

    return SharedIdeaRead(
        id=idea.id,
        title=idea.title or "Untitled idea",
        description=idea.description,
        status=str(idea.status.value) if hasattr(idea.status, "value") else str(idea.status),
        budget=idea.budget,
        skills=idea.skills,
        feasibility=idea.feasibility,
        created_at=idea.created_at,
        updated_at=idea.updated_at,
        domain=idea.domain,
        problem_evidence=idea.problem_evidence,
        core_insight=idea.core_insight,
        target_segment=idea.target_segment,
        founding_hypothesis=idea.founding_hypothesis,
        **sections,
    )
