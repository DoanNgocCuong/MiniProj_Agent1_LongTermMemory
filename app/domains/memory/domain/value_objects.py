"""
Value Objects for the Memory bounded context.
Value objects are immutable and defined by their attributes.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SearchQuery:
    """
    Value object representing a search query.
    Immutable to ensure consistency.
    
    Attributes:
        query: The search query string
        user_id: ID of the user performing the search
        limit: Maximum number of results to return
        score_threshold: Minimum similarity score threshold
        filters: Optional filters for the search
    """
    query: str
    user_id: str
    limit: int = 10
    score_threshold: float = 0.3
    filters: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate value object after creation."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        if not 0.0 <= self.score_threshold <= 1.0:
            raise ValueError("Score threshold must be between 0.0 and 1.0")


@dataclass(frozen=True)
class ExtractionRequest:
    """
    Value object representing a fact extraction request.
    Immutable to ensure consistency.
    
    Attributes:
        user_id: ID of the user
        conversation_id: ID of the conversation
        conversation: List of conversation turns
        metadata: Additional metadata
    """
    user_id: str
    conversation_id: str
    conversation: List[Dict[str, str]]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate value object after creation."""
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if not self.conversation_id:
            raise ValueError("Conversation ID cannot be empty")
        if not self.conversation:
            raise ValueError("Conversation cannot be empty")
        
        # Validate conversation format
        for turn in self.conversation:
            if not isinstance(turn, dict):
                raise ValueError("Each conversation turn must be a dictionary")
            if "role" not in turn or "content" not in turn:
                raise ValueError("Each turn must have 'role' and 'content' keys")
            if turn["role"] not in ["user", "assistant", "system"]:
                raise ValueError(f"Invalid role: {turn['role']}")


@dataclass(frozen=True)
class SearchResult:
    """
    Value object representing a search result.
    
    Attributes:
        id: Memory ID
        score: Similarity score
        content: Memory content
        metadata: Additional metadata
    """
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate value object after creation."""
        if not self.id:
            raise ValueError("Result ID cannot be empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")

