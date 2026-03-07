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

from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PartnerProfileService(BaseService):
    """Refactored class-based access to partner profiles."""
    async def get_partner_profile(self, id: UUID) -> Optional[PartnerProfile]:
        return await get_partner_profile(self.db, id)

    async def get_partner_profiles(self, skip: int = 0, limit: int = 100) -> List[PartnerProfile]:
        return await get_partner_profiles(self.db, skip, limit)

    async def create_partner_profile(self, **kwargs) -> PartnerProfile:
        return await create_partner_profile(self.db, **kwargs)

    async def update_partner_profile(self, db_obj: PartnerProfile, obj_in: Any) -> PartnerProfile:
        return await update_partner_profile(self.db, db_obj, obj_in)

    async def delete_partner_profile(self, id: UUID) -> Optional[PartnerProfile]:
        return await delete_partner_profile(self.db, id)

    async def approve_partner_profile(self, profile_id: UUID, approver_id: UUID) -> Optional[PartnerProfile]:
        return await approve_partner_profile(self.db, profile_id, approver_id)

    async def match_partners_by_capability(self, business_needs: Dict[str, Any]) -> List[PartnerProfile]:
        return await match_partners_by_capability(self.db, business_needs)


from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# PartnerProfile CRUD
# ----------------------------

async def get_partner_profile(db: AsyncSession, id: UUID) -> Optional[PartnerProfile]:
    return await db.get(PartnerProfile, id)



async def get_partner_profiles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PartnerProfile]:
    stmt = select(PartnerProfile).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())



async def create_partner_profile(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    partner_type: Optional[PartnerType] = None,
    bio: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    obj_in: Any = None,
) -> PartnerProfile:
    if obj_in is not None:
        data = _to_update_dict(obj_in)
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

    if not data.get("approval_status"):
        data["approval_status"] = ApprovalStatus.PENDING

    db_obj = PartnerProfile(**data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_partner_profile(db: AsyncSession, db_obj: PartnerProfile, obj_in: Any) -> PartnerProfile:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_partner_profile(db: AsyncSession, id: UUID) -> Optional[PartnerProfile]:
    db_obj = await get_partner_profile(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    return db_obj


async def approve_partner_profile(db: AsyncSession, profile_id: UUID, approver_id: UUID) -> Optional[PartnerProfile]:
    profile = await get_partner_profile(db, profile_id)
    if profile is None:
        return None

    profile.approval_status = ApprovalStatus.APPROVED
    profile.approved_by = approver_id
    profile.approved_at = _utc_now()
    await db.commit()
    await db.refresh(profile)
    return profile


async def match_partners_by_capability(db: AsyncSession, business_needs: Dict[str, Any]) -> List[PartnerProfile]:
    required_type = business_needs.get("required_type")
    required_skills = set(business_needs.get("skills", []))
    required_industry = business_needs.get("industry")
    budget = business_needs.get("budget", 0)

    stmt = select(PartnerProfile).where(PartnerProfile.approval_status == ApprovalStatus.APPROVED)
    if required_type is not None:
        stmt = stmt.where(PartnerProfile.partner_type == required_type)
        
    result = await db.execute(stmt)
    candidates = result.scalars().all()
    scored_candidates = []
    
    for partner in candidates:
        score = 0
        services = partner.services_json or {}
        experience = partner.experience_json or {}
        
        # Skill matching (+2 per skill)
        partner_skills = set(services.get("skills", []) + experience.get("skills", []))
        common_skills = required_skills.intersection(partner_skills)
        score += len(common_skills) * 2
        
        # Industry matching (+5)
        partner_industry = experience.get("industry") or services.get("industry")
        if required_industry and partner_industry and str(required_industry).lower() == str(partner_industry).lower():
            score += 5
            
        # Budget matching (+3)
        min_budget = services.get("min_budget")
        max_budget = services.get("max_budget")
        if budget:
            if min_budget is not None and budget < min_budget:
                pass # Too small budget
            elif max_budget is not None and budget > max_budget:
                pass # Too high budget
            else:
                score += 3 # Fits within budget or no budget constraints
                
        scored_candidates.append((score, partner))
        
    # Sort by score descending
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    return [p for score, p in scored_candidates]
