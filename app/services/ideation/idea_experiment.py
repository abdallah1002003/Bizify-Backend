from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Experiment
from app.models.enums import IdeaStatus, ExperimentStatus
from app.services.ideation import idea_service
from app.services.base_service import BaseService
from app.repositories.idea_repository import ExperimentRepository, IdeaRepository
from app.schemas.ideation.experiment import ExperimentCreate, ExperimentUpdate
from app.core.crud_utils import _to_update_dict
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_async_db

from app.models import Experiment, Idea
from app.models.enums import IdeaStatus, ExperimentStatus
from app.services.ideation import idea_service
from app.services.base_service import BaseService
from app.schemas.ideation.experiment import ExperimentCreate, ExperimentUpdate
from app.core.crud_utils import _to_update_dict, _apply_updates
>>>>>>> origin/main

logger = logging.getLogger(__name__)


class IdeaExperimentService(BaseService):
    """Service for managing Idea Experiments."""
<<<<<<< HEAD

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = ExperimentRepository(db)
        self.idea_repo = IdeaRepository(db)

    async def get_experiment(self, id: UUID) -> Optional[Experiment]:
        """Retrieve a single experiment by id."""
        return await self.repo.get(id)
=======
    db: AsyncSession

    async def get_experiment(self, id: UUID) -> Optional[Experiment]:
        """Retrieve a single experiment by id."""
        stmt = select(Experiment).where(Experiment.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
>>>>>>> origin/main

    async def get_experiments(
        self,
        idea_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Experiment]:
        """Retrieve experiments with optional idea filtering and pagination."""
<<<<<<< HEAD
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
=======
        stmt = select(Experiment)
        if idea_id is not None:
            stmt = stmt.where(Experiment.idea_id == idea_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_experiment(self, obj_in: ExperimentCreate) -> Experiment:
        """Create a new experiment record."""
        db_obj = Experiment(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_experiment(self, db_obj: Experiment, obj_in: ExperimentUpdate) -> Experiment:
        """Update an existing experiment record."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
>>>>>>> origin/main

    async def delete_experiment(self, id: UUID) -> Optional[Experiment]:
        """Delete an experiment and return the deleted record."""
        db_obj = await self.get_experiment(id=id)
<<<<<<< HEAD
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
=======
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    async def initiate_experiment(self, idea_id: UUID, hypothesis: str, creator_id: UUID) -> Experiment:
        """Logic for starting a new experiment on an idea."""
        if not await idea_service.check_idea_access(self.db, idea_id, creator_id, "experiment"):
>>>>>>> origin/main
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
<<<<<<< HEAD
        db_obj = await self.repo.get(exp_id)
        if not db_obj:
            return None

        db_obj = await self.repo.update(db_obj, {"status": status, "result_summary": result_json})

        if status == ExperimentStatus.COMPLETED:
            idea = await self.idea_repo.get(db_obj.idea_id)
            if idea is not None:
                await self.idea_repo.update(idea, {"status": IdeaStatus.VALIDATED})
=======
        db_obj = await self.get_experiment(id=exp_id)
        if not db_obj:
            return None

        db_obj.status = status
        db_obj.result_summary = result_json
        await self.db.commit()
        await self.db.refresh(db_obj)

        if status == ExperimentStatus.COMPLETED:
            stmt = select(Idea).where(Idea.id == db_obj.idea_id)
            result = await self.db.execute(stmt)
            idea = result.scalar_one_or_none()
            if idea is not None:
                idea.status = IdeaStatus.VALIDATED
                await self.db.commit()
>>>>>>> origin/main

        return db_obj


<<<<<<< HEAD
async def get_idea_experiment_service(db: AsyncSession) -> IdeaExperimentService:
    """Dependency provider for IdeaExperimentService."""
    return IdeaExperimentService(db)

=======
async def get_idea_experiment_service(db: AsyncSession = Depends(get_async_db)) -> IdeaExperimentService:
    """Dependency provider for IdeaExperimentService."""
    return IdeaExperimentService(db)


# ----------------------------
# Legacy Aliases
# ----------------------------

async def get_experiment(db: AsyncSession, id: UUID) -> Optional[Experiment]:
    return await IdeaExperimentService(db).get_experiment(id)


async def get_experiments(db: AsyncSession, idea_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[Experiment]:
    return await IdeaExperimentService(db).get_experiments(idea_id, skip, limit)


async def create_experiment(db: AsyncSession, obj_in: Any) -> Experiment:
    return await IdeaExperimentService(db).create_experiment(ExperimentCreate(**_to_update_dict(obj_in)))


async def update_experiment(db: AsyncSession, db_obj: Experiment, obj_in: Any) -> Experiment:
    return await IdeaExperimentService(db).update_experiment(db_obj, ExperimentUpdate(**_to_update_dict(obj_in)))


async def delete_experiment(db: AsyncSession, id: UUID) -> Optional[Experiment]:
    return await IdeaExperimentService(db).delete_experiment(id)


async def initiate_experiment(db: AsyncSession, idea_id: UUID, hypothesis: str, creator_id: UUID) -> Experiment:
    return await IdeaExperimentService(db).initiate_experiment(idea_id, hypothesis, creator_id)


async def finalize_experiment(db: AsyncSession, exp_id: UUID, result_json: dict, status: ExperimentStatus) -> Optional[Experiment]:
    return await IdeaExperimentService(db).finalize_experiment(exp_id, result_json, status)
>>>>>>> origin/main
