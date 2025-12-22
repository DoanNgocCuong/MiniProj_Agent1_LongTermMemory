"""
Extraction Service - Handles fact extraction from conversations.
Integrates with Mem0 and manages cache invalidation.
"""
from typing import List, Dict, Any

from app.domains.memory.application.repositories.memory_repository import (
    IMemoryRepository,
)
from app.domains.memory.domain.entities import Memory
from app.domains.memory.domain.value_objects import ExtractionRequest
from app.infrastructure.cache.l1_redis_cache import get_l1_cache
from app.infrastructure.cache.cache_service import CacheService
from app.core.logging import get_logger
from app.core.exceptions import ServiceError

logger = get_logger(__name__)


class ExtractionService:
    """
    Extraction service for extracting facts from conversations.
    Handles Mem0 integration and cache invalidation.
    """
    
    def __init__(self, memory_repository: IMemoryRepository):
        """
        Initialize extraction service.
        
        Args:
            memory_repository: Memory repository implementation
        """
        self.memory_repository = memory_repository
    
    async def extract_facts(self, request: ExtractionRequest) -> List[Memory]:
        """
        Extract facts from conversation.
        
        Args:
            request: Extraction request value object
            
        Returns:
            List of extracted memory entities
        """
        try:
            logger.info(
                f"Extracting facts for user_id={request.user_id}, "
                f"conversation_id={request.conversation_id}"
            )
            
            # Convert conversation to Memory entities and add via repository
            memories = []
            for turn in request.conversation:
                if turn["role"] == "user":
                    memory = Memory(
                        id="",  # Will be set by repository
                        user_id=request.user_id,
                        content=turn["content"],
                        source="conversation",
                        metadata={
                            **request.metadata,
                            "conversation_id": request.conversation_id,
                        },
                    )
                    # Add memory via repository (which calls Mem0)
                    created_memory = await self.memory_repository.add(memory)
                    memories.append(created_memory)
            
            # Invalidate user cache after extraction
            await self._invalidate_user_cache(request.user_id)
            
            logger.info(f"Successfully extracted {len(memories)} facts")
            return memories
        except Exception as e:
            logger.error(f"Error extracting facts: {e}")
            raise ServiceError(f"Failed to extract facts: {e}") from e
    
    async def _invalidate_user_cache(self, user_id: str) -> None:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID
        """
        try:
            l1_cache = await get_l1_cache()
            patterns = CacheService.invalidate_user_cache(user_id)
            
            for pattern in patterns:
                await l1_cache.delete_pattern(pattern)
            
            logger.info(f"Invalidated cache for user_id={user_id}")
        except Exception as e:
            logger.warning(f"Error invalidating cache: {e}")
            # Don't raise - cache invalidation failures shouldn't break extraction

