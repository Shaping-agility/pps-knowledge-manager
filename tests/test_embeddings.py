"""
Tests for embedding functionality.
"""

import pytest
import os
from unittest.mock import Mock, patch
from typing import List
from pathlib import Path

from src.pps_knowledge_manager.utils.embedding_service import EmbeddingService
from src.pps_knowledge_manager.core.knowledge_manager import KnowledgeManager
from src.pps_knowledge_manager.chunking.base import Chunk
from src.pps_knowledge_manager.storage.supabase_backend import SupabaseStorageBackend


class TestEmbeddingService:
    """Test the embedding service functionality."""

    def test_embedding_service_initialization_with_api_key(self):
        """Test embedding service initialization with API key."""
        api_key = "test-api-key"
        service = EmbeddingService(api_key=api_key)
        assert service.api_key == api_key
        assert service.model == "text-embedding-3-small"

    def test_embedding_service_initialization_with_model(self):
        """Test embedding service initialization with custom model."""
        api_key = "test-api-key"
        model = "text-embedding-3-large"
        service = EmbeddingService(api_key=api_key, model=model)
        assert service.model == model

    def test_embedding_service_initialization_without_api_key(self):
        """Test embedding service initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                EmbeddingService(api_key=None)

    @patch("src.pps_knowledge_manager.utils.embedding_service.OpenAI")
    def test_generate_embedding_success(self, mock_openai):
        """Test successful embedding generation."""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]  # 1536 dimensions
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")
        embedding = service.generate_embedding("test text")

        assert len(embedding) == 1536
        assert embedding == [0.1, 0.2, 0.3] * 512
        mock_client.embeddings.create.assert_called_once()

    @patch("src.pps_knowledge_manager.utils.embedding_service.OpenAI")
    def test_generate_embedding_failure(self, mock_openai):
        """Test embedding generation failure."""
        mock_client = Mock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")
        with pytest.raises(Exception, match="Failed to generate embedding"):
            service.generate_embedding("test text")

    @patch("src.pps_knowledge_manager.utils.embedding_service.OpenAI")
    def test_generate_embeddings_batch_success(self, mock_openai):
        """Test successful batch embedding generation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3] * 512),
            Mock(embedding=[0.4, 0.5, 0.6] * 512),
        ]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")
        embeddings = service.generate_embeddings_batch(["text1", "text2"])

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536
        assert len(embeddings[1]) == 1536
        mock_client.embeddings.create.assert_called_once()

    def test_get_embedding_dimension_small_model(self):
        """Test embedding dimension for small model."""
        service = EmbeddingService(api_key="test-key", model="text-embedding-3-small")
        assert service.get_embedding_dimension() == 1536

    def test_get_embedding_dimension_large_model(self):
        """Test embedding dimension for large model."""
        service = EmbeddingService(api_key="test-key", model="text-embedding-3-large")
        assert service.get_embedding_dimension() == 3072

    def test_get_embedding_dimension_unknown_model(self):
        """Test embedding dimension for unknown model defaults to 1536."""
        service = EmbeddingService(api_key="test-key", model="unknown-model")
        assert service.get_embedding_dimension() == 1536


