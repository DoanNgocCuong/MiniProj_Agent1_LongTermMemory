"""
Extract Facts Endpoint

POST /api/v1/extract_facts
Extracts facts from conversation and stores them in vector/graph stores.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from app.api.v1.schemas.extract import ExtractFactsRequest, ExtractFactsResponse
from app.api.dependencies import get_fact_extractor_service
from typing import TYPE_CHECKING
from app.core.logging import logger
from app.core.exceptions import AppException

if TYPE_CHECKING:
    from app.domains.memory.application.services.fact_extractor_service import FactExtractorService

router = APIRouter()


@router.post("", response_model=ExtractFactsResponse)
async def extract_facts(
    request: ExtractFactsRequest,
    service: "FactExtractorService" = Depends(get_fact_extractor_service)
) -> ExtractFactsResponse:
    """
    Extract facts from conversation
    
    This endpoint extracts facts from a conversation and stores them
    in Milvus (vectors), Neo4j (relationships), and PostgreSQL (metadata).
    """
    try:
        logger.info(
            "Extract facts request",
            extra={
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "message_count": len(request.conversation)
            }
        )
        
        # Convert Pydantic models to dicts for service
        conversation_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation
        ]
        
        # Call service to extract facts
        facts = await service.extract_facts(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            conversation=conversation_dicts,
            metadata=request.metadata
        )
        
        # Convert Fact entities to dicts for response
        facts_data = []
        for fact in facts:
            facts_data.append({
                "id": fact.id,
                "content": fact.content,
                "category": fact.category,
                "confidence": fact.confidence,
                "created_at": fact.created_at.isoformat(),
            })
        
        return ExtractFactsResponse(
            status="success",
            message=f"Extracted {len(facts)} facts successfully",
            data={
                "facts_count": len(facts),
                "fact_ids": [fact.id for fact in facts],
                "facts": facts_data
            }
        )
        
    except AppException as e:
        logger.error(f"Application error extracting facts: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error extracting facts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
