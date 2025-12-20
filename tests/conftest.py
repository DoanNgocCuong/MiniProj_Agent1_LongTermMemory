"""
Pytest Configuration and Fixtures

Shared fixtures for all tests.
"""

import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
import asyncio

# Import domain entities
from app.domains.memory.domain.entities import Fact
from datetime import datetime


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_fact() -> Fact:
    """Sample fact entity for testing"""
    return Fact(
        id="test-fact-1",
        user_id="test-user-1",
        content="User loves playing tennis on weekends",
        category="preference",
        confidence=0.9,
        entities=["tennis", "weekends"],
        embedding=[0.1] * 1536,  # Mock embedding vector
        created_at=datetime.utcnow(),
        metadata={"conversation_id": "conv-1"}
    )


@pytest.fixture
def sample_facts() -> list[Fact]:
    """Multiple sample facts for testing"""
    return [
        Fact(
            id=f"test-fact-{i}",
            user_id="test-user-1",
            content=f"Sample fact content {i}",
            category="preference",
            confidence=0.8 + (i * 0.02),
            embedding=[0.1 * i] * 1536,
            created_at=datetime.utcnow(),
        )
        for i in range(5)
    ]


@pytest.fixture
def mock_milvus_client():
    """Mock Milvus client"""
    mock = AsyncMock()
    mock.insert = AsyncMock(return_value=True)
    mock.search = AsyncMock(return_value=[])
    mock.delete = AsyncMock(return_value=True)
    mock.delete_by_user_id = AsyncMock(return_value=True)
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    return mock


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client"""
    mock = AsyncMock()
    mock.create_user_if_not_exists = AsyncMock(return_value=True)
    mock.create_fact_node = AsyncMock(return_value=True)
    mock.get_fact_relationships = AsyncMock(return_value=[])
    mock.delete_fact_node = AsyncMock(return_value=True)
    mock.delete_user_data = AsyncMock(return_value=True)
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    return mock


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    mock = AsyncMock()
    mock.fetchrow = AsyncMock(return_value=None)
    mock.fetch = AsyncMock(return_value=[])
    mock.execute = AsyncMock(return_value="OK")
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    return mock


@pytest.fixture
def mock_cache_client():
    """Mock cache client"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    return mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock = AsyncMock()
    mock.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    mock.generate_embeddings_batch = AsyncMock(return_value=[[0.1] * 1536] * 3)
    mock.extract_facts = AsyncMock(return_value=[
        {
            "content": "User likes tennis",
            "category": "preference",
            "confidence": 0.9,
            "entities": ["tennis"]
        }
    ])
    mock.hash_text = MagicMock(return_value="test-hash")
    return mock
