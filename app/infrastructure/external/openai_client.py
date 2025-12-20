"""
OpenAI API Client

Client for OpenAI API operations (embeddings, LLM calls).
"""

from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
import hashlib

from app.core.config import settings
from app.core.logging import logger


class OpenAIClient:
    """OpenAI API client wrapper"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.llm_model = settings.OPENAI_LLM_MODEL
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (1536 dimensions for text-embedding-3-small)
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    async def extract_facts(
        self,
        conversation: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract facts from conversation using LLM
        
        Args:
            conversation: List of messages [{"role": "user", "content": "..."}]
            system_prompt: Optional custom system prompt
            
        Returns:
            List of extracted facts with metadata
        """
        try:
            if system_prompt is None:
                system_prompt = """
You are an AI assistant specialized in extracting factual information from conversations.

Your task: Analyze the conversation and extract important FACTS about the user.

Facts include:
- Preferences (hobbies, interests, likes/dislikes)
- Experiences (past events, activities)
- Habits (routines, behaviors)
- Emotions (feelings in specific contexts)
- Relationships (family, friends, pets)
- Learning (progress, achievements, knowledge)

Output format: JSON array
[
  {
    "content": "Fact description",
    "category": "preference|experience|habit|emotion|relationship|learning",
    "confidence": 0.0-1.0,
    "entities": ["entity1", "entity2"]
  }
]

Return only the JSON array, no other text.
"""
            
            # Convert conversation to messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.2
            )
            
            import json
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON (might be wrapped in markdown code blocks)
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            facts = result.get("facts", []) if isinstance(result, dict) else result if isinstance(result, list) else []
            
            logger.debug(f"Extracted {len(facts)} facts from conversation")
            return facts
            
        except Exception as e:
            logger.error(f"Error extracting facts with LLM: {e}")
            raise
    
    @staticmethod
    def hash_text(text: str) -> str:
        """Generate hash for text (for caching)"""
        return hashlib.sha256(text.encode()).hexdigest()


# Global OpenAI client instance
openai_client = OpenAIClient()

