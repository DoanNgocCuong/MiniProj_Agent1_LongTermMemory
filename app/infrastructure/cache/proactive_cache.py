"""
Proactive Caching Service - Pre-computes user favorite summaries.
Updates L2 materialized view and warms up L1 Redis cache.
"""
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.memory.application.repositories.memory_repository import (
    IMemoryRepository,
)
from app.domains.memory.domain.value_objects import SearchQuery
from app.infrastructure.cache.l2_materialized_view import L2MaterializedView
from app.infrastructure.cache.l1_redis_cache import get_l1_cache
from app.infrastructure.cache.cache_service import CacheService
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import CacheError

logger = get_logger(__name__)


class ProactiveCacheService:
    """
    Proactive caching service for pre-computing user favorite summaries.
    Runs periodically to update L2 materialized view and warm up L1 cache.
    """
    
    def __init__(
        self,
        memory_repository: IMemoryRepository,
        l2_cache: L2MaterializedView,
    ):
        """
        Initialize proactive cache service.
        
        Args:
            memory_repository: Memory repository for searching
            l2_cache: L2 materialized view cache
        """
        self.memory_repository = memory_repository
        self.l2_cache = l2_cache
    
    async def update_user_favorite_cache(self, user_id: str) -> Dict[str, Any]:
        """
        Update user favorite cache for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Summary dictionary
        """
        try:
            logger.info(f"Updating favorite cache for user_id={user_id}")
            
            # Create search query for user favorites
            query = SearchQuery(
                query=settings.PROACTIVE_CACHE_USER_FAVORITE_QUERY,
                user_id=user_id,
                limit=50,
                score_threshold=0.3,
            )
            
            # Search memories
            results = await self.memory_repository.search(query)
            
            # Process and categorize results
            summary = self._categorize_results(results)
            summary["last_updated"] = str(datetime.utcnow().isoformat())
            
            # Update L2 materialized view
            await self.l2_cache.set_user_favorite_summary(user_id, summary)
            
            # Warm up L1 Redis cache
            l1_cache = await get_l1_cache()
            cache_key = CacheService.generate_user_favorite_key(user_id)
            await l1_cache.set(cache_key, summary)

            # Bump version tag and warm search key for favorite query
            version = await l1_cache.bump_user_version(user_id)
            search_key = CacheService.generate_search_key(
                user_id=user_id,
                query=settings.PROACTIVE_CACHE_USER_FAVORITE_QUERY,
                version=version,
            )
            await l1_cache.set(search_key, summary)
            
            logger.info(f"Successfully updated favorite cache for user_id={user_id}")
            return summary
        except Exception as e:
            logger.error(f"Error updating favorite cache for user_id={user_id}: {e}")
            raise CacheError(f"Failed to update favorite cache: {e}") from e
    
    def _categorize_results(self, results: List) -> Dict[str, List[str]]:
        """
        Categorize search results by type.
        
        Args:
            results: List of search results
            
        Returns:
            Categorized summary dictionary
        """
        summary: Dict[str, List[str]] = {
            "movies": [],
            "characters": [],
            "pets": [],
            "activities": [],
            "friends": [],
            "music": [],
            "travel": [],
            "toys": [],
        }
        
        for result in results:
            content = result.content.lower()
            metadata = result.metadata or {}
            categories = metadata.get("categories", [])
            
            # Categorize based on content and metadata
            if any(keyword in content for keyword in ["movie", "film", "cinema"]):
                summary["movies"].append(result.content)
            elif any(keyword in content for keyword in ["character", "hero", "superhero"]):
                summary["characters"].append(result.content)
            elif any(keyword in content for keyword in ["pet", "dog", "cat", "animal"]):
                summary["pets"].append(result.content)
            elif any(keyword in content for keyword in ["activity", "hobby", "sport", "game"]):
                summary["activities"].append(result.content)
            elif any(keyword in content for keyword in ["friend", "buddy", "pal"]):
                summary["friends"].append(result.content)
            elif any(keyword in content for keyword in ["music", "song", "artist", "band"]):
                summary["music"].append(result.content)
            elif any(keyword in content for keyword in ["travel", "trip", "vacation", "visit"]):
                summary["travel"].append(result.content)
            elif any(keyword in content for keyword in ["toy", "plaything", "game"]):
                summary["toys"].append(result.content)
        
        # Remove empty categories
        return {k: v for k, v in summary.items() if v}

