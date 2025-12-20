"""
Fact Extractor Service

Application service for extracting facts from conversations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from app.domains.memory.domain.entities import Fact
from app.domains.memory.application.repositories.fact_repository import IFactRepository
from app.infrastructure.external.openai_client import openai_client
from app.core.logging import logger


class FactExtractorService:
    """
    Service responsible for extracting facts from conversations
    
    This service orchestrates the fact extraction process:
    1. Call LLM to extract facts
    2. Generate embeddings
    3. Store in repositories (Milvus, Neo4j, PostgreSQL)
    """
    
    def __init__(
        self,
        fact_repository: IFactRepository,
    ):
        self.fact_repository = fact_repository
    
    async def extract_facts(
        self,
        user_id: str,
        conversation_id: str,
        conversation: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Fact]:
        """
        Extract facts from conversation
        
        Args:
            user_id: PIKA user ID
            conversation_id: Unique conversation ID
            conversation: List of messages [{"role": "user", "content": "..."}]
            metadata: Additional metadata
            
        Returns:
            List of extracted facts
        """
        try:
            logger.info(f"Extracting facts for user {user_id}, conversation {conversation_id}")
            
            # Step 1: Call LLM to extract facts
            extracted_facts_data = await openai_client.extract_facts(conversation)
            
            if not extracted_facts_data:
                logger.warning("No facts extracted from conversation")
                return []
            
            # Step 2: Generate embeddings for each fact
            fact_contents = [fact_data.get("content", "") for fact_data in extracted_facts_data]
            embeddings = await openai_client.generate_embeddings_batch(fact_contents)
            
            # Step 3: Create Fact entities
            facts = []
            for i, fact_data in enumerate(extracted_facts_data):
                fact = Fact(
                    user_id=user_id,
                    content=fact_data.get("content", ""),
                    category=fact_data.get("category", "unknown"),
                    confidence=float(fact_data.get("confidence", 0.8)),
                    entities=fact_data.get("entities", []),
                    embedding=embeddings[i] if i < len(embeddings) else None,
                    metadata={
                        **(metadata or {}),
                        "conversation_id": conversation_id,
                        "extracted_at": datetime.utcnow().isoformat(),
                    }
                )
                facts.append(fact)
            
            # Step 4: Store facts in repository (Milvus, Neo4j, PostgreSQL)
            stored_facts = []
            for fact in facts:
                try:
                    stored_fact = await self.fact_repository.create(fact)
                    stored_facts.append(stored_fact)
                except Exception as e:
                    logger.error(f"Error storing fact {fact.id}: {e}")
                    # Continue with other facts
            
            logger.info(f"Successfully extracted and stored {len(stored_facts)} facts")
            return stored_facts
            
        except Exception as e:
            logger.error(f"Error extracting facts: {e}")
            raise
