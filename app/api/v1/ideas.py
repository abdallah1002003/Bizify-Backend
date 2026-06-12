from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.ai.idea_translation import IdeaTranslation
from app.models.user import User
from app.schemas.idea import IdeaCreate, IdeaRead, IdeaUpdate, SharedIdeaItem
from app.services.idea_service import IdeaService

router = APIRouter()


@router.get("/", response_model=list[IdeaRead])
def get_ideas(
    min_budget: Optional[float] = Query(None, description="Minimum allowed budget"),
    max_budget: Optional[float] = Query(None, description="Maximum allowed budget"),
    skills: Optional[str] = Query(None, description="Comma-separated skills (e.g., Python,React)"),
    feasibility: Optional[float] = Query(None, description="Minimum feasibility score required"),
    sort_by: str = Query("created_at", description="Field to sort by (e.g., budget, feasibility, problem_validation_score)"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IdeaRead]:
    """Return the current user's accessible ideas with filters and sorting."""
    if min_budget is not None and max_budget is not None and min_budget > max_budget:
        raise HTTPException(
            status_code=400,
            detail="Invalid data: Minimum budget cannot be greater than maximum budget.",
        )

    skills_list = [skill.strip() for skill in skills.split(",")] if skills else None
    return IdeaService.get_user_ideas(
        db=db,
        user_id=current_user.id,
        min_budget=min_budget,
        max_budget=max_budget,
        skills=skills_list,
        feasibility=feasibility,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("/", response_model=IdeaRead)
def create_idea(
    idea_in: IdeaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Create a new business idea for the authenticated user."""
    return IdeaService.create_idea(
        db,
        current_user.id,
        idea_in.title,
        idea_in.description,
        budget=idea_in.budget,
        feasibility=idea_in.feasibility,
        skills=idea_in.skills,
        language=idea_in.language,
    )


@router.get("/shared-with-me", response_model=list[SharedIdeaItem])
def get_shared_with_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SharedIdeaItem]:
    """Return ideas shared with the current user through team membership, with per-idea role."""
    return IdeaService.get_ideas_shared_with_user(db=db, user_id=current_user.id)


@router.get("/favorites", response_model=list[IdeaRead])
def get_favorite_ideas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IdeaRead]:
    """Return all ideas the current user has favorited."""
    return IdeaService.get_favorited_ideas(db=db, user_id=current_user.id)


@router.post("/{idea_id}/favorite", status_code=204)
def favorite_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Add an idea to the current user's favorites."""
    IdeaService.favorite_idea(db=db, idea_id=idea_id, user_id=current_user.id)


@router.delete("/{idea_id}/favorite", status_code=204)
def unfavorite_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove an idea from the current user's favorites."""
    IdeaService.unfavorite_idea(db=db, idea_id=idea_id, user_id=current_user.id)


@router.get("/archived", response_model=list[IdeaRead])
def get_archived_ideas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IdeaRead]:
    """Return archived ideas accessible to the current user."""
    return IdeaService.get_archived_user_ideas(db=db, user_id=current_user.id)


@router.get("/{idea_id}", response_model=IdeaRead)
def get_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Return a single idea the user can access."""
    return IdeaService.get_idea(db=db, idea_id=idea_id, user_id=current_user.id)


@router.patch("/{idea_id}/archive", response_model=IdeaRead)
def archive_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Archive a business idea."""
    return IdeaService.archive_idea(db=db, idea_id=idea_id, user_id=current_user.id)


@router.patch("/{idea_id}/unarchive", response_model=IdeaRead)
def unarchive_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Restore an archived business idea."""
    return IdeaService.unarchive_idea(db=db, idea_id=idea_id, user_id=current_user.id)


@router.patch("/{idea_id}", response_model=IdeaRead)
def update_idea(
    idea_id: UUID,
    idea_in: IdeaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Update an idea owned by the authenticated user."""
    updates = idea_in.model_dump(exclude_unset=True)
    return IdeaService.update_idea(db=db, idea_id=idea_id, user_id=current_user.id, updates=updates)


@router.post("/{idea_id}/convert", response_model=IdeaRead)
def convert_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Mark a validated idea as converted — the user has decided to build it."""
    return IdeaService.convert_idea(db=db, idea_id=idea_id, user_id=current_user.id)


@router.delete("/{idea_id}", status_code=204)
def delete_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Permanently delete an idea owned by the authenticated user."""
    IdeaService.delete_idea(db=db, idea_id=idea_id, user_id=current_user.id)


@router.get("/{idea_id}/translations")
def get_idea_translations(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return which languages have cached translations for this idea."""
    idea = IdeaService.get_idea(db=db, idea_id=idea_id, user_id=current_user.id)
    rows = db.query(IdeaTranslation).filter(IdeaTranslation.idea_id == idea_id).all()
    languages = list({r.language for r in rows})
    return {"source_language": idea.language, "translated_languages": languages}


@router.post("/{idea_id}/translate")
async def translate_idea(
    idea_id: UUID,
    target_language: str = Query(..., pattern="^(en|ar)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Trigger a full-idea translation to target_language.
    Calls bizifyAI, caches results in idea_translations.
    """
    idea = IdeaService.get_idea(db=db, idea_id=idea_id, user_id=current_user.id)

    if idea.language == target_language:
        raise HTTPException(status_code=400, detail="Idea is already in the requested language.")

    try:
        # AI routes are mounted under /pipeline, and section rows are stored
        # under the idea OWNER's user_id (required by TranslateIdeaInput).
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{settings.AI_PIPELINE_BASE_URL}/pipeline/translate/idea",
                json={
                    "idea_id": str(idea_id),
                    "user_id": str(idea.owner_id),
                    "target_language": target_language,
                },
                headers={"X-API-Key": settings.AI_PIPELINE_API_KEY or ""},
            )
            resp.raise_for_status()
            translated: dict = resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Translation service error: {e}")

    # Delete stale cached translations for this language, then insert fresh ones
    db.query(IdeaTranslation).filter(
        IdeaTranslation.idea_id == idea_id,
        IdeaTranslation.language == target_language,
    ).delete()

    for section_name, content in translated.get("sections", {}).items():
        db.add(IdeaTranslation(
            idea_id=idea_id,
            language=target_language,
            section_name=section_name,
            content=content,
            model_used=translated.get("model_used"),
        ))

    db.commit()
    return {"status": "ok", "translated_sections": list(translated.get("sections", {}).keys())}


@router.get("/{idea_id}/content")
def get_idea_content_in_language(
    idea_id: UUID,
    lang: str = Query("en", pattern="^(en|ar)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Return translated section content for an idea.
    Falls back to source if translation not available.
    """
    IdeaService.get_idea(db=db, idea_id=idea_id, user_id=current_user.id)  # access check
    rows = (
        db.query(IdeaTranslation)
        .filter(IdeaTranslation.idea_id == idea_id, IdeaTranslation.language == lang)
        .all()
    )
    return {r.section_name: r.content for r in rows}
