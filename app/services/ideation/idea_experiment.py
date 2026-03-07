from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Experiment
from app.models.enums import IdeaStatus, ExperimentStatus
from app.services.ideation import idea_service
from app.services.base_service import BaseService
from app.repositories.idea_repository import ExperimentRepository, IdeaRepository
from app.schemas.ideation.experiment import ExperimentCreate, ExperimentUpdate
from app.core.crud_utils import _to_update_dict

logger = logging.getLogger(__name__)


class IdeaExperimentService(BaseService):
    """Service for managing Idea Experiments."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = ExperimentRepository(db)
        self.idea_repo = IdeaRepository(db)

    async def get_experiment(self, id: UUID) -> Optional[Experiment]:
        """Retrieve a single experiment by id."""
        return await self.repo.get(id)

    async def get_experiments(
        self,
        idea_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Experiment]:
        """Retrieve experiments with optional idea filtering and pagination."""
        if idea_id is not None:
            exps = await self.repo.get_for_idea(idea_id)
            return exps[skip:skip+limit]
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_experiment(self, obj_in: ExperimentCreate) -> Experiment:
        """Create a new experiment record."""
        return await self.repo.create(_to_update_dict(obj_in))

    async def update_experiment(self, db_obj: Experiment, obj_in: ExperimentUpdate) -> Experiment:
        """Update an existing experiment record."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_experiment(self, id: UUID) -> Optional[Experiment]:
        """Delete an experiment and return the deleted record."""
        db_obj = await self.get_experiment(id=id)
        if db_obj:
            return await self.repo.delete(db_obj)
        return None

    async def initiate_experiment(self, idea_id: UUID, hypothesis: str, creator_id: UUID) -> Experiment:
        """Logic for starting a new experiment on an idea."""
        from app.services.ideation.idea_access import IdeaAccessService
        from app.services.ideation.idea_version import IdeaVersionService
        if not await idea_service.IdeaService(
            self.db, 
            IdeaAccessService(self.db), 
            IdeaVersionService(self.db)
        ).check_idea_access(idea_id, creator_id, "experiment"):
            raise PermissionError("Not authorized to experiment on this idea")

        obj_in = ExperimentCreate(
            idea_id=idea_id,
            created_by=creator_id,
            hypothesis=hypothesis,
            status=ExperimentStatus.RUNNING,
            result_summary={},
        )
        return await self.create_experiment(obj_in)

    async def finalize_experiment(self, exp_id: UUID, result_json: dict, status: ExperimentStatus) -> Optional[Experiment]:
        """Logic for completing an experiment and updating idea status."""
        db_obj = await self.repo.get(exp_id)
        if not db_obj:
            return None

        db_obj = await self.repo.update(db_obj, {"status": status, "result_summary": result_json})

        if status == ExperimentStatus.COMPLETED:
            idea = await self.idea_repo.get(db_obj.idea_id)
            if idea is not None:
                await self.idea_repo.update(idea, {"status": IdeaStatus.VALIDATED})

        return db_obj


async def get_idea_experiment_service(db: AsyncSession) -> IdeaExperimentService:
    """Dependency provider for IdeaExperimentService."""
    return IdeaExperimentService(db)

