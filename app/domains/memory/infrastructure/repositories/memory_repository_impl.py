"""
Memory repository implementation using Mem0 client.
Implements IMemoryRepository interface.
"""
from typing import List, Optional

from app.domains.memory.application.repositories.memory_repository import (
    IMemoryRepository,
)
from app.domains.memory.domain.entities import Memory
from app.domains.memory.domain.value_objects import SearchQuery, SearchResult
from app.infrastructure.mem0.mem0_client import Mem0ClientWrapper
from app.core.logging import get_logger
from app.core.exceptions import RepositoryError, MemoryNotFoundError

logger = get_logger(__name__)


class MemoryRepositoryImpl(IMemoryRepository):
    """
    Memory repository implementation using Mem0.
    Delegates to Mem0 client for actual operations.
    """
    
    def __init__(self, mem0_client: Mem0ClientWrapper):
        """
        Initialize memory repository.
        
        Args:
            mem0_client: Mem0 client wrapper instance
        """
        self.mem0_client = mem0_client
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search memories by query."""
        try:
            logger.info(f"Searching memories: query='{query.query[:50]}...', user_id={query.user_id}")
            
            # Call Mem0 search
            results = await self.mem0_client.search(
                query=query.query,
                user_id=query.user_id,
                top_k=query.limit,
                threshold=query.score_threshold,
            )
            
            # Convert to SearchResult value objects
            search_results = []
            for result in results:
                try:
                    search_result = SearchResult(
                        id=result.get("id", ""),
                        score=result.get("score", 0.0),
                        content=result.get("memory", result.get("text", "")),
                        metadata=result.get("metadata", {}),
                    )
                    search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Failed to parse search result: {e}")
                    continue
            
            logger.info(f"Found {len(search_results)} memories")
            return search_results
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise RepositoryError(f"Failed to search memories: {e}") from e
    
    async def add(self, memory: Memory) -> Memory:
        """Add a new memory."""
        try:
            logger.info(f"Adding memory for user_id={memory.user_id}")
            
            # Convert Memory entity to Mem0 format
            messages = [{"role": "user", "content": memory.content}]
            
            # Call Mem0 add
            results = await self.mem0_client.add(
                messages=messages,
                user_id=memory.user_id,
                agent_id=memory.metadata.get("conversation_id"),
                metadata=memory.metadata,
            )
            
            # Update memory with result
            if results and len(results) > 0:
                result = results[0]
                memory.id = result.get("id", memory.id)
                if "data" in result:
                    memory.content = result["data"].get("memory", memory.content)
            
            logger.info(f"Successfully added memory: id={memory.id}")
            return memory
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise RepositoryError(f"Failed to add memory: {e}") from e
    
    async def get_by_id(self, memory_id: str, user_id: str) -> Optional[Memory]:
        """Get memory by ID."""
        # Mem0 doesn't have a direct get_by_id, so we use get_all and filter
        try:
            memories = await self.get_all(user_id=user_id, limit=1000)
            for memory in memories:
                if memory.id == memory_id:
                    return memory
            return None
        except Exception as e:
            logger.error(f"Error getting memory by ID: {e}")
            raise RepositoryError(f"Failed to get memory by ID: {e}") from e
    
    async def get_all(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Memory]:
        """Get all memories for a user."""
        try:
            logger.info(f"Getting all memories for user_id={user_id}")
            
            # Call Mem0 get_all
            results = await self.mem0_client.get_all(
                user_id=user_id,
                page_size=limit,
            )
            
            # Convert to Memory entities
            memories = []
            for result in results:
                try:
                    memory = Memory(
                        id=result.get("id", ""),
                        user_id=user_id,
                        content=result.get("memory", result.get("text", "")),
                        source=result.get("source", "conversation"),
                        metadata=result.get("metadata", {}),
                    )
                    memories.append(memory)
                except Exception as e:
                    logger.warning(f"Failed to parse memory: {e}")
                    continue
            
            # Apply pagination
            paginated_memories = memories[offset:offset + limit]
            logger.info(f"Retrieved {len(paginated_memories)} memories")
            return paginated_memories
        except Exception as e:
            logger.error(f"Error getting all memories: {e}")
            raise RepositoryError(f"Failed to get all memories: {e}") from e
    
    async def delete(self, memory_id: str, user_id: str) -> bool:
        """Delete a memory."""
        # Note: Mem0 client doesn't expose delete in the wrapper
        # This would need to be implemented if Mem0 supports it
        logger.warning("Delete operation not fully implemented for Mem0")
        raise NotImplementedError("Delete operation not yet implemented")

