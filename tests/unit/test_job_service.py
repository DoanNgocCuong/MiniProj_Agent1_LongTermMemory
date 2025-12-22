"""
Unit tests for Job Service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domains.memory.application.services.job_service import JobService
from app.domains.memory.domain.entities import Job
from app.domains.memory.domain.value_objects import ExtractionRequest


@pytest.fixture
def mock_job_repository():
    """Mock job repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ service."""
    mq = MagicMock()
    mq.publish = MagicMock()
    return mq


@pytest.fixture
def job_service(mock_job_repository):
    """Job service instance with mocked dependencies."""
    return JobService(job_repository=mock_job_repository)


@pytest.mark.asyncio
@patch('app.domains.memory.application.services.job_service.get_rabbitmq_service')
async def test_create_extraction_job(
    mock_get_rabbitmq,
    job_service,
    mock_job_repository,
    mock_rabbitmq,
):
    """Test creating extraction job."""
    # Arrange
    mock_get_rabbitmq.return_value = mock_rabbitmq
    
    request = ExtractionRequest(
        user_id="user_123",
        conversation_id="conv_001",
        conversation=[
            {"role": "user", "content": "I like pizza"},
        ],
        metadata={},
    )
    created_job = Job(
        id=str(uuid4()),
        user_id=request.user_id,
        conversation_id=request.conversation_id,
        status="pending",
    )
    mock_job_repository.create = AsyncMock(return_value=created_job)
    
    # Act
    job = await job_service.create_extraction_job(request)
    
    # Assert
    assert job.id == created_job.id
    assert job.status == "pending"
    mock_job_repository.create.assert_called_once()
    mock_rabbitmq.publish.assert_called_once()


@pytest.mark.asyncio
async def test_get_job_status(job_service, mock_job_repository):
    """Test getting job status."""
    # Arrange
    job_id = str(uuid4())
    job = Job(
        id=job_id,
        user_id="user_123",
        status="completed",
        progress=100,
    )
    mock_job_repository.get_by_id = AsyncMock(return_value=job)
    
    # Act
    result = await job_service.get_job_status(job_id)
    
    # Assert
    assert result.id == job_id
    assert result.status == "completed"
    mock_job_repository.get_by_id.assert_called_once_with(job_id)

