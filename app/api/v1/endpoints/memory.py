"""
Memory API endpoints - search_facts and extract_facts.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Union

from app.api.v1.schemas.memory import (
    SearchRequest,
    SearchResponse,
    ExtractRequest,
    ExtractResponse,
    InlineExtractResponse,
    Fact,
)
from app.api.dependencies import (
    get_memory_orchestrator,
    get_job_service,
    get_extraction_service,
)
from app.domains.memory.application.services.memory_orchestrator import (
    MemoryOrchestrator,
)
from app.domains.memory.application.services.job_service import JobService
from app.domains.memory.application.services.extraction_service import (
    ExtractionService,
)
from app.domains.memory.domain.value_objects import ExtractionRequest
from app.core.logging import get_logger, get_request_id, set_request_id
from app.core.exceptions import ServiceError, ValidationError
from app.core.config import settings
from uuid import uuid4

logger = get_logger(__name__)

router = APIRouter()


@router.post("/search_facts", response_model=SearchResponse, tags=["memory"])
async def search_facts(
    request: SearchRequest,
    orchestrator: MemoryOrchestrator = Depends(get_memory_orchestrator),
):
    """
    Search facts/memories by query.
    
    Uses multi-layer caching (L0 → L1 → L2 → L3 → L4) for LTM
    and STM context in parallel, then merges results.
    """
    # Set request ID for correlation
    request_id = get_request_id()
    set_request_id(request_id)
    
    try:
        logger.info(
            f"Search request: user_id={request.user_id}, "
            f"query='{request.query[:50]}...', request_id={request_id}"
        )
        
        # Convert request to value object
        # Search STM + LTM in parallel via orchestrator
        results = await orchestrator.search(
            user_id=request.user_id,
            session_id=request.session_id or request.user_id,
            query=request.query,
            limit=request.limit,
        )
        
        # Convert to response format
        facts = [
            Fact(
                id=result.id,
                score=result.score,
                source="conversation",
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                fact_type=result.metadata.get("categories", []),
                fact_value=result.content,
                metadata=result.metadata,
            )
            for result in results
        ]
        
        logger.info(
            f"Search completed: found {len(facts)} facts, request_id={request_id}"
        )
        
        return SearchResponse(status="ok", count=len(facts), facts=facts)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/extract_facts",
    response_model=Union[ExtractResponse, InlineExtractResponse],
    status_code=status.HTTP_202_ACCEPTED,
    tags=["memory"],
)
async def extract_facts(
    request: ExtractRequest,
    job_service: JobService = Depends(get_job_service),
    extraction_service: ExtractionService = Depends(get_extraction_service),
):
    """
    Extract facts from conversation.

    Mặc định (`USE_ASYNC_WORKER_FOR_EXTRACTION=True`): xử lý bất đồng bộ qua Job + RabbitMQ.
    Khi `USE_ASYNC_WORKER_FOR_EXTRACTION=False`: tạm thời xử lý trực tiếp trong luồng (INLINE), không qua worker.
    """
    # Set request ID for correlation
    request_id = get_request_id()
    set_request_id(request_id)
    
    try:
        logger.info(
            f"Extract request: user_id={request.user_id}, "
            f"conversation_id={request.conversation_id}, request_id={request_id}"
        )
        
        # Convert request to value object (dùng chung cho async & inline)
        extraction_request = ExtractionRequest(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            conversation=[
                {"role": turn.role, "content": turn.content}
                for turn in request.conversation
            ],
            metadata=request.metadata,
        )

        # ---------- INLINE MODE (bypass worker) ----------
        if not settings.USE_ASYNC_WORKER_FOR_EXTRACTION:
            logger.info(
                "Running extract_facts in INLINE mode (USE_ASYNC_WORKER_FOR_EXTRACTION=False, bypass worker/RabbitMQ)"
            )
            memories = await extraction_service.extract_facts(extraction_request)

            # Map Memory entities -> API Fact schema (giống /search_facts)
            facts: List[Fact] = []
            for mem in memories:
                conv_id = mem.metadata.get("conversation_id")
                facts.append(
                    Fact(
                        id=mem.id,
                        score=1.0,
                        source=mem.source,
                        user_id=mem.user_id,
                        conversation_id=conv_id,
                        fact_type=None,
                        fact_value=mem.content,
                        metadata=mem.metadata,
                    )
                )

            # Trả về InlineExtractResponse để phù hợp response_model
            return InlineExtractResponse(status="ok", count=len(facts), facts=facts)

        # ---------- ASYNC MODE (design gốc, dùng worker) ----------
        # Create extraction job
        job = await job_service.create_extraction_job(extraction_request)
        
        logger.info(
            f"Extraction job created: job_id={job.id}, request_id={request_id}"
        )
        
        return ExtractResponse(
            status="accepted",
            job_id=job.id,
            status_url=f"/api/v1/jobs/{job.id}/status",
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

