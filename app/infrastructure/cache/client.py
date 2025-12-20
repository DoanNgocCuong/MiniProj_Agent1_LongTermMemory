"""
Redis Cache Client

Redis client wrapper with connection management and helper methods.
"""

from typing import Optional, Any, Union
import json
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import logger


class CacheClient:
    """Redis cache client wrapper"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
    
    async def connect(self):
        """Create Redis connection"""
        try:
            self.client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL (seconds)"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key"""
        try:
            return bool(await self.client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False


# Global cache instance
cache = CacheClient()

