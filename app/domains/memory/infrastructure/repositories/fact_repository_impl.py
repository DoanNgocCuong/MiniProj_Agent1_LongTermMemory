"""
Fact Repository Implementation

Concrete implementation of IFactRepository using Milvus, Neo4j, PostgreSQL.
"""

from typing import List, Optional
from datetime import datetime
import asyncio
import json

from app.domains.memory.domain.entities import Fact
from app.domains.memory.application.repositories.fact_repository import IFactRepository
from app.infrastructure.search.milvus_client import milvus_client
from app.infrastructure.search.hybrid_search import hybrid_search
from app.infrastructure.external.neo4j_client import neo4j_client
from app.infrastructure.db.connection import db
from app.infrastructure.db.models import FactMetadataModel
from app.core.config import settings
from app.core.logging import logger


class FactRepository(IFactRepository):
    """
    Concrete implementation of Fact repository
    
    Uses:
    - Milvus for vector storage
    - Neo4j for relationships
    - PostgreSQL for metadata
    """
    
    async def create(self, fact: Fact) -> Fact:
        """
        Create a new fact
        
        Stores fact in:
        1. Milvus (vector + metadata)
        2. Neo4j (user relationship)
        3. PostgreSQL (metadata for querying)
        """
        try:
            # Ensure user exists in Neo4j
            await neo4j_client.create_user_if_not_exists(fact.user_id)
            
            # Parallel storage operations (Milvus, Neo4j, PostgreSQL)
            created_at_timestamp = int(fact.created_at.timestamp())
            
            # Prepare parallel tasks
            tasks = []
            
            # Task 1: Store in Milvus (if embedding available)
            if fact.embedding:
                logger.debug(f"Inserting fact {fact.id} into Milvus with embedding (length: {len(fact.embedding)})")
                tasks.append(
                    milvus_client.insert(
                        fact_id=fact.id,
                        user_id=fact.user_id,
                        content=fact.content,
                        category=fact.category,
                        embedding=fact.embedding,
                        confidence=fact.confidence,
                        created_at=created_at_timestamp
                    )
                )
            else:
                logger.warning(f"Fact {fact.id} has no embedding, skipping Milvus insert")
            
            # Task 2: Create fact node in Neo4j
            tasks.append(
                neo4j_client.create_fact_node(
                    fact_id=fact.id,
                    user_id=fact.user_id,
                    content=fact.content,
                    category=fact.category,
                    confidence=fact.confidence
                )
            )
            
            # Task 3: Store metadata in PostgreSQL
            # Convert metadata dict to JSON string for asyncpg
            meta_data_json = json.dumps(fact.metadata) if fact.metadata else json.dumps({})
            tasks.append(
                db.execute(
                    """
                    INSERT INTO facts_metadata 
                    (fact_id, user_id, content, category, confidence, created_at, meta_data)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
                    ON CONFLICT (fact_id) DO UPDATE
                    SET content = EXCLUDED.content,
                        category = EXCLUDED.category,
                        confidence = EXCLUDED.confidence,
                        meta_data = EXCLUDED.meta_data
                    """,
                    fact.id,
                    fact.user_id,
                    fact.content,
                    fact.category,
                    fact.confidence,
                    fact.created_at,
                    meta_data_json  # JSON string, cast to jsonb in SQL
                )
            )
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in parallel storage task {i}: {result}")
                    raise result
                if result is False:
                    task_name = ["Milvus", "Neo4j", "PostgreSQL"][i]
                    raise Exception(f"Failed to store in {task_name}")
            
            logger.info(f"Created fact {fact.id} for user {fact.user_id}")
            return fact
            
        except Exception as e:
            logger.error(f"Error creating fact: {e}")
            raise
    
    async def get_by_id(self, fact_id: str) -> Optional[Fact]:
        """Get fact by ID from PostgreSQL"""
        try:
            row = await db.fetchrow(
                "SELECT * FROM facts_metadata WHERE fact_id = $1",
                fact_id
            )
            
            if not row:
                return None
            
            # Build Fact entity from database row
            # Parse meta_data from JSON string if needed
            meta_data = row.get("meta_data", {})
            if isinstance(meta_data, str):
                try:
                    meta_data = json.loads(meta_data)
                except (json.JSONDecodeError, TypeError):
                    meta_data = {}
            elif meta_data is None:
                meta_data = {}
            
            fact = Fact(
                id=row["fact_id"],
                user_id=row["user_id"],
                content=row["content"],
                category=row["category"],
                confidence=row["confidence"],
                created_at=row["created_at"],
                metadata=meta_data  # Map 'meta_data' column to 'metadata' field
            )
            
            return fact
            
        except Exception as e:
            logger.error(f"Error getting fact by ID: {e}")
            return None
    
    async def get_by_user_id(self, user_id: str, limit: int = 100) -> List[Fact]:
        """Get all facts for a user from PostgreSQL"""
        try:
            rows = await db.fetch(
                """
                SELECT * FROM facts_metadata 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
                """,
                user_id,
                limit
            )
            
            facts = []
            for row in rows:
                # Parse meta_data from JSON string if needed
                meta_data = row.get("meta_data", {})
                if isinstance(meta_data, str):
                    try:
                        meta_data = json.loads(meta_data)
                    except (json.JSONDecodeError, TypeError):
                        meta_data = {}
                elif meta_data is None:
                    meta_data = {}
                
                fact = Fact(
                    id=row["fact_id"],
                    user_id=row["user_id"],
                    content=row["content"],
                    category=row["category"],
                    confidence=row["confidence"],
                    created_at=row["created_at"],
                    metadata=meta_data  # Map 'meta_data' column to 'metadata' field
                )
                facts.append(fact)
            
            return facts
            
        except Exception as e:
            logger.error(f"Error getting facts by user ID: {e}")
            return []
    
    async def search_similar(
        self,
        user_id: str,
        query_vector: List[float],
        top_k: int = 20,
        score_threshold: float = 0.4,
        query_text: Optional[str] = None
    ) -> List[Fact]:
        """
        Search for similar facts using vector similarity in Milvus
        
        Enriches results with metadata from PostgreSQL and relationships from Neo4j
        """
        try:
            logger.debug(f"Searching similar facts for user {user_id}, top_k={top_k}, threshold={score_threshold}")
            
            # Use hybrid search if enabled, otherwise vector search only
            if settings.USE_HYBRID_SEARCH and query_text:
                logger.debug(f"Using hybrid search with query: {query_text[:50]}...")
                milvus_results = await hybrid_search.search(
                    user_id=user_id,
                    query=query_text,
                    query_vector=query_vector,
                    top_k=top_k,
                    score_threshold=score_threshold,
                    vector_weight=settings.HYBRID_VECTOR_WEIGHT,
                    keyword_weight=settings.HYBRID_KEYWORD_WEIGHT
                )
            else:
                # Vector search only
                logger.debug("Using vector search only")
                milvus_results = await milvus_client.search(
                    query_vector=query_vector,
                    user_id=user_id,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
            
            logger.debug(f"Milvus search returned {len(milvus_results)} results")
            if not milvus_results:
                logger.warning(f"No results from Milvus search for user {user_id}. Check if facts exist in Milvus.")
                return []
            
            # Get fact IDs
            fact_ids = [r["fact_id"] for r in milvus_results]
            
            # Load full metadata from PostgreSQL
            placeholders = ",".join([f"${i+1}" for i in range(len(fact_ids))])
            rows = await db.fetch(
                f"""
                SELECT * FROM facts_metadata 
                WHERE fact_id IN ({placeholders})
                """,
                *fact_ids
            )
            
            # Create mapping of fact_id to metadata
            metadata_map = {row["fact_id"]: row for row in rows}
            
            # Build Fact entities with scores
            facts = []
            for result in milvus_results:
                fact_id = result["fact_id"]
                if fact_id in metadata_map:
                    row = metadata_map[fact_id]
                    # Parse meta_data from JSON string if needed
                    meta_data = row.get("meta_data", {})
                    if isinstance(meta_data, str):
                        try:
                            meta_data = json.loads(meta_data)
                        except (json.JSONDecodeError, TypeError):
                            meta_data = {}
                    elif meta_data is None:
                        meta_data = {}
                    
                    fact = Fact(
                        id=fact_id,
                        user_id=row["user_id"],
                        content=row["content"],
                        category=row["category"],
                        confidence=row["confidence"],
                        created_at=row["created_at"],
                        metadata=meta_data  # Map 'meta_data' column to 'metadata' field
                    )
                    # Store score in metadata for ranking (ensure it's a dict)
                    if not isinstance(fact.metadata, dict):
                        fact.metadata = {}
                    fact.metadata["_similarity_score"] = result["score"]
                    facts.append(fact)
            
            # Sort by similarity score (highest first)
            facts.sort(key=lambda f: f.metadata.get("_similarity_score", 0), reverse=True)
            
            logger.debug(f"Found {len(facts)} similar facts for user {user_id}")
            return facts
            
        except Exception as e:
            logger.error(f"Error searching similar facts: {e}")
            return []
    
    async def get_related_facts(self, fact_id: str) -> List[str]:
        """Get related fact IDs from Neo4j"""
        try:
            relationships = await neo4j_client.get_fact_relationships(fact_id)
            return [rel["fact_id"] for rel in relationships]
        except Exception as e:
            logger.error(f"Error getting related facts: {e}")
            return []
    
    async def delete(self, fact_id: str) -> bool:
        """
        Delete a fact from all stores
        
        Removes from Milvus, Neo4j, and PostgreSQL
        """
        try:
            # Delete from Milvus
            await milvus_client.delete(fact_id)
            
            # Delete from Neo4j (relationships are deleted automatically with node)
            await neo4j_client.delete_fact_node(fact_id)
            
            # Delete from PostgreSQL
            await db.execute(
                "DELETE FROM facts_metadata WHERE fact_id = $1",
                fact_id
            )
            
            logger.info(f"Deleted fact {fact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting fact: {e}")
            return False
    
    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete all facts for a user (GDPR compliance)"""
        try:
            # Delete from Milvus
            await milvus_client.delete_by_user_id(user_id)
            
            # Delete from Neo4j
            await neo4j_client.delete_user_data(user_id)
            
            # Delete from PostgreSQL
            await db.execute(
                "DELETE FROM facts_metadata WHERE user_id = $1",
                user_id
            )
            
            logger.info(f"Deleted all facts for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user facts: {e}")
            return False
