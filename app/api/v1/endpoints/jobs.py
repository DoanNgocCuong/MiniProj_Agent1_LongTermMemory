"""
Job API endpoints - job status polling.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.jobs import JobStatusResponse
from app.api.dependencies import get_job_service
from app.domains.memory.application.services.job_service import JobService
from app.core.logging import get_logger, get_request_id, set_request_id
from app.core.exceptions import JobNotFoundError, ServiceError

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/jobs/{job_id}/status",
    response_model=JobStatusResponse,
    tags=["jobs"],
)
async def get_job_status(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
):
    """
    Get job status by ID.
    
    Returns current status, progress, and result data (if completed).
    """
    # Set request ID for correlation
    request_id = get_request_id()
    set_request_id(request_id)
    
    try:
        logger.info(f"Job status request: job_id={job_id}, request_id={request_id}")
        
        job = await job_service.get_job_status(job_id)
        
        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            data=job.data,
            error=job.error,
        )
    except JobNotFoundError as e:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

