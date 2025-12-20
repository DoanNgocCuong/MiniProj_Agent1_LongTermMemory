"""
Unit Tests for FactSearcherService

Tests fact search service with mocked repository, cache, and OpenAI client.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.domains.memory.domain.entities import Fact, SearchResult
from app.domains.memory.application.services.fact_searcher_service import FactSearcherService


@pytest.mark.asyncio
class TestFactSearcherService:
    """Test suite for FactSearcherService"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock fact repository"""
        mock = AsyncMock()
        mock.search_similar = AsyncMock(return_value=[])
        mock.get_related_facts = AsyncMock(return_value=[])
        return mock
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create service instance with mocked dependencies"""
        with patch('app.domains.memory.application.services.fact_searcher_service.openai_client') as mock_openai, \
             patch('app.domains.memory.application.services.fact_searcher_service.cache') as mock_cache:
            
            mock_openai.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
            mock_openai.hash_text = MagicMock(return_value="test-hash")
            
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            
            service = FactSearcherService(fact_repository=mock_repository)
            service.openai_client = mock_openai
            service.cache = mock_cache
            return service
    
    @pytest.mark.asyncio
    async def test_search_facts_cache_hit(self, service, mock_repository, mock_cache):
        """Test search with cache hit"""
        # Setup cache hit
        cached_result = {
            "results": [
                {
                    "fact": {
                        "id": "fact-1",
                        "user_id": "user-1",
                        "content": "Test fact",
                        "category": "preference",
                        "confidence": 0.8,
                        "created_at": datetime.utcnow().isoformat(),
                        "metadata": {}
                    },
                    "score": 0.9,
                    "matched_query": "test query",
                    "related_facts": []
                }
            ]
        }
        service.cache.get = AsyncMock(return_value=cached_result)
        
        # Execute
        results = await service.search_facts(
            user_id="user-1",
            query="test query",
            limit=10
        )
        
        # Assertions
        assert len(results) == 1
        assert results[0].score == 0.9
        mock_repository.search_similar.assert_not_called()  # Should not search if cache hit
    
    @pytest.mark.asyncio
    async def test_search_facts_cache_miss(self, service, mock_repository):
        """Test search with cache miss"""
        # Setup cache miss
        service.cache.get = AsyncMock(return_value=None)
        
        # Setup repository to return facts
        fact = Fact(
            id="fact-1",
            user_id="user-1",
            content="Test fact",
            category="preference",
            confidence=0.8,
            embedding=[0.1] * 1536,
            created_at=datetime.utcnow(),
            metadata={"_similarity_score": 0.85}
        )
        mock_repository.search_similar.return_value = [fact]
        mock_repository.get_related_facts.return_value = []
        
        # Execute
        results = await service.search_facts(
            user_id="user-1",
            query="test query",
            limit=10,
            score_threshold=0.4
        )
        
        # Assertions
        assert len(results) == 1
        mock_repository.search_similar.assert_called_once()
        service.cache.set.assert_called_once()  # Should cache results
    
    @pytest.mark.asyncio
    async def test_search_facts_with_related_facts(self, service, mock_repository):
        """Test search enriches results with related facts"""
        # Setup
        service.cache.get = AsyncMock(return_value=None)
        
        fact = Fact(
            id="fact-1",
            user_id="user-1",
            content="Test fact",
            category="preference",
            confidence=0.8,
            embedding=[0.1] * 1536,
            created_at=datetime.utcnow(),
            metadata={"_similarity_score": 0.85}
        )
        mock_repository.search_similar.return_value = [fact]
        mock_repository.get_related_facts.return_value = ["related-fact-1", "related-fact-2"]
        
        # Execute
        results = await service.search_facts(
            user_id="user-1",
            query="test query",
            limit=10
        )
        
        # Assertions
        assert len(results) == 1
        assert len(results[0].related_facts) == 2
        assert "related-fact-1" in results[0].related_facts
        mock_repository.get_related_facts.assert_called_once_with("fact-1")
    
    @pytest.mark.asyncio
    async def test_search_facts_empty_results(self, service, mock_repository):
        """Test search returns empty list when no results"""
        # Setup
        service.cache.get = AsyncMock(return_value=None)
        mock_repository.search_similar.return_value = []
        
        # Execute
        results = await service.search_facts(
            user_id="user-1",
            query="nonexistent query",
            limit=10
        )
        
        # Assertions
        assert len(results) == 0
        mock_repository.search_similar.assert_called_once()

