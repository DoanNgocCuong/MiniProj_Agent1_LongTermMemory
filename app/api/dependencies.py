"""
Dependency injection functions for FastAPI.
Provides instances of services and repositories.
"""
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.postgres_session import get_db_session
from app.infrastructure.mem0.mem0_client import Mem0ClientWrapper
from app.domains.memory.application.repositories.memory_repository import (
    IMemoryRepository,
)
from app.domains.memory.application.repositories.job_repository import IJobRepository
from app.domains.memory.infrastructure.repositories.memory_repository_impl import (
    MemoryRepositoryImpl,
)
from app.domains.memory.infrastructure.repositories.job_repository_impl import (
    JobRepositoryImpl,
)
from app.domains.memory.application.services.memory_service import MemoryService
from app.domains.memory.application.services.extraction_service import (
    ExtractionService,
)
from app.domains.memory.application.services.job_service import JobService
from app.domains.memory.application.services.stm_service import STMService
from app.domains.memory.application.services.memory_orchestrator import (
    MemoryOrchestrator,
)
from app.infrastructure.cache.l2_materialized_view import L2MaterializedView
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache()
def get_mem0_client() -> Mem0ClientWrapper:
    """Get Mem0 client instance (singleton)."""
    return Mem0ClientWrapper()


async def get_memory_repository() -> IMemoryRepository:
    """Get memory repository instance."""
    mem0_client = get_mem0_client()
    return MemoryRepositoryImpl(mem0_client)


async def get_job_repository() -> IJobRepository:
    """Get job repository instance."""
    async for db_session in get_db_session():
        return JobRepositoryImpl(db_session)


async def get_memory_service() -> MemoryService:
    """Get memory service instance."""
    memory_repository = await get_memory_repository()
    # Get database session for L2 cache
    db_gen = get_db_session()
    db_session = await db_gen.__anext__()
    l2_cache = L2MaterializedView(db_session)
    return MemoryService(
        memory_repository=memory_repository,
        l2_cache=l2_cache,
    )


async def get_extraction_service() -> ExtractionService:
    """Get extraction service instance."""
    memory_repository = await get_memory_repository()
    return ExtractionService(memory_repository)


async def get_job_service() -> JobService:
    """Get job service instance."""
    job_repository = await get_job_repository()
    return JobService(job_repository)


@lru_cache()
def get_stm_service() -> STMService:
    """Get STM service singleton."""
    return STMService()


async def get_memory_orchestrator() -> MemoryOrchestrator:
    """Get orchestrator that runs STM + LTM in parallel."""
    stm_service = get_stm_service()
    memory_service = await get_memory_service()
    return MemoryOrchestrator(stm_service=stm_service, memory_service=memory_service)


async def get_db() -> AsyncSession:
    """Get database session."""
    async for session in get_db_session():
        yield session

