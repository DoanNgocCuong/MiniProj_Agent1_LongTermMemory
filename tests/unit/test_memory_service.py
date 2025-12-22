"""
Unit tests for Memory Service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.memory.application.services.memory_service import MemoryService
from app.domains.memory.domain.value_objects import SearchQuery, SearchResult
from app.infrastructure.cache.l2_materialized_view import L2MaterializedView


@pytest.fixture
def mock_memory_repository():
    """Mock memory repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_l2_cache():
    """Mock L2 cache."""
    cache = AsyncMock(spec=L2MaterializedView)
    return cache


@pytest.fixture
def mock_l0_cache():
    """Mock L0 cache."""
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    return cache


@pytest.fixture
def mock_l1_cache():
    """Mock L1 cache."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def memory_service(mock_memory_repository, mock_l2_cache):
    """Memory service instance with mocked dependencies."""
    return MemoryService(
        memory_repository=mock_memory_repository,
        l2_cache=mock_l2_cache,
    )


@pytest.mark.asyncio
@patch('app.domains.memory.application.services.memory_service.get_l0_cache')
@patch('app.domains.memory.application.services.memory_service.get_l1_cache')
async def test_search_memories_cache_miss(
    mock_get_l1_cache,
    mock_get_l0_cache,
    memory_service,
    mock_memory_repository,
    mock_l0_cache,
    mock_l1_cache,
):
    """Test search memories with cache miss."""
    # Arrange
    mock_get_l0_cache.return_value = mock_l0_cache
    mock_get_l1_cache.return_value = mock_l1_cache
    
    query = SearchQuery(
        query="test query",
        user_id="user_123",
        limit=10,
        score_threshold=0.4,
    )
    expected_results = [
        SearchResult(
            id="mem_1",
            score=0.9,
            content="Test memory",
            metadata={},
        )
    ]
    mock_memory_repository.search = AsyncMock(return_value=expected_results)
    
    # Act
    results = await memory_service.search_memories(query)
    
    # Assert
    assert len(results) == 1
    assert results[0].id == "mem_1"
    mock_memory_repository.search.assert_called_once_with(query)


@pytest.mark.asyncio
@patch('app.domains.memory.application.services.memory_service.get_l0_cache')
@patch('app.domains.memory.application.services.memory_service.get_l1_cache')
async def test_search_memories_user_favorite_query(
    mock_get_l1_cache,
    mock_get_l0_cache,
    memory_service,
    mock_l2_cache,
    mock_l0_cache,
    mock_l1_cache,
):
    """Test search memories with user favorite query hitting L2 cache."""
    # Arrange
    mock_get_l0_cache.return_value = mock_l0_cache
    mock_get_l1_cache.return_value = mock_l1_cache
    
    query = SearchQuery(
        query="user favorite movies",
        user_id="user_123",
        limit=10,
        score_threshold=0.4,
    )
    l2_data = {
        "movies": ["Movie 1", "Movie 2"],
        "last_updated": "2025-01-01T00:00:00",
    }
    mock_l2_cache.get_user_favorite_summary = AsyncMock(return_value=l2_data)
    
    # Act
    results = await memory_service.search_memories(query)
    
    # Assert
    assert len(results) > 0
    mock_l2_cache.get_user_favorite_summary.assert_called_once_with("user_123")

