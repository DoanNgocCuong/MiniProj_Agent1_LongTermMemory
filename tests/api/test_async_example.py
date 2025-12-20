"""
Ví dụ Test API với httpx.AsyncClient

File này minh họa cách test API với async client thực sự.
Chỉ sử dụng khi cần test async behavior hoặc lifespan events.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app.main import app
from app.domains.memory.domain.entities import Fact


@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
class TestAsyncClientExample:
    """Ví dụ test với AsyncClient"""
    
    async def test_extract_facts_with_async_client(self, async_client):
        """Ví dụ test extract facts với async client"""
        with patch('app.api.dependencies.get_fact_extractor_service') as mock_service:
            # Setup mock
            mock_service_instance = AsyncMock()
            mock_service_instance.extract_facts = AsyncMock(return_value=[
                Fact(
                    id="fact-1",
                    user_id="test-user-1",
                    content="User loves playing tennis",
                    category="preference",
                    confidence=0.9,
                    created_at=datetime.utcnow()
                )
            ])
            mock_service.return_value = mock_service_instance
            
            # Execute với async client
            response = await async_client.post(
                "/api/v1/extract_facts",
                json={
                    "user_id": "test-user-1",
                    "conversation_id": "conv-1",
                    "conversation": [
                        {"role": "user", "content": "I love tennis"}
                    ]
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["facts_count"] == 1
    
    async def test_search_facts_with_async_client(self, async_client):
        """Ví dụ test search facts với async client"""
        from app.domains.memory.domain.entities import SearchResult
        
        with patch('app.api.dependencies.get_fact_searcher_service') as mock_service:
            # Setup mock
            fact = Fact(
                id="fact-1",
                user_id="test-user-1",
                content="User loves playing tennis",
                category="preference",
                confidence=0.9,
                created_at=datetime.utcnow()
            )
            
            result = SearchResult(
                fact=fact,
                score=0.85,
                matched_query="tennis",
                related_facts=[]
            )
            
            mock_service_instance = AsyncMock()
            mock_service_instance.search_facts = AsyncMock(return_value=[result])
            mock_service.return_value = mock_service_instance
            
            # Execute
            response = await async_client.post(
                "/api/v1/search_facts",
                json={
                    "user_id": "test-user-1",
                    "query": "tennis",
                    "limit": 10,
                    "score_threshold": 0.4
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]["results"]) == 1

