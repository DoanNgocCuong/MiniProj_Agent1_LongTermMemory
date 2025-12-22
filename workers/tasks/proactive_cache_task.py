"""
Proactive Caching Worker Task - Scheduled job to update user favorite caches.
Runs periodically (every 30 minutes by default) to pre-compute and cache results.
"""
import asyncio
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.proactive_cache import ProactiveCacheService
from app.infrastructure.database.postgres_session import get_db_session
from app.domains.memory.application.repositories.memory_repository import (
    IMemoryRepository,
)
from app.domains.memory.infrastructure.repositories.memory_repository_impl import (
    MemoryRepositoryImpl,
)
from app.infrastructure.mem0.mem0_client import Mem0ClientWrapper
from app.infrastructure.cache.l2_materialized_view import L2MaterializedView
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def run_proactive_caching_job(user_ids: List[str]) -> None:
    """
    Run proactive caching job for a list of users.
    
    Args:
        user_ids: List of user IDs to process
    """
    logger.info(f"Starting proactive caching job for {len(user_ids)} users")
    
    # Initialize dependencies
    mem0_client = Mem0ClientWrapper()
    memory_repository = MemoryRepositoryImpl(mem0_client)
    
    # Process each user
    db_gen = get_db_session()
    db_session = await db_gen.__anext__()
    try:
        l2_cache = L2MaterializedView(db_session)
        proactive_service = ProactiveCacheService(
            memory_repository=memory_repository,
            l2_cache=l2_cache,
        )
        
        success_count = 0
        error_count = 0
        
        for user_id in user_ids:
            try:
                await proactive_service.update_user_favorite_cache(user_id)
                success_count += 1
            except Exception as e:
                logger.error(f"Error updating cache for user_id={user_id}: {e}")
                error_count += 1
        
        logger.info(
            f"Proactive caching job completed: "
            f"success={success_count}, errors={error_count}"
        )
    except Exception as e:
        logger.error(f"Error in proactive caching job: {e}")
        raise
    finally:
        await db_session.close()


def get_all_user_ids() -> List[str]:
    """
    Get all user IDs from database.
    This is a placeholder - should query actual user table.
    
    Returns:
        List of user IDs
    """
    # TODO: Implement actual query to get all user IDs
    # For now, return empty list
    return []


if __name__ == "__main__":
    """Run proactive caching job manually."""
    user_ids = get_all_user_ids()
    asyncio.run(run_proactive_caching_job(user_ids))

