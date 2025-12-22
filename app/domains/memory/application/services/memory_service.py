"""
Memory Service - Orchestrates memory search with multi-layer caching.
Implements cache layer orchestration (L0 → L1 → L2 → L3 → L4).
"""
import asyncio
from typing import List

from app.domains.memory.application.repositories.memory_repository import (
    IMemoryRepository,
)
from app.domains.memory.domain.value_objects import SearchQuery, SearchResult
from app.infrastructure.cache.l0_session_cache import get_l0_cache
from app.infrastructure.cache.l1_redis_cache import get_l1_cache
from app.infrastructure.cache.l2_materialized_view import L2MaterializedView
from app.infrastructure.cache.l3_embedding_cache import get_l3_cache
from app.infrastructure.cache.cache_service import CacheService
from app.core.logging import get_logger
from app.core.exceptions import ServiceError

logger = get_logger(__name__)


class MemoryService:
    """
    Memory service for searching memories with multi-layer caching.
    Orchestrates cache layers and repository calls.
    """
    
    def __init__(
        self,
        memory_repository: IMemoryRepository,
        l2_cache: L2MaterializedView,
    ):
        """
        Initialize memory service.
        
        Args:
            memory_repository: Memory repository implementation
            l2_cache: L2 materialized view cache
        """
        self.memory_repository = memory_repository
        self.l2_cache = l2_cache
    
    async def search_memories(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search memories with multi-layer cache orchestration.
        
        Cache layers:
        - L0: Session cache (in-memory, request lifetime)
        - L1: Redis cache (distributed, 1 hour TTL)
        - L2: Materialized view (PostgreSQL, pre-computed)
        - L3: Embedding cache (Redis, 24 hours TTL)
        - L4: Vector search (Mem0, fallback)
        
        Args:
            query: Search query value object
            
        Returns:
            List of search results
        """
        try:
            # L0: Check session cache
            l0_cache = get_l0_cache()
            # Get per-user version tag for invalidation
            l1_cache = await get_l1_cache()
            user_version = await l1_cache.get_user_version(query.user_id)
            cache_key = CacheService.generate_search_key(query.user_id, query.query, user_version)
            
            cached_result = l0_cache.get(cache_key)
            if cached_result is not None:
                logger.info("L0 cache HIT")
                return cached_result
            
            # L1: Check Redis cache
            cached_result = await l1_cache.get(cache_key)
            if cached_result is not None:
                logger.info("L1 cache HIT")
                # Update L0 cache
                l0_cache.set(cache_key, cached_result)
                return cached_result
            
            # L2: Check materialized view (for user favorite queries)
            if self._is_user_favorite_query(query.query):
                l2_result = await self.l2_cache.get_user_favorite_summary(query.user_id)
                if l2_result is not None:
                    logger.info("L2 cache HIT")
                    # Convert to SearchResult format
                    results = self._convert_l2_to_search_results(l2_result)
                    # Update L1 and L0 caches
                    await l1_cache.set(cache_key, results)
                    l0_cache.set(cache_key, results)
                    return results
            
            # L3 & L4: Fallback to vector search
            logger.info("Cache MISS - performing vector search")
            results = await self.memory_repository.search(query)
            
            # Update all cache layers
            l0_cache.set(cache_key, results)
            await l1_cache.set(cache_key, results)
            
            return results
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise ServiceError(f"Failed to search memories: {e}") from e
    
    def _is_user_favorite_query(self, query: str) -> bool:
        """Check if query is a user favorite query."""
        favorite_keywords = ["favorite", "like", "prefer", "love"]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in favorite_keywords)
    
    def _convert_l2_to_search_results(self, l2_data: dict) -> List[SearchResult]:
        """Convert L2 materialized view data to SearchResult list."""
        results = []
        for category, items in l2_data.items():
            if category == "last_updated":
                continue
            if isinstance(items, list):
                for item in items:
                    try:
                        result = SearchResult(
                            id=f"l2_{category}_{hash(item)}",
                            score=1.0,  # Pre-computed results have max score
                            content=item,
                            metadata={"category": category, "source": "l2_cache"},
                        )
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"Failed to convert L2 item: {e}")
        return results

