"""
Extraction Worker Task - Processes extraction jobs from RabbitMQ.
Consumes messages, extracts facts, and updates job status.
"""
import asyncio
import threading
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.memory.application.services.extraction_service import (
    ExtractionService,
)
from app.domains.memory.application.services.job_service import JobService
from app.domains.memory.application.repositories.memory_repository import (
    IMemoryRepository,
)
from app.domains.memory.application.repositories.job_repository import (
    IJobRepository,
)
from app.domains.memory.domain.value_objects import ExtractionRequest
from app.domains.memory.infrastructure.repositories.memory_repository_impl import (
    MemoryRepositoryImpl,
)
from app.domains.memory.infrastructure.repositories.job_repository_impl import (
    JobRepositoryImpl,
)
from app.infrastructure.mem0.mem0_client import Mem0ClientWrapper
from app.infrastructure.database.postgres_session import get_db_session
from app.core.logging import get_logger
from app.core.exceptions import ServiceError

logger = get_logger(__name__)

# Thread-local event loop for worker thread
_worker_loop: Optional[asyncio.AbstractEventLoop] = None
_loop_lock = threading.Lock()


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get or create event loop for current thread.
    This ensures we reuse the same loop in the worker thread.
    """
    global _worker_loop
    with _loop_lock:
        if _worker_loop is None or _worker_loop.is_closed():
            _worker_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_worker_loop)
        return _worker_loop


async def process_extraction_job(message: Dict[str, Any]) -> None:
    """
    Process a single extraction job.
    
    Args:
        message: RabbitMQ message containing job details
    """
    job_id = message.get("job_id")
    user_id = message.get("user_id")
    conversation_id = message.get("conversation_id")
    conversation = message.get("conversation", [])
    metadata = message.get("metadata", {})
    
    logger.info(f"Processing extraction job: job_id={job_id}")
    
    # Initialize dependencies
    mem0_client = Mem0ClientWrapper()
    memory_repository = MemoryRepositoryImpl(mem0_client)
    
    async for db_session in get_db_session():
        try:
            # Initialize services
            job_repository = JobRepositoryImpl(db_session)
            job_service = JobService(job_repository)
            extraction_service = ExtractionService(memory_repository)
            
            # Update job status to processing
            await job_service.update_job_status(
                job_id=job_id,
                status="processing",
                progress=10,
                current_step="Extracting facts from conversation",
            )
            
            # Create extraction request
            request = ExtractionRequest(
                user_id=user_id,
                conversation_id=conversation_id,
                conversation=conversation,
                metadata=metadata,
            )
            
            # Extract facts
            await job_service.update_job_status(
                job_id=job_id,
                status="processing",
                progress=50,
                current_step="Storing extracted facts",
            )
            
            memories = await extraction_service.extract_facts(request)
            
            # Update job status to completed
            await job_service.update_job_status(
                job_id=job_id,
                status="completed",
                progress=100,
                current_step="Completed",
                data={"facts_extracted": len(memories)},
            )
            
            logger.info(
                f"Successfully processed extraction job: "
                f"job_id={job_id}, facts_extracted={len(memories)}"
            )
            break  # Exit after first session
        except Exception as e:
            logger.error(f"Error processing extraction job {job_id}: {e}")
            # Update job status to failed
            try:
                await job_service.update_job_status(
                    job_id=job_id,
                    status="failed",
                    error=str(e),
                )
            except Exception as update_error:
                logger.error(f"Error updating job status to failed: {update_error}")
            raise


def handle_extraction_message(message: Dict[str, Any]) -> None:
    """
    Handle extraction message from RabbitMQ.
    This is a synchronous wrapper for async processing.
    Uses thread-local event loop to avoid conflicts.
    
    Args:
        message: RabbitMQ message
    """
    try:
        # Get or create event loop for this thread
        loop = get_or_create_event_loop()
        
        # Set as current event loop for this thread
        asyncio.set_event_loop(loop)
        
        # Run async function in the loop
        loop.run_until_complete(process_extraction_job(message))
    except RuntimeError as e:
        if "attached to a different loop" in str(e) or "Event loop is closed" in str(e):
            # Event loop conflict - create new loop
            logger.warning("Event loop conflict detected, creating new loop")
            global _worker_loop
            with _loop_lock:
                if _worker_loop and not _worker_loop.is_closed():
                    try:
                        _worker_loop.close()
                    except:
                        pass
                _worker_loop = None
            # Retry with new loop
            loop = get_or_create_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_extraction_job(message))
        else:
            logger.error(f"Runtime error handling extraction message: {e}")
            raise Exception("Permanent processing error - do not requeue") from e
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error handling extraction message: {error_msg}")
        # Don't requeue if it's a permanent error (like asyncio loop issue)
        if "attached to a different loop" in error_msg or "Permanent processing error" in error_msg:
            logger.error("Permanent error detected, message will not be requeued")
            raise Exception("Permanent processing error - do not requeue") from e
        raise

