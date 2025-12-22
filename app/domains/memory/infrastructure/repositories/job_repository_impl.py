"""
Job repository implementation using PostgreSQL.
Implements IJobRepository interface.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.domains.memory.application.repositories.job_repository import IJobRepository
from app.domains.memory.domain.entities import Job
from app.domains.memory.infrastructure.models.job_model import JobModel
from app.core.logging import get_logger
from app.core.exceptions import RepositoryError, JobNotFoundError

logger = get_logger(__name__)


class JobRepositoryImpl(IJobRepository):
    """
    Job repository implementation using PostgreSQL.
    Uses SQLAlchemy async for database operations.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize job repository.
        
        Args:
            db_session: SQLAlchemy async session
        """
        self.db = db_session
    
    async def create(self, job: Job) -> Job:
        """Create a new job."""
        try:
            logger.info(f"Creating job: id={job.id}, user_id={job.user_id}")
            
            # Convert Job entity to ORM model
            job_model = JobModel(
                id=job.id,
                user_id=job.user_id,
                conversation_id=job.conversation_id,
                status=job.status,
                progress=job.progress,
                current_step=job.current_step,
                data=job.data,
                error=job.error,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
            
            self.db.add(job_model)
            await self.db.commit()
            await self.db.refresh(job_model)
            
            logger.info(f"Successfully created job: id={job.id}")
            return self._model_to_entity(job_model)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating job: {e}")
            raise RepositoryError(f"Failed to create job: {e}") from e
    
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        try:
            stmt = select(JobModel).where(JobModel.id == job_id)
            result = await self.db.execute(stmt)
            job_model = result.scalar_one_or_none()
            
            if job_model:
                return self._model_to_entity(job_model)
            return None
        except Exception as e:
            logger.error(f"Error getting job by ID: {e}")
            raise RepositoryError(f"Failed to get job by ID: {e}") from e
    
    async def update(self, job: Job) -> Job:
        """Update an existing job."""
        try:
            logger.info(f"Updating job: id={job.id}, status={job.status}")
            
            stmt = (
                update(JobModel)
                .where(JobModel.id == job.id)
                .values(
                    status=job.status,
                    progress=job.progress,
                    current_step=job.current_step,
                    data=job.data,
                    error=job.error,
                    completed_at=job.completed_at,
                )
            )
            
            await self.db.execute(stmt)
            await self.db.commit()
            
            # Fetch updated job
            updated_job = await self.get_by_id(job.id)
            if not updated_job:
                raise JobNotFoundError(f"Job not found after update: {job.id}")
            
            logger.info(f"Successfully updated job: id={job.id}")
            return updated_job
        except JobNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job: {e}")
            raise RepositoryError(f"Failed to update job: {e}") from e
    
    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Job]:
        """Get jobs by user ID."""
        try:
            stmt = (
                select(JobModel)
                .where(JobModel.user_id == user_id)
                .order_by(JobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await self.db.execute(stmt)
            job_models = result.scalars().all()
            
            jobs = [self._model_to_entity(model) for model in job_models]
            logger.info(f"Retrieved {len(jobs)} jobs for user_id={user_id}")
            return jobs
        except Exception as e:
            logger.error(f"Error getting jobs by user ID: {e}")
            raise RepositoryError(f"Failed to get jobs by user ID: {e}") from e
    
    def _model_to_entity(self, model: JobModel) -> Job:
        """Convert ORM model to domain entity."""
        return Job(
            id=model.id,
            user_id=model.user_id,
            conversation_id=model.conversation_id,
            status=model.status,
            progress=model.progress,
            current_step=model.current_step,
            data=model.data,
            error=model.error,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

