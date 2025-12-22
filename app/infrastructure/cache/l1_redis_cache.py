"""
L1 Cache: Redis cache for search results and frequently accessed data.
TTL: 1 hour (configurable).
"""
import json
from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import CacheError
from app.infrastructure.cache.cache_service import CacheService

logger = get_logger(__name__)


class L1RedisCache:
    """
    L1 Redis Cache - Distributed cache for search results.
    Uses Redis with connection pooling.
    """
    
    def __init__(self):
        """Initialize L1 Redis cache."""
        self.enabled = settings.CACHE_L1_ENABLED
        self.ttl = settings.CACHE_L1_TTL
        self.redis_client: Optional[redis.Redis] = None
        self._pool: Optional[ConnectionPool] = None
    
    async def connect(self) -> None:
        """Connect to Redis and create connection pool."""
        if not self.enabled:
            return
        
        try:
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
            )
            self.redis_client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("L1 Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheError(f"Failed to connect to Redis: {e}") from e
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("L1 Redis cache disconnected")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"L1 cache HIT: {key}")
                return CacheService.deserialize_value(value)
            logger.debug(f"L1 cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Error getting from L1 cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in Redis cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (defaults to configured TTL)
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            serialized = CacheService.serialize_value(value)
            ttl = ttl or self.ttl
            await self.redis_client.setex(key, ttl, serialized)
            logger.debug(f"L1 cache SET: {key} (TTL={ttl}s)")
        except Exception as e:
            logger.warning(f"Error setting L1 cache: {e}")
            # Don't raise - cache failures shouldn't break the app
    
    async def delete(self, key: str) -> None:
        """
        Delete value from Redis cache.
        
        Args:
            key: Cache key
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(key)
            logger.debug(f"L1 cache DELETE: {key}")
        except Exception as e:
            logger.warning(f"Error deleting from L1 cache: {e}")
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "search:user_123:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            count = 0
            async for key in self.redis_client.scan_iter(match=pattern):
                await self.redis_client.delete(key)
                count += 1
            logger.info(f"L1 cache deleted {count} keys matching pattern: {pattern}")
            return count
        except Exception as e:
            logger.warning(f"Error deleting pattern from L1 cache: {e}")
            return 0
    
    async def invalidate_user_cache(self, user_id: str) -> None:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID
        """
        patterns = CacheService.invalidate_user_cache(user_id)
        for pattern in patterns:
            await self.delete_pattern(pattern)

    # ----- User version tag helpers -----
    async def get_user_version(self, user_id: str) -> Optional[str]:
        """Get per-user version tag for cache invalidation."""
        if not self.enabled or not self.redis_client:
            return None
        try:
            return await self.redis_client.get(f"user:version:{user_id}")
        except Exception as e:
            logger.warning(f"Error getting user version for {user_id}: {e}")
            return None

    async def bump_user_version(self, user_id: str) -> str:
        """Increment and return per-user version tag (timestamp-based)."""
        if not self.enabled or not self.redis_client:
            return "0"
        try:
            new_version = CacheService.serialize_value({"ts": CacheService._now_ts()})
            # store as plain string ts for simplicity
            ts = CacheService._now_ts()
            await self.redis_client.set(f"user:version:{user_id}", str(ts))
            return str(ts)
        except Exception as e:
            logger.warning(f"Error bumping user version for {user_id}: {e}")
            return "0"


# Global L1 cache instance
l1_cache = L1RedisCache()


async def get_l1_cache() -> L1RedisCache:
    """Get L1 cache instance and ensure it's connected."""
    if not l1_cache.redis_client:
        await l1_cache.connect()
    return l1_cache

