"""
Search Facts Endpoint

POST /api/v1/search_facts
Searches for facts using semantic similarity.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import TYPE_CHECKING

from app.api.v1.schemas.search import SearchFactsRequest, SearchFactsResponse
from app.api.dependencies import get_fact_searcher_service
from app.core.logging import logger
from app.core.exceptions import AppException

if TYPE_CHECKING:
    from app.domains.memory.application.services.fact_searcher_service import FactSearcherService

router = APIRouter()


@router.post("", response_model=SearchFactsResponse)
async def search_facts(
    request: SearchFactsRequest,
    service: "FactSearcherService" = Depends(get_fact_searcher_service)
) -> SearchFactsResponse:
    """
    Search facts by semantic query
    
    Uses vector similarity search to find relevant facts for the user.
    """
    try:
        logger.info(
            "Search facts request",
            extra={
                "user_id": request.user_id,
                "query": request.query[:100],  # Log first 100 chars
                "limit": request.limit
            }
        )
        
        # Call service to search facts
        results = await service.search_facts(
            user_id=request.user_id,
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        # Convert SearchResult entities to dicts for response
        results_data = []
        for result in results:
            results_data.append({
                "fact_id": result.fact.id,
                "content": result.fact.content,
                "category": result.fact.category,
                "score": result.score,
                "created_at": result.fact.created_at.isoformat(),
                "related_facts": result.related_facts
            })
        
        return SearchFactsResponse(
            status="success",
            data={
                "query": request.query,
                "results_count": len(results),
                "results": results_data
            }
        )
        
    except AppException as e:
        logger.error(f"Application error searching facts: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error searching facts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
