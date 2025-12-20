"""
Milvus Vector Store Client

Client for Milvus vector database operations (insert, search, delete).
"""

from typing import List, Optional, Dict, Any
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)
import numpy as np

from app.core.config import settings
from app.core.logging import logger


class MilvusClient:
    """Milvus vector database client"""
    
    def __init__(self):
        self.connected = False
        self.collection: Optional[Collection] = None
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.embedding_dim = 1536  # OpenAI text-embedding-3-small dimension
    
    async def connect(self):
        """Connect to Milvus server with timeout and authentication support"""
        try:
            # Prepare connection parameters
            # Note: pymilvus connections.connect() may not support timeout directly
            # Timeout is handled at gRPC level, but we can try to set it
            connect_params = {
                "alias": "default",
                "host": settings.MILVUS_HOST,
                "port": settings.MILVUS_PORT,
            }
            
            # Add authentication if provided
            if settings.MILVUS_USER and settings.MILVUS_PASSWORD:
                connect_params["user"] = settings.MILVUS_USER
                connect_params["password"] = settings.MILVUS_PASSWORD
            elif settings.MILVUS_PASSWORD:
                # Some Milvus setups only require password
                connect_params["password"] = settings.MILVUS_PASSWORD
            
            # Note: pymilvus connections.connect() doesn't support timeout parameter directly
            # Timeout is handled at gRPC channel level internally
            logger.debug(f"Connecting to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
            
            # Connect to Milvus (synchronous call, but fast)
            # Wrap in try-except to provide better error messages
            try:
                connections.connect(**connect_params)
            except Exception as connect_error:
                # Check if it's a connection timeout/refused error
                error_str = str(connect_error).lower()
                if "timeout" in error_str or "refused" in error_str or "unavailable" in error_str:
                    raise ConnectionError(
                        f"Cannot connect to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}. "
                        f"Please check:\n"
                        f"  1. Milvus server is running\n"
                        f"  2. Port {settings.MILVUS_PORT} is correct (default: 19530 for gRPC)\n"
                        f"  3. Network/firewall allows connection\n"
                        f"  4. Authentication credentials if required"
                    ) from connect_error
                raise
            self.connected = True
            logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
            
            # Load or create collection
            await self._ensure_collection()
            
        except Exception as e:
            self.connected = False
            error_msg = f"Failed to connect to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}: {e}"
            logger.error(error_msg)
            # Provide helpful error message
            error_str = str(e).lower()
            if "timeout" in error_str or "unavailable" in error_str or "illegal connection" in error_str:
                logger.warning(
                    f"Milvus connection failed. Possible causes:\n"
                    f"  1. Server may be down or not ready\n"
                    f"  2. Network/firewall blocking connection\n"
                    f"  3. Authentication required (check MILVUS_USER/MILVUS_PASSWORD)\n"
                    f"  4. Server not accepting connections on port {settings.MILVUS_PORT}\n"
                    f"  Set MILVUS_REQUIRED=false in .env to continue without Milvus"
                )
            raise
    
    async def disconnect(self):
        """Disconnect from Milvus"""
        if self.connected:
            connections.disconnect("default")
            self.connected = False
            logger.info("Disconnected from Milvus")
    
    async def _ensure_collection(self):
        """Ensure collection exists, create if not"""
        try:
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            else:
                await self._create_collection()
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    async def _create_collection(self):
        """Create Milvus collection with schema"""
        try:
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="fact_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.embedding_dim
                ),
                FieldSchema(name="confidence", dtype=DataType.FLOAT),
                FieldSchema(name="created_at", dtype=DataType.INT64),
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="PIKA user facts with embeddings"
            )
            
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
            )
            
            # Create index on embedding field
            # Try GPU-accelerated CAGRA first, fallback to CPU IVF_FLAT
            try:
                # Check if GPU is available
                import pymilvus
                # Try CAGRA (GPU-accelerated) index
                index_params = {
                    "metric_type": "IP",  # Inner Product (cosine similarity)
                    "index_type": "CAGRA",  # GPU-accelerated index
                    "params": {
                        "intermediate_graph_degree": 128,
                        "graph_degree": 64,
                        "gpu_id": 0  # Use first GPU if available
                    }
                }
                self.collection.create_index(
                    field_name="embedding",
                    index_params=index_params
                )
                logger.info("Created CAGRA (GPU-accelerated) index for Milvus")
            except Exception as e:
                # Fallback to CPU index if GPU not available
                logger.warning(f"GPU acceleration not available, using CPU index: {e}")
                index_params = {
                    "metric_type": "IP",  # Inner Product (cosine similarity)
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024}
                }
                self.collection.create_index(
                    field_name="embedding",
                    index_params=index_params
                )
                logger.info("Created IVF_FLAT (CPU) index for Milvus")
            
            logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    async def insert(
        self,
        fact_id: str,
        user_id: str,
        content: str,
        category: str,
        embedding: List[float],
        confidence: float,
        created_at: int
    ) -> bool:
        """
        Insert a fact with embedding into Milvus
        
        Args:
            fact_id: Unique fact ID
            user_id: User ID
            content: Fact content
            category: Fact category
            embedding: Vector embedding
            confidence: Extraction confidence
            created_at: Unix timestamp
            
        Returns:
            True if successful
        """
        try:
            # Prepare data
            data = [{
                "id": fact_id,
                "fact_id": fact_id,
                "user_id": user_id,
                "content": content,
                "category": category,
                "embedding": embedding,
                "confidence": confidence,
                "created_at": created_at,
            }]
            
            self.collection.insert(data)
            self.collection.flush()
            
            logger.info(f"✅ Inserted fact {fact_id} into Milvus (user_id: {user_id}, content: {content[:50]}...)")
            return True
        except Exception as e:
            logger.error(f"Error inserting into Milvus: {e}")
            return False
    
    async def search(
        self,
        query_vector: List[float],
        user_id: Optional[str] = None,
        top_k: int = 20,
        score_threshold: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Search for similar facts
        
        Args:
            query_vector: Query embedding vector
            user_id: Filter by user_id (optional)
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with scores
        """
        try:
            # Load collection into memory
            self.collection.load()
            
            # Build search parameters
            # Use GPU-optimized params if CAGRA index, otherwise CPU params
            try:
                # Check if collection uses CAGRA index
                index_info = self.collection.indexes
                uses_cagra = any(
                    hasattr(idx, 'params') and idx.params.get("index_type") == "CAGRA" 
                    for idx in index_info
                ) if index_info else False
                
                if uses_cagra:
                    # CAGRA (GPU) search parameters
                    search_params = {
                        "metric_type": "IP",
                        "params": {
                            "search_width": 1,
                            "min_iterations": 0,
                            "max_iterations": 0,
                            "itopk_size": 128
                        }
                    }
                else:
                    # IVF_FLAT (CPU) search parameters
                    search_params = {
                        "metric_type": "IP",
                        "params": {"nprobe": 10}
                    }
            except Exception:
                # Default to CPU params if index check fails
                search_params = {
                    "metric_type": "IP",
                    "params": {"nprobe": 10}
                }
            
            # Build filter expression
            expr = None
            if user_id:
                expr = f'user_id == "{user_id}"'
                logger.debug(f"Milvus search filter: {expr}")
            
            logger.debug(f"Performing Milvus search: top_k={top_k}, threshold={score_threshold}, has_filter={expr is not None}")
            
            # Perform search
            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["fact_id", "user_id", "content", "category", "confidence", "created_at"]
            )
            
            # Log raw results before filtering
            total_hits = sum(len(hits) for hits in results)
            logger.debug(f"Milvus search returned {total_hits} raw hits (before threshold filter)")
            
            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    score = float(hit.score)
                    logger.debug(f"Milvus hit: fact_id={hit.entity.get('fact_id')}, score={score:.4f}, threshold={score_threshold}")
                    if score >= score_threshold:
                        formatted_results.append({
                            "fact_id": hit.entity.get("fact_id"),
                            "user_id": hit.entity.get("user_id"),
                            "content": hit.entity.get("content"),
                            "category": hit.entity.get("category"),
                            "confidence": hit.entity.get("confidence"),
                            "created_at": hit.entity.get("created_at"),
                            "score": score,
                        })
                    else:
                        logger.debug(f"Hit filtered out: score {score:.4f} < threshold {score_threshold}")
            
            logger.info(f"Milvus search returned {len(formatted_results)} results (after threshold filter)")
            if not formatted_results and total_hits > 0:
                logger.warning(f"All {total_hits} hits were filtered out by score threshold {score_threshold}. Consider lowering threshold.")
            elif total_hits == 0:
                logger.warning(f"No hits found in Milvus. Check if facts exist for user_id={user_id}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching Milvus: {e}")
            return []
    
    async def delete(self, fact_id: str) -> bool:
        """Delete a fact by ID"""
        try:
            expr = f'fact_id == "{fact_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            logger.debug(f"Deleted fact {fact_id} from Milvus")
            return True
        except Exception as e:
            logger.error(f"Error deleting from Milvus: {e}")
            return False
    
    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete all facts for a user"""
        try:
            expr = f'user_id == "{user_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            logger.info(f"Deleted all facts for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user facts from Milvus: {e}")
            return False


# Global Milvus client instance
milvus_client = MilvusClient()

