"""
Job Service - Manages asynchronous extraction jobs.
Handles job creation, status tracking, and RabbitMQ integration.
"""
from typing import Optional
from uuid import uuid4

from app.domains.memory.application.repositories.job_repository import IJobRepository
from app.domains.memory.domain.entities import Job
from app.domains.memory.domain.value_objects import ExtractionRequest
from app.infrastructure.messaging.rabbitmq_service import get_rabbitmq_service
from app.core.logging import get_logger
from app.core.exceptions import ServiceError, JobNotFoundError

logger = get_logger(__name__)


class JobService:
    """
    Job service for managing asynchronous extraction jobs.
    Handles job lifecycle and message queue integration.
    """
    
    def __init__(
        self,
        job_repository: IJobRepository,
    ):
        """
        Initialize job service.
        
        Args:
            job_repository: Job repository implementation
        """
        self.job_repository = job_repository
    
    async def create_extraction_job(
        self,
        request: ExtractionRequest,
    ) -> Job:
        """
        Create a new extraction job and enqueue it.
        
        Args:
            request: Extraction request value object
            
        Returns:
            Created job entity
        """
        try:
            # Create job entity
            job = Job(
                id=str(uuid4()),
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                status="pending",
                progress=0,
                current_step="Queued for processing",
            )
            
            # Save job to database
            created_job = await self.job_repository.create(job)
            logger.info(f"Created job: id={created_job.id}")
            
            # Enqueue job to RabbitMQ (graceful: continue even if RabbitMQ is down)
            rabbitmq = get_rabbitmq_service()
            message = {
                "job_id": created_job.id,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "conversation": request.conversation,
                "metadata": request.metadata,
            }
            published = rabbitmq.publish(message, raise_on_error=False)
            if published:
                logger.info(f"Enqueued job to RabbitMQ: id={created_job.id}")
            else:
                logger.warning(
                    f"Job created but not enqueued to RabbitMQ (RabbitMQ unavailable): "
                    f"id={created_job.id}. Worker will need to poll database for pending jobs."
                )
            
            return created_job
        except Exception as e:
            logger.error(f"Error creating extraction job: {e}")
            raise ServiceError(f"Failed to create extraction job: {e}") from e
    
    async def get_job_status(self, job_id: str) -> Job:
        """
        Get job status by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job entity
            
        Raises:
            JobNotFoundError: If job not found
        """
        try:
            job = await self.job_repository.get_by_id(job_id)
            if not job:
                raise JobNotFoundError(f"Job not found: {job_id}")
            return job
        except JobNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            raise ServiceError(f"Failed to get job status: {e}") from e
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        data: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> Job:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            progress: Progress percentage (0-100)
            current_step: Current processing step
            data: Result data
            error: Error message
            
        Returns:
            Updated job entity
        """
        try:
            # Get existing job
            job = await self.get_job_status(job_id)
            
            # Update fields
            job.update_status(status, current_step)
            if progress is not None:
                job.update_progress(progress)
            if data is not None:
                job.data = data
            if error is not None:
                job.error = error
            
            # Mark as completed or failed
            if status == "completed":
                job.mark_completed(data)
            elif status == "failed":
                job.mark_failed(error or "Unknown error")
            
            # Save updates
            updated_job = await self.job_repository.update(job)
            logger.info(f"Updated job: id={job_id}, status={status}")
            return updated_job
        except JobNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            raise ServiceError(f"Failed to update job status: {e}") from e

