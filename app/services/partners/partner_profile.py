# ruff: noqa
"""
Partner Profile CRUD operations and matching.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import PartnerProfile
from app.models.enums import ApprovalStatus, PartnerType
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.repositories.partner_repository import PartnerProfileRepository
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PartnerProfileService(BaseService):
    """Service for managing Partner Profiles and matching logic."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = PartnerProfileRepository(db)

    async def get_partner_profile(self, id: UUID) -> Optional[PartnerProfile]:
        """Retrieve a partner profile by ID."""
        return await self.repo.get(id)

    async def get_partner_profiles(self, skip: int = 0, limit: int = 100) -> List[PartnerProfile]:
        """Retrieve all partner profiles with pagination."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_partner_profile(
        self,
        user_id: Optional[UUID] = None,
        partner_type: Optional[PartnerType] = None,
        bio: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        obj_in: Any = None,
    ) -> PartnerProfile:
        """Create a new partner profile."""
        if obj_in is not None:
            data = _to_update_dict(obj_in)
            if "bio" in data and "description" not in data:
                data["description"] = data.pop("bio")
        elif hasattr(user_id, "model_dump"):
            data = user_id.model_dump(exclude_unset=True)
        else:
            data = {
                "user_id": user_id,
                "partner_type": partner_type,
                "description": bio,
                "services_json": details or {},
                "approval_status": ApprovalStatus.PENDING,
            }

        if data.get("details") and not data.get("services_json"):
             data["services_json"] = data.pop("details")

        if not data.get("approval_status"):
            data["approval_status"] = ApprovalStatus.PENDING

        return await self.repo.create_safe(data)

    async def update_partner_profile(self, db_obj: PartnerProfile, obj_in: Any) -> PartnerProfile:
        """Update an existing partner profile."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_partner_profile(self, id: UUID) -> Optional[PartnerProfile]:
        """Delete a partner profile by ID."""
        return await self.repo.delete(id)

    async def approve_partner_profile(self, profile_id: UUID, approver_id: UUID) -> Optional[PartnerProfile]:
        """Approve a partner profile."""
        profile = await self.repo.get(profile_id)
        if profile is None:
            return None

        return await self.repo.update(
            profile,
            {
                "approval_status": ApprovalStatus.APPROVED,
                "approved_by": approver_id,
                "approved_at": _utc_now()
            }
        )

    async def match_partners_by_capability(
        self,
        business_needs: Dict[str, Any],
        limit: int = 20,
        offset: int = 0,
        candidate_fetch_limit: int = 500,
    ) -> List[PartnerProfile]:
        """Score and rank approved partners based on business requirements.

        Uses DB-level filtering and a capped candidate pool to avoid
        loading unbounded rows into memory on large datasets.

        Args:
            business_needs: Dict with keys: required_type, skills, industry, budget.
            limit:          Max results to return after scoring.
            offset:         Pagination offset into the scored results.
            candidate_fetch_limit: Max rows fetched from DB before in-memory scoring.
                            Prevents OOM on large partner tables. Default: 500.
        """
        required_type = business_needs.get("required_type")
        required_skills = set(business_needs.get("skills", []))
        required_industry = business_needs.get("industry")
        budget = business_needs.get("budget", 0)

        # --- DB-level filtering (reduce candidate pool before Python scoring) ---
        candidates = await self.repo.get_approved_by_type(
            partner_type=required_type,
            limit=candidate_fetch_limit
        )

        # --- In-memory scoring (only on the capped candidate pool) ---
        scored_candidates = []
        for partner in candidates:
            score = 0
            services = partner.services_json or {}
            experience = partner.experience_json or {}

            partner_skills = set(services.get("skills", []) + experience.get("skills", []))
            common_skills = required_skills.intersection(partner_skills)
            score += len(common_skills) * 2

            partner_industry = experience.get("industry") or services.get("industry")
            if required_industry and partner_industry and str(required_industry).lower() == str(partner_industry).lower():
                score += 5

            if budget:
                min_budget = services.get("min_budget")
                max_budget = services.get("max_budget")
                budget_ok = (
                    (min_budget is None or budget >= min_budget) and
                    (max_budget is None or budget <= max_budget)
                )
                if budget_ok:
                    score += 3

            scored_candidates.append((score, partner))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Apply pagination on the sorted results
        page = scored_candidates[offset: offset + limit]
        return [p for _, p in page]
async def get_partner_profile_service(db: AsyncSession) -> PartnerProfileService:
    """Dependency provider for PartnerProfileService."""
    return PartnerProfileService(db)
