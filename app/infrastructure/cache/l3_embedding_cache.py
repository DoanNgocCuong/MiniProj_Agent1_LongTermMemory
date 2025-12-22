"""
L3 Cache: Embedding cache in Redis.
Caches query embeddings to avoid redundant API calls.
TTL: 24 hours.
"""
from typing import List, Optional
import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import CacheError
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.cache.l1_redis_cache import get_l1_cache

logger = get_logger(__name__)


class L3EmbeddingCache:
    """
    L3 Embedding Cache - Caches query embeddings in Redis.
    Reduces calls to embedding API (OpenAI, etc.).
    """
    
    def __init__(self):
        """Initialize L3 embedding cache."""
        self.enabled = settings.CACHE_L3_ENABLED
        self.ttl = settings.CACHE_L3_TTL
        # Reuse L1 Redis connection
        self._l1_cache = None
    
    async def _get_redis_client(self):
        """Get Redis client from L1 cache."""
        if not self._l1_cache:
            self._l1_cache = await get_l1_cache()
        return self._l1_cache.redis_client
    
    async def get_embedding(self, query: str) -> Optional[List[float]]:
        """
        Get cached embedding for a query.
        
        Args:
            query: Query string
            
        Returns:
            Cached embedding vector or None
        """
        if not self.enabled:
            return None
        
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return None
            
            key = CacheService.generate_embedding_key(query)
            value = await redis_client.get(key)
            
            if value:
                logger.debug(f"L3 embedding cache HIT: query='{query[:50]}...'")
                return CacheService.deserialize_value(value)
            logger.debug(f"L3 embedding cache MISS: query='{query[:50]}...'")
            return None
        except Exception as e:
            logger.warning(f"Error getting from L3 embedding cache: {e}")
            return None
    
    async def set_embedding(self, query: str, embedding: List[float]) -> None:
        """
        Cache embedding for a query.
        
        Args:
            query: Query string
            embedding: Embedding vector
        """
        if not self.enabled:
            return
        
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return
            
            key = CacheService.generate_embedding_key(query)
            serialized = CacheService.serialize_value(embedding)
            await redis_client.setex(key, self.ttl, serialized)
            logger.debug(f"L3 embedding cache SET: query='{query[:50]}...' (TTL={self.ttl}s)")
        except Exception as e:
            logger.warning(f"Error setting L3 embedding cache: {e}")
            # Don't raise - cache failures shouldn't break the app
    
    async def delete_embedding(self, query: str) -> None:
        """
        Delete cached embedding for a query.
        
        Args:
            query: Query string
        """
        if not self.enabled:
            return
        
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return
            
            key = CacheService.generate_embedding_key(query)
            await redis_client.delete(key)
            logger.debug(f"L3 embedding cache DELETE: query='{query[:50]}...'")
        except Exception as e:
            logger.warning(f"Error deleting from L3 embedding cache: {e}")


# Global L3 cache instance
l3_cache = L3EmbeddingCache()


async def get_l3_cache() -> L3EmbeddingCache:
    """Get L3 embedding cache instance."""
    return l3_cache

