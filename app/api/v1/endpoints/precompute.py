"""
Pre-computation Endpoint

POST /api/v1/precompute
Pre-computes common queries for a user.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field

from app.api.dependencies import get_fact_searcher_service
from app.services.precomputation_service import PrecomputationService
from app.core.logging import logger
from app.core.exceptions import AppException
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.memory.application.services.fact_searcher_service import FactSearcherService

router = APIRouter()


class PrecomputeRequest(BaseModel):
    """Request model for pre-computation"""
    user_id: str = Field(..., description="PIKA user unique ID")
    queries: Optional[List[str]] = Field(None, description="Custom queries to pre-compute (uses defaults if not provided)")
    limit: int = Field(20, ge=1, le=100, description="Result limit per query")


class PrecomputeResponse(BaseModel):
    """Response model for pre-computation"""
    status: str = "success"
    message: str
    data: dict


@router.post("", response_model=PrecomputeResponse)
async def precompute_queries(
    request: PrecomputeRequest,
    fact_searcher_service: "FactSearcherService" = Depends(get_fact_searcher_service)
) -> PrecomputeResponse:
    """
    Pre-compute common queries for a user
    
    This endpoint pre-computes and caches results for common queries,
    achieving <1ms latency on subsequent searches.
    """
    try:
        logger.info(
            "Pre-computation request",
            extra={
                "user_id": request.user_id,
                "query_count": len(request.queries) if request.queries else "default"
            }
        )
        
        # Create precomputation service
        precomputation_service = PrecomputationService(fact_searcher_service)
        
        # Pre-compute queries
        if request.queries:
            stats = await precomputation_service.precompute_top_queries(
                user_id=request.user_id,
                queries=request.queries,
                limit=request.limit
            )
        else:
            # Use default queries
            stats = await precomputation_service.precompute_default_queries(
                user_id=request.user_id
            )
        
        return PrecomputeResponse(
            status="success",
            message=f"Pre-computed {stats['success']}/{stats['total']} queries successfully",
            data={
                "total": stats["total"],
                "success": stats["success"],
                "failed": stats["failed"],
                "errors": stats["errors"][:10]  # Limit errors in response
            }
        )
        
    except AppException as e:
        logger.error(f"Application error in pre-computation: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error in pre-computation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

