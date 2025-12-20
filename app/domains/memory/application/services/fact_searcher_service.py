"""
Fact Searcher Service

Application service for searching facts using semantic similarity.
"""

from typing import List, Optional
import asyncio
from app.domains.memory.domain.entities import Fact, SearchResult
from app.domains.memory.application.repositories.fact_repository import IFactRepository
from app.infrastructure.external.openai_client import openai_client
from app.infrastructure.cache.client import cache
from app.infrastructure.cache.l1_cache import l1_cache
from app.infrastructure.cache.semantic_cache import semantic_cache
from app.infrastructure.cache.keys import CacheKeys
from app.core.constants import CACHE_TTL_SEARCH_RESULTS
from app.core.logging import logger


class FactSearcherService:
    """
    Service responsible for searching facts
    
    This service orchestrates the search process:
    1. Check cache (L1, L2)
    2. Embed query
    3. Search in vector store (Milvus)
    4. Enrich with relationships (Neo4j)
    5. Re-rank results
    6. Cache results
    """
    
    def __init__(
        self,
        fact_repository: IFactRepository,
    ):
        self.fact_repository = fact_repository
    
    async def search_facts(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        score_threshold: float = 0.4
    ) -> List[SearchResult]:
        """
        Search facts by semantic query
        
        Args:
            user_id: PIKA user ID
            query: Natural language search query
            limit: Max results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results sorted by relevance
        """
        try:
            # Step 1: Check L1 cache (in-memory, fastest)
            l1_key = f"{user_id}:{l1_cache.hash_query(query)}:{limit}"
            l1_result = l1_cache.get(l1_key)
            if l1_result:
                logger.debug(f"L1 cache hit for query: {query[:50]}...")
                # Convert cached dict back to SearchResult objects
                results = []
                for item in l1_result.get("results", []):
                    fact = Fact(**item["fact"])
                    results.append(SearchResult(
                        fact=fact,
                        score=item["score"],
                        matched_query=item["matched_query"],
                        related_facts=item.get("related_facts", [])
                    ))
                return results
            
            # Step 2: Generate query embedding (needed for semantic cache)
            query_vector = await openai_client.generate_embedding(query)
            
            # Step 3: Check L2 cache with semantic similarity
            cached_result = await semantic_cache.get(
                user_id=user_id,
                query=query,
                query_vector=query_vector,
                limit=limit
            )
            
            if cached_result:
                logger.debug(f"L2 cache hit (semantic) for query: {query[:50]}...")
                # Convert cached dict back to SearchResult objects
                results = []
                for item in cached_result.get("results", []):
                    fact = Fact(**item["fact"])
                    results.append(SearchResult(
                        fact=fact,
                        score=item["score"],
                        matched_query=item["matched_query"],
                        related_facts=item.get("related_facts", [])
                    ))
                
                # Store in L1 cache for next time
                l1_cache.set(l1_key, cached_result, ttl=60)
                
                return results
            
            logger.debug(f"Cache miss for query: {query[:50]}...")
            
            # Step 4: Search in repository (Milvus) - with hybrid search support
            similar_facts = await self.fact_repository.search_similar(
                user_id=user_id,
                query_vector=query_vector,
                top_k=limit * 2,  # Get more for filtering and ranking
                score_threshold=score_threshold,
                query_text=query  # Pass query text for hybrid search
            )
            
            # Step 5: Enrich with related facts from Neo4j (parallel for multiple facts)
            search_results = []
            if similar_facts:
                # Parallel enrichment for better performance
                enrichment_tasks = [
                    self.fact_repository.get_related_facts(fact.id)
                    for fact in similar_facts
                ]
                related_facts_list = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
                
                for i, fact in enumerate(similar_facts):
                    related_fact_ids = related_facts_list[i] if not isinstance(related_facts_list[i], Exception) else []
                    
                    # Get similarity score from metadata
                    similarity_score = fact.metadata.get("_similarity_score", 0.0)
                    
                    result = SearchResult(
                        fact=fact,
                        score=similarity_score,
                        matched_query=query,
                        related_facts=related_fact_ids
                    )
                    search_results.append(result)
            
            # Step 6: Re-rank and limit results
            # Results are already sorted by similarity score from repository
            ranked_results = search_results[:limit]
            
            # Step 7: Cache results in L1 and L2 (semantic cache)
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
                    for r in ranked_results
                ]
            }
            
            # Store in L1 cache
            l1_cache.set(l1_key, cache_data, ttl=60)
            
            # Store in L2 semantic cache
            await semantic_cache.set(
                user_id=user_id,
                query=query,
                query_vector=query_vector,
                result=cache_data,
                limit=limit,
                ttl=CACHE_TTL_SEARCH_RESULTS
            )
            
            logger.info(f"Found {len(ranked_results)} facts for query: {query[:50]}...")
            return ranked_results
            
        except Exception as e:
            logger.error(f"Error searching facts: {e}")
            raise
