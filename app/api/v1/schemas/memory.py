"""
Pydantic schemas for memory API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class SearchRequest(BaseModel):
    """Request schema for searching facts."""
    user_id: str = Field(..., description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID for STM context")
    query: str = Field(..., max_length=1000, description="Search query")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    score_threshold: float = Field(0.4, ge=0.0, le=1.0, description="Minimum similarity score")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID filter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "session_id": "sess_abc",
                "query": "What do I like?",
                "limit": 10,
                "score_threshold": 0.4,
            }
        }


class Fact(BaseModel):
    """Individual fact/memory schema."""
    id: str
    score: float
    source: Optional[str] = None
    user_id: str
    conversation_id: Optional[str] = None
    fact_type: Optional[List[str]] = None
    fact_value: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response schema for search results."""
    status: str = "ok"
    count: int
    facts: List[Fact]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "count": 2,
                "facts": [
                    {
                        "id": "mem_001",
                        "score": 0.95,
                        "source": "conversation",
                        "user_id": "user_123",
                        "fact_type": ["preference"],
                        "fact_value": "I like pizza",
                        "metadata": {},
                    }
                ],
            }
        }


class ConversationTurn(BaseModel):
    """Single turn in conversation."""
    role: str = Field(..., description="Role: user, assistant, or system")
    content: str = Field(..., description="Message content")


class ExtractRequest(BaseModel):
    """Request schema for extracting facts."""
    user_id: str = Field(..., description="User ID")
    conversation_id: str = Field(..., description="Conversation ID")
    conversation: List[ConversationTurn] = Field(..., description="Conversation turns")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "conversation_id": "conv_001",
                "conversation": [
                    {"role": "user", "content": "I like pizza and dogs"},
                    {"role": "assistant", "content": "That's great!"}
                ],
                "metadata": {},
            }
        }


class ExtractResponse(BaseModel):
    """Response schema for extract endpoint (202 Accepted)."""
    status: str = "accepted"
    job_id: str
    status_url: str = Field(..., description="URL to poll for job status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "job_id": "job_550e8400-e29b-41d4-a716-446655440000",
                "status_url": "/api/v1/jobs/job_550e8400-e29b-41d4-a716-446655440000/status",
            }
        }


class InlineExtractResponse(BaseModel):
    """Response schema for inline extract mode (no worker)."""
    status: str = "ok"
    count: int
    facts: List[Fact]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "count": 1,
                "facts": [
                    {
                        "id": "mem_001",
                        "score": 1.0,
                        "source": "conversation",
                        "user_id": "user_123",
                        "conversation_id": "conv_001",
                        "fact_type": None,
                        "fact_value": "Tôi tên là Nguyễn Văn A, sống ở Hà Nội.",
                        "metadata": {
                            "source": "test",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "conversation_id": "conv_001",
                        },
                    }
                ],
            }
        }

