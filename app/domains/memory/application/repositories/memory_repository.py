"""
Repository interface for Memory operations.
Follows Repository pattern and Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domains.memory.domain.entities import Memory
from app.domains.memory.domain.value_objects import SearchQuery, SearchResult


class IMemoryRepository(ABC):
    """Abstract repository interface for memory operations."""
    
    @abstractmethod
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search memories by query.
        
        Args:
            query: Search query value object
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def add(self, memory: Memory) -> Memory:
        """
        Add a new memory.
        
        Args:
            memory: Memory entity to add
            
        Returns:
            Created memory entity
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, memory_id: str, user_id: str) -> Optional[Memory]:
        """
        Get memory by ID.
        
        Args:
            memory_id: Memory ID
            user_id: User ID for authorization
            
        Returns:
            Memory entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Memory]:
        """
        Get all memories for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of memory entities
        """
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str, user_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory ID
            user_id: User ID for authorization
            
        Returns:
            True if deleted, False otherwise
        """
        pass

