"""
L1 In-Memory Cache

Application-level cache for extremely hot queries (top 1-5%).
Fastest cache layer with <1ms latency on hit.
"""

from typing import Optional, Dict, Any, Tuple
import time
from collections import OrderedDict
import hashlib

from app.core.logging import logger


class L1Cache:
    """
    L1 In-Memory LRU Cache
    
    Characteristics:
    - Fastest cache layer (<1ms latency)
    - Single-process, volatile
    - Limited capacity (~100MB-1GB)
    - Use case: Extremely hot queries (top 1-5%)
    """
    
    def __init__(self, maxsize: int = 1000, default_ttl: int = 60):
        """
        Initialize L1 cache
        
        Args:
            maxsize: Maximum number of entries (LRU eviction)
            default_ttl: Default TTL in seconds
        """
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if miss/expired
        """
        if key not in self.cache:
            self.misses += 1
            return None
        
        value, timestamp = self.cache[key]
        current_time = time.time()
        
        # Check if expired
        if current_time - timestamp > self.default_ttl:
            del self.cache[key]
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        
        logger.debug(f"L1 cache hit for key: {key[:50]}...")
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl or self.default_ttl
            timestamp = time.time()
            
            # If key exists, update it
            if key in self.cache:
                self.cache.move_to_end(key)
            
            # Add new entry
            self.cache[key] = (value, timestamp)
            
            # Evict oldest if over capacity
            if len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)  # Remove oldest
            
            return True
        except Exception as e:
            logger.error(f"L1 cache set error for key {key[:50]}...: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%"
        }
    
    @staticmethod
    def hash_query(query: str) -> str:
        """Generate hash for query (for cache key)"""
        return hashlib.sha256(query.encode()).hexdigest()[:16]


# Global L1 cache instance
l1_cache = L1Cache(maxsize=1000, default_ttl=60)

