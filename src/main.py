from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import logging
from datetime import datetime
from src.memory.mem_client import MemoryInterface

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s,%(msecs)d - %(name)s - %(levelname)s - %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Fact Extraction API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_client = MemoryInterface()


# Request/Response Models
class ConversationRequest(BaseModel):
    conversation: List[Dict[str, str]]  # [{"role": "user", "content": "..."}]
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    limit: int = 10
    score_threshold: float = 0.3


class FactResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    source: Optional[str] = None
    fact_type: Optional[str] = None
    fact_value: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    operation: Optional[str] = None
    score: Optional[float] = None


class SearchResultResponse(BaseModel):
    id: str
    score: float
    source: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    fact_type: Optional[List[str] | str ] = None
    fact_value: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/extract_facts", response_model=Dict, tags=["production"])
async def extract_facts(request: ConversationRequest):
    """
    Extract facts from conversation using Mem0 API
    """
    try:
        logger.info(f"Starting fact extraction for conversation: {request.conversation_id}")
        
        metadata = request.metadata
        if not isinstance(metadata, dict):
            metadata = {}
        metadata["conversation_id"] = request.conversation_id

        # Call MemoryClient to add memories
        memories = await memory_client.add(
            messages=request.conversation,
            user_id=request.user_id,
            agent_id=request.conversation_id,
            metadata=metadata,
        )
        
        logger.info(f"Extracted {len(memories)} facts")
        logger.info(f"===========Memories: {memories}")

        facts = []

        # Convert to response format
        facts = [
            FactResponse(
                id=mem.get("id"),
                source="conversation",
                user_id=request.user_id,
                fact_type=None,
                fact_value=mem.get("data").get("memory"),
                operation="ADD",
                metadata={},
                score=0
            )
            for mem in memories
        ]
        
        return {
            "status": "ok",
            "count": len(facts),
            "facts": facts
        }
        
    except Exception as e:
        logger.error(f"Error in fact extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search_facts", response_model=Dict, tags=["production"])
async def search_facts(request: SearchRequest):
    """
    Search facts using Mem0 API
    """
    try:
        logger.info(f"Searching facts with query: {request.query}")
        
        # Call MemoryClient to search memories
        results = await memory_client.search(
            query=request.query,
            user_id=request.user_id,
            agent_id=request.conversation_id,  # Using conversation_id as agent_id
            top_k=request.limit,
            threshold=request.score_threshold
        )
        
        logger.info(f"Found {len(results)} facts")
        logger.info(f"===========Results: {results}")
        
        # Convert to response format
        facts = [
            SearchResultResponse(
                id=result.get("id"),
                source="conversation",
                user_id=result.get("user_id"),
                conversation_id=request.conversation_id,
                fact_type=result.get("categories"),
                fact_value=result.get("memory"),
                metadata=result.get("metadata"),
                score=result.get("score"),
            )
            for result in results
        ]
        
        return {
            "status": "ok",
            "count": len(facts),
            "facts": facts
        }
        
    except Exception as e:
        logger.error(f"Error searching facts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_facts_by_days", response_model=Dict, tags=["production"])
async def get_facts_by_days(
    user_id: str,
    days: Optional[int] = None,
    conversation_id: Optional[str] = None,
    limit: int = 100
):
    """
    Get all memories from Mem0 using get_all method
    
    Args:
        user_id: User identifier
        conversation_id: Optional conversation identifier to filter by (used as agent_id)
        limit: Maximum number of memories to return (default: 100)
    """
    try:
        logger.info(f"Getting memories for user {user_id}" + 
                   (f" for conversation {conversation_id}" if conversation_id else ""))
        
        if limit <= 0:
            raise HTTPException(status_code=400, detail="Limit must be greater than 0")
        
        # Get memories from Mem0 using get_all
        memories = await memory_client.get_all(
            user_id=user_id,
            agent_id=conversation_id,
            days=days,
            page_size=limit
        )
        logger.info(f"===========Memories: {memories}")
        
        # Filter memories based on days condition
        if days is not None:
            current_datetime = datetime.now()
            filtered_memories = []
            for mem in memories:
                structured_attrs = mem.get("structured_attributes", {})
                mem_day = structured_attrs.get("day")
                mem_month = structured_attrs.get("month")
                mem_year = structured_attrs.get("year")
                
                if mem_day is not None and mem_month is not None and mem_year is not None:
                    try:
                        mem_datetime = datetime(year=mem_year, month=mem_month, day=mem_day)
                        days_diff = (current_datetime - mem_datetime).days
                        if days_diff <= days:
                            filtered_memories.append(mem)
                    except ValueError:
                        # Skip invalid dates
                        continue
            memories = filtered_memories
        
        facts = []
        for mem in memories:
            facts.append(
                FactResponse(
                    id=mem.get("id"),
                    source="conversation",
                    user_id=mem.get("user_id"),
                    fact_type=None,
                    fact_value=mem.get("memory"),
                    operation="GET",
                    metadata=mem.get("metadata", {}),
                    score=0
                )
            )
        
        return {
            "status": "ok",
            "facts": facts
        }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GET_MEMORIES] Error: {str(e)}")
        logger.error(f"Error in getting memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

