"""
Unit Tests for FactRepository

Tests repository implementation with mocked infrastructure clients.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.domains.memory.domain.entities import Fact
from app.domains.memory.infrastructure.repositories.fact_repository_impl import FactRepository


class TestFactRepository:
    """Test suite for FactRepository"""
    
    @pytest.fixture
    def repository(self):
        """Create repository instance with mocked dependencies"""
        # Mock all infrastructure clients at module level
        with patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.milvus_client') as mock_milvus, \
             patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.neo4j_client') as mock_neo4j, \
             patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.db') as mock_db:
            
            # Setup mocks
            mock_milvus.insert = AsyncMock(return_value=True)
            mock_milvus.delete = AsyncMock(return_value=True)
            mock_milvus.delete_by_user_id = AsyncMock(return_value=True)
            mock_milvus.search = AsyncMock(return_value=[])
            
            mock_neo4j.create_user_if_not_exists = AsyncMock(return_value=True)
            mock_neo4j.create_fact_node = AsyncMock(return_value=True)
            mock_neo4j.get_fact_relationships = AsyncMock(return_value=[])
            mock_neo4j.delete_fact_node = AsyncMock(return_value=True)
            mock_neo4j.delete_user_data = AsyncMock(return_value=True)
            
            mock_db.execute = AsyncMock(return_value="OK")
            mock_db.fetchrow = AsyncMock(return_value=None)
            mock_db.fetch = AsyncMock(return_value=[])
            
            yield FactRepository()
    
    @pytest.mark.asyncio
    async def test_create_fact_success(self, repository, sample_fact):
        """Test successful fact creation"""
        # Execute
        result = await repository.create(sample_fact)
        
        # Assertions
        assert result.id == sample_fact.id
        assert result.user_id == sample_fact.user_id
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, sample_fact):
        """Test getting fact by ID when found"""
        with patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.db') as mock_db:
            # Setup mock
            mock_db.fetchrow = AsyncMock(return_value={
                "fact_id": sample_fact.id,
                "user_id": sample_fact.user_id,
                "content": sample_fact.content,
                "category": sample_fact.category,
                "confidence": sample_fact.confidence,
                "created_at": sample_fact.created_at,
                "metadata": sample_fact.metadata
            })
            
            # Temporarily replace db in repository
            import app.domains.memory.infrastructure.repositories.fact_repository_impl as repo_module
            original_db = repo_module.db
            repo_module.db = mock_db
            
            try:
                # Execute
                result = await repository.get_by_id(sample_fact.id)
                
                # Assertions
                assert result is not None
                assert result.id == sample_fact.id
                assert result.content == sample_fact.content
            finally:
                repo_module.db = original_db
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test getting fact by ID when not found"""
        with patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.db') as mock_db:
            mock_db.fetchrow = AsyncMock(return_value=None)
            
            import app.domains.memory.infrastructure.repositories.fact_repository_impl as repo_module
            original_db = repo_module.db
            repo_module.db = mock_db
            
            try:
                # Execute
                result = await repository.get_by_id("non-existent-id")
                
                # Assertions
                assert result is None
            finally:
                repo_module.db = original_db
    
    @pytest.mark.asyncio
    async def test_get_by_user_id(self, repository, sample_facts):
        """Test getting facts by user ID"""
        with patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.db') as mock_db:
            mock_db.fetch = AsyncMock(return_value=[
                {
                    "fact_id": fact.id,
                    "user_id": fact.user_id,
                    "content": fact.content,
                    "category": fact.category,
                    "confidence": fact.confidence,
                    "created_at": fact.created_at,
                    "metadata": fact.metadata
                }
                for fact in sample_facts
            ])
            
            import app.domains.memory.infrastructure.repositories.fact_repository_impl as repo_module
            original_db = repo_module.db
            repo_module.db = mock_db
            
            try:
                # Execute
                results = await repository.get_by_user_id("test-user-1", limit=10)
                
                # Assertions
                assert len(results) == len(sample_facts)
                assert all(r.user_id == "test-user-1" for r in results)
            finally:
                repo_module.db = original_db
    
    @pytest.mark.asyncio
    async def test_search_similar(self, repository, sample_facts):
        """Test searching similar facts"""
        with patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.milvus_client') as mock_milvus, \
             patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.db') as mock_db:
            
            query_vector = [0.1] * 1536
            mock_milvus_results = [
                {
                    "fact_id": fact.id,
                    "user_id": fact.user_id,
                    "content": fact.content,
                    "category": fact.category,
                    "confidence": fact.confidence,
                    "created_at": int(datetime.utcnow().timestamp()),
                    "score": 0.8 - (i * 0.1)
                }
                for i, fact in enumerate(sample_facts)
            ]
            mock_milvus.search = AsyncMock(return_value=mock_milvus_results)
            
            mock_db.fetch = AsyncMock(return_value=[
                {
                    "fact_id": fact.id,
                    "user_id": fact.user_id,
                    "content": fact.content,
                    "category": fact.category,
                    "confidence": fact.confidence,
                    "created_at": fact.created_at,
                    "metadata": {}
                }
                for fact in sample_facts
            ])
            
            import app.domains.memory.infrastructure.repositories.fact_repository_impl as repo_module
            original_milvus = repo_module.milvus_client
            original_db = repo_module.db
            repo_module.milvus_client = mock_milvus
            repo_module.db = mock_db
            
            try:
                # Execute
                results = await repository.search_similar(
                    user_id="test-user-1",
                    query_vector=query_vector,
                    top_k=5,
                    score_threshold=0.4
                )
                
                # Assertions
                assert len(results) == len(sample_facts)
            finally:
                repo_module.milvus_client = original_milvus
                repo_module.db = original_db
    
    @pytest.mark.asyncio
    async def test_delete_fact(self, repository):
        """Test deleting a fact"""
        # This will use the mocks from repository fixture
        result = await repository.delete("test-fact-1")
        
        # Assertions
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_related_facts(self, repository):
        """Test getting related facts from Neo4j"""
        with patch('app.domains.memory.infrastructure.repositories.fact_repository_impl.neo4j_client') as mock_neo4j:
            mock_neo4j.get_fact_relationships = AsyncMock(return_value=[
                {"fact_id": "related-fact-1", "relationship_type": "RELATED_TO", "properties": {}},
                {"fact_id": "related-fact-2", "relationship_type": "RELATED_TO", "properties": {}}
            ])
            
            import app.domains.memory.infrastructure.repositories.fact_repository_impl as repo_module
            original_neo4j = repo_module.neo4j_client
            repo_module.neo4j_client = mock_neo4j
            
            try:
                # Execute
                related_ids = await repository.get_related_facts("test-fact-1")
                
                # Assertions
                assert len(related_ids) == 2
                assert "related-fact-1" in related_ids
                assert "related-fact-2" in related_ids
            finally:
                repo_module.neo4j_client = original_neo4j
