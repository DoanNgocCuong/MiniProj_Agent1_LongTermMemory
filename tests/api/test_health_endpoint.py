"""
API Tests for Health Check Endpoints

Tests the /api/v1/health endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test suite for health check endpoints"""
    
    def test_health_check_success(self, client):
        """Test basic health check endpoint"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
        
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    
    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe"""
        response = client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        
        # Verify timestamp is valid
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    
    def test_readiness_probe_success(self, client):
        """Test Kubernetes readiness probe - success case"""
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data
        assert "checks" in data
        
        # Verify all checks are present
        checks = data["checks"]
        assert "database" in checks
        assert "milvus" in checks
        assert "neo4j" in checks
        assert "redis" in checks
        
        # Verify all checks pass (currently mocked as True)
        assert all(checks.values())
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "PIKA Memory API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"