class TestKnowledgeManagerEmbeddings:
    """Test embedding integration with knowledge manager."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service."""
        service = Mock(spec=EmbeddingService)
        service.generate_embedding.return_value = [0.1, 0.2, 0.3] * 512
        return service

    @pytest.fixture
    def knowledge_manager_with_embeddings(self, mock_embedding_service):
        """Create a knowledge manager with embedding service."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            km = KnowledgeManager()
            km.embedding_service = mock_embedding_service
            return km

    def test_knowledge_manager_embedding_service_initialization_with_key(self):
        """Test knowledge manager initializes embedding service when API key is available."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch(
                "src.pps_knowledge_manager.core.knowledge_manager.EmbeddingService"
            ) as mock_service:
                mock_instance = Mock()
                mock_service.return_value = mock_instance

                km = KnowledgeManager()
                assert km.embedding_service is not None
                mock_service.assert_called_once()

    def test_knowledge_manager_embedding_service_initialization_without_key(self):
        """Test knowledge manager doesn't initialize embedding service when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            km = KnowledgeManager()
            assert km.embedding_service is None

    def test_similarity_search_with_embedding_service(
        self, knowledge_manager_with_embeddings, mock_embedding_service
    ):
        """Test similarity search when embedding service is available."""
        # Mock storage backend with similarity search
        mock_backend = Mock(spec=SupabaseStorageBackend)
        mock_backend.similarity_search.return_value = [{"id": "1", "content": "test"}]
        knowledge_manager_with_embeddings.storage_backends = [mock_backend]

        results = knowledge_manager_with_embeddings.similarity_search("test query")

        assert len(results) == 1
        assert results[0]["id"] == "1"
        mock_embedding_service.generate_embedding.assert_called_once_with("test query")
        mock_backend.similarity_search.assert_called_once()

    def test_similarity_search_without_embedding_service(self):
        """Test similarity search when embedding service is not available."""
        km = KnowledgeManager()
        km.embedding_service = None

        results = km.similarity_search("test query")
        assert results == []

    def test_similarity_search_with_embedding_error(
        self, knowledge_manager_with_embeddings, mock_embedding_service
    ):
        """Test similarity search handles embedding generation errors."""
        mock_embedding_service.generate_embedding.side_effect = Exception(
            "Embedding error"
        )

        results = knowledge_manager_with_embeddings.similarity_search("test query")
        assert results == []


class TestSupabaseBackendEmbeddings:
    """Test embedding integration with Supabase backend."""

    @pytest.fixture
    def mock_supabase_connection(self):
        """Create a mock Supabase connection."""
        with patch(
            "src.pps_knowledge_manager.storage.supabase_backend.SupabaseConnection"
        ) as mock_conn:
            mock_client = Mock()
            mock_conn.return_value.__enter__.return_value = mock_client
            yield mock_client

    def test_store_chunk_with_embedding(self, mock_supabase_connection):
        """Test storing chunk with embedding."""
        # Mock response for existing chunk check
        mock_supabase_connection.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
            []
        )

        # Mock response for insert
        mock_supabase_connection.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "test-id"}
        ]

        backend = SupabaseStorageBackend({"url": "test", "key": "test"})
        chunk = Chunk(
            content="test content",
            metadata={"document_id": "doc-1", "chunk_index": 0},
            source_path=Path("test.txt"),
        )
        embedding = [0.1, 0.2, 0.3] * 512

        result = backend.store_chunk(chunk, embedding)

        assert result["success"] is True
        assert result["operation"] == "created"

        # Verify embedding was included in the data
        insert_call = mock_supabase_connection.table.return_value.insert.call_args
        assert "embedding" in insert_call[0][0]

    def test_store_chunk_without_embedding(self, mock_supabase_connection):
        """Test storing chunk without embedding."""
        # Mock response for existing chunk check
        mock_supabase_connection.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
            []
        )

        # Mock response for insert
        mock_supabase_connection.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "test-id"}
        ]

        backend = SupabaseStorageBackend({"url": "test", "key": "test"})
        chunk = Chunk(
            content="test content",
            metadata={"document_id": "doc-1", "chunk_index": 0},
            source_path=Path("test.txt"),
        )

        result = backend.store_chunk(chunk)

        assert result["success"] is True
        assert result["operation"] == "created"

        # Verify embedding was not included in the data
        insert_call = mock_supabase_connection.table.return_value.insert.call_args
        assert "embedding" not in insert_call[0][0]

    def test_store_embedding_success(self, mock_supabase_connection):
        """Test storing embedding for existing chunk."""
        mock_supabase_connection.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"id": "test-id"}
        ]

        backend = SupabaseStorageBackend({"url": "test", "key": "test"})
        embedding = [0.1, 0.2, 0.3] * 512

        result = backend.store_embedding("test-chunk-id", embedding)

        assert result is True
        mock_supabase_connection.table.return_value.update.assert_called_once()

    def test_similarity_search_success(self, mock_supabase_connection):
        """Test similarity search using table query."""
        mock_supabase_connection.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
            {"id": "1", "content": "test"}
        ]

        backend = SupabaseStorageBackend({"url": "test", "key": "test"})
        query_embedding = [0.1, 0.2, 0.3] * 512

        results = backend.similarity_search(query_embedding, limit=5)

        assert len(results) == 1
        assert results[0]["id"] == "1"

        # Verify table query was called
        mock_supabase_connection.table.assert_called_once_with("chunks")
