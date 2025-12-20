"""
API Tests for Search Facts Endpoint

Tests the /api/v1/search_facts endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app.main import app
from app.domains.memory.domain.entities import Fact, SearchResult


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_search_request():
    """Sample search facts request payload"""
    return {
        "user_id": "test-user-1",
        "query": "user favorite activities",
        "limit": 10,
        "score_threshold": 0.4
    }


class TestSearchEndpoint:
    """Test suite for search_facts endpoint"""
    
    def test_search_facts_success(self, client, sample_search_request):
        """Test successful fact search"""
        with patch('app.api.dependencies.get_fact_searcher_service') as mock_service:
            # Mock service response
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
                matched_query="user favorite activities",
                related_facts=[]
            )
            
            mock_service_instance = AsyncMock()
            mock_service_instance.search_facts = AsyncMock(return_value=[result])
            mock_service.return_value = mock_service_instance
            
            # Execute
            response = client.post("/api/v1/search_facts", json=sample_search_request)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "results_count" in data["data"]
            assert len(data["data"]["results"]) == 1
            assert data["data"]["results"][0]["score"] == 0.85
    
    def test_search_facts_validation_error(self, client):
        """Test validation error for invalid request"""
        invalid_request = {
            "user_id": "test-user-1",
            "query": "",  # Invalid: empty query
            "limit": 0  # Invalid: limit must be >= 1
        }
        
        # Execute
        response = client.post("/api/v1/search_facts", json=invalid_request)
        
        # Assertions
        assert response.status_code == 422  # Validation error
    
    def test_search_facts_empty_results(self, client, sample_search_request):
        """Test search with no results"""
        with patch('app.api.dependencies.get_fact_searcher_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.search_facts = AsyncMock(return_value=[])
            mock_service.return_value = mock_service_instance
            
            # Execute
            response = client.post("/api/v1/search_facts", json=sample_search_request)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["results_count"] == 0

