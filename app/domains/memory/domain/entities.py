"""
Domain entities for the Memory bounded context.
Entities represent core business objects with identity and behavior.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.domains.memory.domain.value_objects import SearchResult


@dataclass
class Memory:
    """
    Memory entity representing a stored fact/memory.
    
    Attributes:
        id: Unique identifier for the memory
        user_id: ID of the user who owns this memory
        content: The actual memory content/fact
        embedding: Vector embedding for semantic search (optional)
        source: Source of the memory (e.g., "conversation")
        metadata: Additional metadata as key-value pairs
        created_at: Timestamp when memory was created
        updated_at: Timestamp when memory was last updated
    """
    id: str
    user_id: str
    content: str
    embedding: Optional[List[float]] = None
    source: str = "conversation"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if not self.id:
            self.id = str(uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
    
    def update_content(self, new_content: str) -> None:
        """Update memory content and timestamp."""
        self.content = new_content
        self.updated_at = datetime.utcnow()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add or update metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()


@dataclass
class Fact:
    """
    Fact entity used primarily for compatibility with existing tests.
    Essentially a light-weight view over Memory/SearchResult.
    """
    id: str
    user_id: str
    value: str
    score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Job:
    """
    Job entity representing an asynchronous extraction job.
    
    Attributes:
        id: Unique identifier for the job
        user_id: ID of the user who initiated the job
        conversation_id: ID of the conversation being processed
        status: Current job status (pending, processing, completed, failed)
        progress: Progress percentage (0-100)
        current_step: Description of current processing step
        data: Job result data (optional)
        error: Error message if job failed (optional)
        created_at: Timestamp when job was created
        completed_at: Timestamp when job was completed (optional)
    """
    id: str
    user_id: str
    conversation_id: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed
    progress: int = 0
    current_step: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if not self.id:
            self.id = str(uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
    
    def update_status(self, status: str, step: Optional[str] = None) -> None:
        """Update job status and current step."""
        self.status = status
        if step:
            self.current_step = step
    
    def update_progress(self, progress: int) -> None:
        """Update job progress (0-100)."""
        self.progress = max(0, min(100, progress))
    
    def mark_completed(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Mark job as completed with optional result data."""
        self.status = "completed"
        self.progress = 100
        self.completed_at = datetime.utcnow()
        if data:
            self.data = data
    
    def mark_failed(self, error: str) -> None:
        """Mark job as failed with error message."""
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.utcnow()

