import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.ai.idea import Idea
from app.models.share_link import ShareLink
from app.models.user import User
from app.schemas.share_link import ShareItem, ShareRequest, ShareResponse, SharedIdeaRead

router = APIRouter()
public_router = APIRouter()

FRONTEND_BASE = "https://bizify-v2.vercel.app"


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


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
        )
        db.add(link)
        items.append(
            ShareItem(
                idea_id=idea_id,
                idea_title=idea.title or "Untitled idea",
                token=token,
                share_url=f"{FRONTEND_BASE}/share/{token}",
            )
        )

    db.commit()
    return ShareResponse(items=items)


@public_router.get("/share/{token}", response_model=SharedIdeaRead)
def get_shared_idea(token: str, db: Session = Depends(get_db)) -> SharedIdeaRead:
    """Public endpoint — no auth required. Returns the idea linked to a share token."""
    link: ShareLink | None = (
        db.query(ShareLink).filter(ShareLink.token == token, ShareLink.is_public == True).first()
    )
    if not link or not link.idea_id:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    idea: Idea | None = db.query(Idea).filter(Idea.id == link.idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea no longer exists")

    return SharedIdeaRead(
        id=idea.id,
        title=idea.title or "Untitled idea",
        description=idea.description,
        status=str(idea.status.value) if hasattr(idea.status, "value") else str(idea.status),
        budget=idea.budget,
        skills=idea.skills,
        feasibility=idea.feasibility,
        created_at=idea.created_at,
    )
