"""
Pydantic schemas for job API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class JobStatusResponse(BaseModel):
    """Response schema for job status polling."""
    job_id: str
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current processing step")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "progress": 100,
                "current_step": "Completed",
                "data": {
                    "facts_extracted": 2,
                },
                "error": None,
            }
        }

