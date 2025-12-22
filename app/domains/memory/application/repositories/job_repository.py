"""
Repository interface for Job operations.
Follows Repository pattern and Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.domains.memory.domain.entities import Job


class IJobRepository(ABC):
    """Abstract repository interface for job operations."""
    
    @abstractmethod
    async def create(self, job: Job) -> Job:
        """
        Create a new job.
        
        Args:
            job: Job entity to create
            
        Returns:
            Created job entity with ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, job: Job) -> Job:
        """
        Update an existing job.
        
        Args:
            job: Job entity with updated fields
            
        Returns:
            Updated job entity
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """
        Get jobs by user ID.
        
        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of job entities
        """
        pass

