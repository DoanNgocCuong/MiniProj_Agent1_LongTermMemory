"""
Extract Facts API Schemas

Request/Response models for extract_facts endpoint.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime


class Message(BaseModel):
    """Single message in conversation"""
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant']:
            raise ValueError('role must be "user" or "assistant"')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('content cannot be empty')
        if len(v) > 5000:
            raise ValueError('content too long (max 5000 chars)')
        return v.strip()


class ExtractFactsRequest(BaseModel):
    """Request model for extract_facts API"""
    user_id: str = Field(..., description="PIKA user unique ID")
    conversation_id: str = Field(..., description="Unique conversation ID")
    conversation: List[Message] = Field(..., description="Conversation messages")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('conversation')
    def validate_conversation(cls, v):
        if len(v) < 2:
            raise ValueError('conversation must have at least 2 messages')
        if len(v) > 100:
            raise ValueError('conversation too long (max 100 messages)')
        return v


class FactData(BaseModel):
    """Single fact in response"""
    id: str
    content: str
    category: str
    confidence: float
    created_at: str  # ISO format string


class ExtractFactsResponse(BaseModel):
    """Response model for extract_facts API"""
    status: str = "success"
    message: str
    data: Dict[str, Any]

