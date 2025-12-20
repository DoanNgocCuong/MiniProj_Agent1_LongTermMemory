"""
Unit Tests for FactExtractorService

Tests fact extraction service with mocked repository and OpenAI client.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.domains.memory.domain.entities import Fact
from app.domains.memory.application.services.fact_extractor_service import FactExtractorService


@pytest.mark.asyncio
class TestFactExtractorService:
    """Test suite for FactExtractorService"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock fact repository"""
        mock = AsyncMock()
        mock.create = AsyncMock(side_effect=lambda f: f)  # Return fact as-is
        return mock
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create service instance with mocked repository"""
        with patch('app.domains.memory.application.services.fact_extractor_service.openai_client') as mock_openai:
            mock_openai.extract_facts = AsyncMock(return_value=[
                {
                    "content": "User loves playing tennis",
                    "category": "preference",
                    "confidence": 0.9,
                    "entities": ["tennis"]
                },
                {
                    "content": "User has a cat named Whiskers",
                    "category": "relationship",
                    "confidence": 0.85,
                    "entities": ["cat", "Whiskers"]
                }
            ])
            mock_openai.generate_embeddings_batch = AsyncMock(return_value=[
                [0.1] * 1536,
                [0.2] * 1536
            ])
            service = FactExtractorService(fact_repository=mock_repository)
            service.openai_client = mock_openai
            return service
    
    @pytest.mark.asyncio
    async def test_extract_facts_success(self, service, mock_repository):
        """Test successful fact extraction"""
        # Setup
        conversation = [
            {"role": "user", "content": "I love playing tennis on weekends"},
            {"role": "assistant", "content": "That's great! Do you play competitively?"},
            {"role": "user", "content": "Yes, I have a cat named Whiskers"}
        ]
        
        # Execute
        facts = await service.extract_facts(
            user_id="test-user-1",
            conversation_id="conv-1",
            conversation=conversation,
            metadata={"source": "test"}
        )
        
        # Assertions
        assert len(facts) == 2
        assert all(isinstance(f, Fact) for f in facts)
        assert facts[0].content == "User loves playing tennis"
        assert facts[1].content == "User has a cat named Whiskers"
        assert mock_repository.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_extract_facts_no_facts_extracted(self, service, mock_repository):
        """Test when LLM returns no facts"""
        # Setup
        service.openai_client.extract_facts = AsyncMock(return_value=[])
        conversation = [{"role": "user", "content": "Hello"}]
        
        # Execute
        facts = await service.extract_facts(
            user_id="test-user-1",
            conversation_id="conv-1",
            conversation=conversation
        )
        
        # Assertions
        assert len(facts) == 0
        mock_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_extract_facts_with_repository_error(self, service, mock_repository):
        """Test handling repository errors during fact storage"""
        # Setup
        mock_repository.create.side_effect = [
            Fact(id="fact-1", user_id="user-1", content="Test", category="preference", confidence=0.8),
            Exception("Storage error")
        ]
        service.openai_client.extract_facts = AsyncMock(return_value=[
            {"content": "Fact 1", "category": "preference", "confidence": 0.8, "entities": []},
            {"content": "Fact 2", "category": "preference", "confidence": 0.8, "entities": []}
        ])
        service.openai_client.generate_embeddings_batch = AsyncMock(return_value=[
            [0.1] * 1536,
            [0.2] * 1536
        ])
        
        conversation = [{"role": "user", "content": "Test"}]
        
        # Execute - should continue despite error
        facts = await service.extract_facts(
            user_id="test-user-1",
            conversation_id="conv-1",
            conversation=conversation
        )
        
        # Assertions - one fact should be stored despite error
        assert len(facts) == 1

