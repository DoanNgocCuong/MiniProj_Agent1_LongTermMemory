"""
Cache service abstraction and utilities.
Provides cache key generation and invalidation strategies.
"""
import hashlib
import json
from typing import Any, Dict, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Cache service with key generation and utilities."""
    @staticmethod
    def _now_ts() -> int:
        """Return current timestamp seconds."""
        import time
        return int(time.time())
    
    @staticmethod
    def generate_cache_key(
        prefix: str,
        user_id: str,
        query: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a cache key from components.
        
        Args:
            prefix: Cache key prefix (e.g., "search", "embedding")
            user_id: User ID
            query: Query string (optional)
            **kwargs: Additional key components
            
        Returns:
            Cache key string
        """
        key_parts = [prefix, user_id]
        
        if query:
            # Hash query to keep key length manageable
            query_hash = hashlib.md5(query.encode()).hexdigest()
            key_parts.append(query_hash)
        
        # Add additional components
        for key, value in sorted(kwargs.items()):
            if value is not None:
                key_parts.append(f"{key}:{value}")
        
        return ":".join(key_parts)
    
    @staticmethod
    def generate_search_key(user_id: str, query: str, version: Optional[str] = None) -> str:
        """Generate cache key for search results with optional version tag."""
        return CacheService.generate_cache_key(
            prefix=settings.CACHE_L1_KEY_PREFIX,
            user_id=user_id,
            query=query,
            version=version,
        )
    
    @staticmethod
    def generate_embedding_key(query: str) -> str:
        """Generate cache key for embeddings."""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"{settings.CACHE_L3_KEY_PREFIX}:{query_hash}"
    
    @staticmethod
    def generate_user_favorite_key(user_id: str) -> str:
        """Generate cache key for user favorite summary."""
        return f"user_favorite:{user_id}"
    
    @staticmethod
    def serialize_value(value: Any) -> str:
        """Serialize value to JSON string."""
        return json.dumps(value, ensure_ascii=False, default=str)
    
    @staticmethod
    def deserialize_value(value: str) -> Any:
        """Deserialize JSON string to value."""
        return json.loads(value)
    
    @staticmethod
    def invalidate_user_cache(user_id: str) -> list[str]:
        """
        Generate list of cache keys to invalidate for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of cache key patterns to invalidate
        """
        return [
            f"{settings.CACHE_L1_KEY_PREFIX}:{user_id}:*",
            f"user_favorite:{user_id}",
        ]

