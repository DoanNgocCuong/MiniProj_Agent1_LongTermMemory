"""
Hybrid Search Implementation

Combines vector search (semantic) with keyword search (BM25) for better accuracy.
"""

from typing import List, Dict, Any, Optional
from app.infrastructure.search.milvus_client import milvus_client
from app.infrastructure.db.connection import db
from app.core.logging import logger


class HybridSearch:
    """
    Hybrid Search combining vector and keyword search
    
    Strategy:
    1. Vector search (semantic similarity) - primary
    2. Keyword search (BM25-like) - secondary
    3. Merge and re-rank results
    """
    
    async def search(
        self,
        user_id: str,
        query: str,
        query_vector: List[float],
        top_k: int = 20,
        score_threshold: float = 0.4,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + keyword)
        
        Args:
            user_id: User ID
            query: Search query
            query_vector: Query embedding vector
            top_k: Number of results
            score_threshold: Minimum similarity score
            keyword_weight: Weight for keyword search (0.0-1.0)
            vector_weight: Weight for vector search (0.0-1.0)
            
        Returns:
            List of search results with combined scores
        """
        try:
            # Step 1: Vector search (primary)
            vector_results = await milvus_client.search(
                query_vector=query_vector,
                user_id=user_id,
                top_k=top_k * 2,  # Get more for merging
                score_threshold=score_threshold
            )
            
            # Step 2: Keyword search (secondary) - simple text matching
            keyword_results = await self._keyword_search(
                user_id=user_id,
                query=query,  # Use query parameter directly
                top_k=top_k
            )
            
            # Step 3: Merge and re-rank results
            merged_results = self._merge_results(
                vector_results=vector_results,
                keyword_results=keyword_results,
                vector_weight=vector_weight,
                keyword_weight=keyword_weight,
                top_k=top_k
            )
            
            logger.debug(f"Hybrid search returned {len(merged_results)} results")
            return merged_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to vector search only
            return await milvus_client.search(
                query_vector=query_vector,
                user_id=user_id,
                top_k=top_k,
                score_threshold=score_threshold
            )
    
    async def _keyword_search(
        self,
        user_id: str,
        query: str,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Simple keyword search using PostgreSQL text matching
        
        Args:
            user_id: User ID
            query: Search query
            top_k: Number of results
            
        Returns:
            List of results with keyword match scores
        """
        try:
            # Extract keywords from query
            keywords = query.lower().split()
            
            # Build SQL query with text matching (parameterized to prevent SQL injection)
            # Simple ILIKE matching for keyword search
            if not keywords:
                return []
            
            # Use PostgreSQL array and ANY operator for safe parameterized query
            # Build pattern array
            patterns = [f"%{keyword}%" for keyword in keywords]
            
            query_sql = """
                SELECT 
                    fact_id,
                    content,
                    category,
                    confidence,
                    created_at,
                    CASE
                        WHEN content ILIKE ANY($3::text[]) THEN 1.0
                        ELSE 0.5
                    END as keyword_score
                FROM facts_metadata
                WHERE user_id = $1
                AND content ILIKE ANY($3::text[])
                ORDER BY keyword_score DESC, created_at DESC
                LIMIT $2
            """
            
            rows = await db.fetch(query_sql, user_id, top_k, patterns)
            
            results = []
            for row in rows:
                results.append({
                    "fact_id": row["fact_id"],
                    "user_id": user_id,
                    "content": row["content"],
                    "category": row["category"],
                    "confidence": row["confidence"],
                    "created_at": row["created_at"],
                    "score": float(row["keyword_score"]),
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        vector_weight: float,
        keyword_weight: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Merge and re-rank results from vector and keyword search
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            vector_weight: Weight for vector scores
            keyword_weight: Weight for keyword scores
            top_k: Number of final results
            
        Returns:
            Merged and re-ranked results
        """
        # Create mapping of fact_id to results
        result_map: Dict[str, Dict[str, Any]] = {}
        
        # Add vector results
        for result in vector_results:
            fact_id = result["fact_id"]
            if fact_id not in result_map:
                result_map[fact_id] = result.copy()
                result_map[fact_id]["vector_score"] = result["score"]
                result_map[fact_id]["keyword_score"] = 0.0
            else:
                result_map[fact_id]["vector_score"] = result["score"]
        
        # Add keyword results
        for result in keyword_results:
            fact_id = result["fact_id"]
            if fact_id not in result_map:
                result_map[fact_id] = result.copy()
                result_map[fact_id]["vector_score"] = 0.0
                result_map[fact_id]["keyword_score"] = result["score"]
            else:
                result_map[fact_id]["keyword_score"] = result["score"]
        
        # Calculate combined scores
        merged_results = []
        for fact_id, result in result_map.items():
            combined_score = (
                result["vector_score"] * vector_weight +
                result["keyword_score"] * keyword_weight
            )
            result["score"] = combined_score
            merged_results.append(result)
        
        # Sort by combined score (highest first)
        merged_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top K
        return merged_results[:top_k]


# Global hybrid search instance
hybrid_search = HybridSearch()

