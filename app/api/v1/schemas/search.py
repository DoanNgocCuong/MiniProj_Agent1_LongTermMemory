"""
Search Facts API Schemas

Request/Response models for search_facts endpoint.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class SearchFactsRequest(BaseModel):
    """Request model for search_facts API"""
    user_id: str = Field(..., description="PIKA user unique ID")
    query: str = Field(..., description="Natural language search query")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    score_threshold: float = Field(0.4, ge=0.0, le=1.0, description="Minimum similarity score")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('query cannot be empty')
        if len(v) > 500:
            raise ValueError('query too long (max 500 chars)')
        return v.strip()


class SearchResult(BaseModel):
    """Single search result"""
    fact_id: str
    content: str
    category: str
    score: float
    created_at: datetime
    related_facts: Optional[List[str]] = []


class SearchFactsResponse(BaseModel):
    """Response model for search_facts API"""
    status: str = "success"
    data: Dict[str, Any]

