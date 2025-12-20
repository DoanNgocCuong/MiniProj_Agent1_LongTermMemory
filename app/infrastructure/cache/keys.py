"""
Cache Key Generation Constants

Centralized cache key patterns for consistency.
"""

from typing import Optional


class CacheKeys:
    """Cache key patterns"""
    
    # Search results cache
    @staticmethod
    def search_result(user_id: str, query_hash: str, limit: int) -> str:
        """Cache key for search results"""
        return f"search:{user_id}:{query_hash}:{limit}"
    
    # User facts cache
    @staticmethod
    def user_facts(user_id: str, version: str = "latest") -> str:
        """Cache key for user facts"""
        return f"user:facts:{user_id}:{version}"
    
    # Rate limiting
    @staticmethod
    def rate_limit(user_id: str, endpoint: str, window: str) -> str:
        """Cache key for rate limiting"""
        return f"ratelimit:{user_id}:{endpoint}:{window}"
    
    # API key cache
    @staticmethod
    def api_key(api_key: str) -> str:
        """Cache key for API key validation"""
        return f"api_key:{api_key}"
    
    # Job status (for async operations)
    @staticmethod
    def job_status(job_id: str) -> str:
        """Cache key for job status"""
        return f"job:status:{job_id}"
    
    # Embedding cache (for repeated queries)
    @staticmethod
    def embedding(text_hash: str) -> str:
        """Cache key for embedding"""
        return f"embedding:{text_hash}"

