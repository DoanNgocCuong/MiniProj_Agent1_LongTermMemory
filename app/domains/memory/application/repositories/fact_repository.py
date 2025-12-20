"""
Fact Repository Interface

Abstract repository interface following Repository pattern.
Concrete implementations are in infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.domains.memory.domain.entities import Fact


class IFactRepository(ABC):
    """Abstract interface for Fact repository"""
    
    @abstractmethod
    async def create(self, fact: Fact) -> Fact:
        """Create a new fact"""
        pass
    
    @abstractmethod
    async def get_by_id(self, fact_id: str) -> Optional[Fact]:
        """Get fact by ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str, limit: int = 100) -> List[Fact]:
        """Get all facts for a user"""
        pass
    
    @abstractmethod
    async def search_similar(
        self,
        user_id: str,
        query_vector: List[float],
        top_k: int = 20,
        score_threshold: float = 0.4,
        query_text: Optional[str] = None
    ) -> List[Fact]:
        """Search for similar facts using vector similarity (with optional hybrid search)"""
        pass
    
    @abstractmethod
    async def delete(self, fact_id: str) -> bool:
        """Delete a fact"""
        pass

