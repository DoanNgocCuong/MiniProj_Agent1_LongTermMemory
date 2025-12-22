"""
L0 Cache: In-memory session cache using functools.lru_cache.
Per-request cache with request lifetime.
"""
from functools import lru_cache
from typing import Any, Callable, Optional, TypeVar
from contextvars import ContextVar

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Request-scoped cache storage
_request_cache: ContextVar[dict] = ContextVar("request_cache", default={})


class L0SessionCache:
    """
    L0 Session Cache - In-memory cache for request lifetime.
    Uses context variables for request isolation.
    """
    
    def __init__(self):
        """Initialize L0 cache."""
        self.enabled = settings.CACHE_L0_ENABLED
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from L0 cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled:
            return None
        
        try:
            cache = _request_cache.get()
            value = cache.get(key)
            if value is not None:
                logger.debug(f"L0 cache HIT: {key}")
            return value
        except LookupError:
            # No cache in context, return None
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in L0 cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.enabled:
            return
        
        try:
            cache = _request_cache.get()
            cache[key] = value
            logger.debug(f"L0 cache SET: {key}")
        except LookupError:
            # No cache in context, create new one
            cache = {key: value}
            _request_cache.set(cache)
            logger.debug(f"L0 cache SET (new context): {key}")
    
    def clear(self) -> None:
        """Clear L0 cache for current request."""
        try:
            cache = _request_cache.get()
            cache.clear()
            logger.debug("L0 cache cleared")
        except LookupError:
            pass
    
    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        """
        Get value from cache or compute and set it.
        
        Args:
            key: Cache key
            factory: Callable that returns the value if not cached
            
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value)
        return value


# Global L0 cache instance
l0_cache = L0SessionCache()


def get_l0_cache() -> L0SessionCache:
    """Get L0 cache instance."""
    return l0_cache

