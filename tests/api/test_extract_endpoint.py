"""
API Tests for Extract Facts Endpoint

Tests the /api/v1/extract_facts endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_extract_request():
    """Sample extract facts request payload"""
    return {
        "user_id": "test-user-1",
        "conversation_id": "conv-1",
        "conversation": [
            {"role": "user", "content": "I love playing tennis"},
            {"role": "assistant", "content": "That's great!"},
            {"role": "user", "content": "I have a cat named Whiskers"}
        ],
        "metadata": {"source": "test"}
    }


class TestExtractEndpoint:
    """Test suite for extract_facts endpoint"""
    
    def test_extract_facts_success(self, client, sample_extract_request):
        """Test successful fact extraction"""
        with patch('app.api.dependencies.get_fact_extractor_service') as mock_service:
            # Mock service response
            from app.domains.memory.domain.entities import Fact
            from datetime import datetime
            
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
            
            # Execute
            response = client.post("/api/v1/extract_facts", json=sample_extract_request)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "facts_count" in data["data"]
            assert len(data["data"]["fact_ids"]) == 1
    
    def test_extract_facts_validation_error(self, client):
        """Test validation error for invalid request"""
        invalid_request = {
            "user_id": "",  # Invalid: empty user_id
            "conversation_id": "conv-1",
            "conversation": []  # Invalid: empty conversation
        }
        
        # Execute
        response = client.post("/api/v1/extract_facts", json=invalid_request)
        
        # Assertions
        assert response.status_code == 422  # Validation error
    
    def test_extract_facts_service_error(self, client, sample_extract_request):
        """Test handling service errors"""
        with patch('app.api.dependencies.get_fact_extractor_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.extract_facts = AsyncMock(side_effect=Exception("Service error"))
            mock_service.return_value = mock_service_instance
            
            # Execute
            response = client.post("/api/v1/extract_facts", json=sample_extract_request)
            
            # Assertions
            assert response.status_code == 500

