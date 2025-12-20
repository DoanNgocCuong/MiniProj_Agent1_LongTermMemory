"""
Query Pre-computation Service

Pre-computes and caches results for common queries to achieve <1ms latency on hit.
"""

from typing import List, Dict, Any
import asyncio

from app.infrastructure.cache.client import cache
from app.infrastructure.cache.l1_cache import l1_cache
from app.infrastructure.cache.semantic_cache import semantic_cache
from app.infrastructure.external.openai_client import openai_client
from app.domains.memory.application.services.fact_searcher_service import FactSearcherService
from app.core.logging import logger
from app.core.constants import CACHE_TTL_SEARCH_RESULTS


class PrecomputationService:
    """
    Service for pre-computing common queries
    
    Pre-computes results for top queries and stores in cache
    to achieve <1ms latency on hit.
    """
    
    def __init__(self, fact_searcher_service: FactSearcherService):
        self.fact_searcher_service = fact_searcher_service
    
    async def precompute_top_queries(
        self,
        user_id: str,
        queries: List[str],
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Pre-compute results for top queries
        
        Args:
            user_id: User ID
            queries: List of common queries to pre-compute
            limit: Result limit
            
        Returns:
            Statistics about pre-computation
        """
        stats = {
            "total": len(queries),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        logger.info(f"Pre-computing {len(queries)} queries for user {user_id}")
        
        for query in queries:
            try:
                # Generate embedding
                query_vector = await openai_client.generate_embedding(query)
                
                # Search facts
                results = await self.fact_searcher_service.search_facts(
                    user_id=user_id,
                    query=query,
                    limit=limit,
                    score_threshold=0.4
                )
                
                # Results are already cached by FactSearcherService
                # But we ensure they're in L1 cache too
                l1_key = f"{user_id}:{l1_cache.hash_query(query)}:{limit}"
                cache_data = {
                    "results": [
                        {
                            "fact": {
                                "id": r.fact.id,
                                "user_id": r.fact.user_id,
                                "content": r.fact.content,
                                "category": r.fact.category,
                                "confidence": r.fact.confidence,
                                "created_at": r.fact.created_at.isoformat(),
                                "metadata": r.fact.metadata
                            },
                            "score": r.score,
                            "matched_query": r.matched_query,
                            "related_facts": r.related_facts
                        }
                        for r in results
                    ]
                }
                l1_cache.set(l1_key, cache_data, ttl=3600)  # 1 hour TTL for pre-computed
                
                stats["success"] += 1
                logger.debug(f"Pre-computed query: {query[:50]}...")
                
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append({"query": query[:50], "error": str(e)})
                logger.error(f"Error pre-computing query {query[:50]}...: {e}")
        
        logger.info(f"Pre-computation completed: {stats['success']}/{stats['total']} successful")
        return stats
    
    async def precompute_default_queries(self, user_id: str) -> Dict[str, Any]:
        """
        Pre-compute default/common queries for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics about pre-computation
        """
        default_queries = [
            "Sở thích của tôi",
            "Gia đình của tôi",
            "Trường học của tôi",
            "Công việc của tôi",
            "Bạn bè của tôi",
            "Thú cưng của tôi",
            "Sở thích về phim ảnh",
            "Sở thích về âm nhạc",
            "Sở thích về thể thao",
            "Kỷ niệm đáng nhớ",
            "Món ăn yêu thích",
            "Địa điểm yêu thích",
            "Hoạt động yêu thích",
            "Người quan trọng",
            "Mục tiêu của tôi",
            "Thành tựu của tôi",
            "Kinh nghiệm của tôi",
            "Kiến thức của tôi",
            "Thói quen của tôi",
            "Cảm xúc của tôi",
        ]
        
        return await self.precompute_top_queries(user_id, default_queries)


# Background task to pre-compute queries
async def background_precomputation_task(fact_searcher_service: FactSearcherService):
    """
    Background task to pre-compute queries for active users
    
    This should be run periodically (e.g., daily) to keep cache warm.
    """
    # TODO: Get list of active users from database
    # For now, this is a placeholder
    logger.info("Background pre-computation task started")
    # await precomputation_service.precompute_default_queries(user_id)

