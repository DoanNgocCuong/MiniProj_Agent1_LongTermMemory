"""
Memory Domain Entities

Domain entities representing core business concepts.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4


@dataclass
class Fact:
    """
    Fact Entity - Core domain entity
    
    Represents a fact extracted from conversation about a user.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    content: str = ""
    category: str = "unknown"
    confidence: float = 0.0
    entities: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.content:
            raise ValueError("content is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass
class Conversation:
    """
    Conversation Entity
    
    Represents a conversation between user and assistant.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)
    facts_extracted: List[str] = field(default_factory=list)  # Fact IDs
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """
    Search Result Entity
    
    Represents a search result with score and metadata.
    """
    fact: Fact
    score: float
    matched_query: str
    related_facts: List[str] = field(default_factory=list)

