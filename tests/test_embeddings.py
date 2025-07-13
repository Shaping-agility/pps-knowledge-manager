"""
NOTE: Mocks are not permitted in this codebase without explicit approval from the project owner.

Integration tests for embedding functionality using the real database and embedding logic.
"""

import os
import pytest
from pathlib import Path
from src.pps_knowledge_manager.utils.test_data_manager import SupabaseTestDataManager
from src.pps_knowledge_manager.core.knowledge_manager import KnowledgeManager
from src.pps_knowledge_manager.chunking.base import Chunk
from src.pps_knowledge_manager.utils.embedding_service import EmbeddingService


@pytest.fixture(scope="module", autouse=True)
def reset_database():
    manager = SupabaseTestDataManager()
    assert manager.reset(), "Database reset failed"


@pytest.fixture
def knowledge_manager():
    return KnowledgeManager()


@pytest.fixture
def embedding_service():
    api_key = os.getenv("OPENAI_API_KEY")
    assert api_key, "OPENAI_API_KEY must be set for embedding tests."
    return EmbeddingService(api_key=api_key)


def test_embedding_string_format_conversion():
    """Test that embedding list is correctly converted to PostgreSQL vector string format."""
    # Test embedding conversion logic
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    assert embedding_str == "[0.1,0.2,0.3,0.4,0.5]"
    assert len(embedding_str) > 0
    assert embedding_str.startswith("[")
    assert embedding_str.endswith("]")


def test_embedding_service_generation(embedding_service):
    """Test that embedding service can generate embeddings without database operations."""
    text = "This is a simple test text for embedding generation."
    embedding = embedding_service.generate_embedding(text)

    # Verify embedding format
    assert isinstance(embedding, list)
    assert len(embedding) == embedding_service.get_embedding_dimension()
    assert all(isinstance(x, float) for x in embedding)

    # Test the string conversion
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
    assert embedding_str.startswith("[")
    assert embedding_str.endswith("]")
    assert len(embedding_str) > 0


def test_minimal_embedding_storage(knowledge_manager, embedding_service):
    """Minimal test to verify embedding storage without database reset."""
    # Create a document first
    doc_metadata = {
        "title": "Minimal Test Doc",
        "file_path": "minimal_test.txt",
        "file_type": "txt",
        "file_size": 50,
        "metadata": {"source": "minimal-test"},
    }
    doc_id = knowledge_manager.storage_backends[0].store_document(doc_metadata)

    # Create a simple chunk
    chunk_content = "Minimal test chunk for embedding storage."
    chunk = Chunk(
        content=chunk_content,
        metadata={"document_id": doc_id, "chunk_index": 999},  # Use unique index
        source_path=Path("minimal_test.txt"),
        start_position=0,
        end_position=len(chunk_content),
    )

    # Generate embedding
    embedding = embedding_service.generate_embedding(chunk_content)

    # Store chunk with embedding
    result = knowledge_manager.storage_backends[0].store_chunk(chunk, embedding)

    # Verify storage was successful
    assert result["success"] is True
    assert "chunk_id" in result

    print(f"Successfully stored chunk with ID: {result['chunk_id']}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"Embedding string format: {embedding[:3]}...")  # Show first 3 values


def test_embedding_generation_and_storage(knowledge_manager, embedding_service):
    # Create a fake document and chunk
    doc_metadata = {
        "title": "Test Doc",
        "file_path": "test.txt",
        "file_type": "txt",
        "file_size": 20,
        "metadata": {"source": "unit-test"},
    }
    doc_id = knowledge_manager.storage_backends[0].store_document(doc_metadata)
    chunk_content = "This is a test chunk for embedding."
    chunk = Chunk(
        content=chunk_content,
        metadata={"document_id": doc_id, "chunk_index": 0},
        source_path=Path("test.txt"),
        start_position=0,
        end_position=len(chunk_content),
    )
    embedding = embedding_service.generate_embedding(chunk_content)

    # Debug: Check embedding format
    print(f"DEBUG: Embedding type: {type(embedding)}")
    print(f"DEBUG: Embedding length: {len(embedding)}")
    print(f"DEBUG: First 3 values: {embedding[:3]}")
    print(f"DEBUG: Is list: {isinstance(embedding, list)}")
    print(f"DEBUG: All floats: {all(isinstance(x, float) for x in embedding)}")

    result = knowledge_manager.storage_backends[0].store_chunk(chunk, embedding)
    assert result["success"] is True
    # Check that the embedding is stored in the DB
    backend = knowledge_manager.storage_backends[0]
    with backend.get_client() as client:
        db_chunk = (
            client.table("chunks")
            .select("*")
            .eq("id", result["chunk_id"])
            .execute()
            .data[0]
        )
        print(f"DEBUG: DB embedding type: {type(db_chunk['embedding'])}")
        print(f"DEBUG: DB embedding length: {len(db_chunk['embedding'])}")
        print(f"DEBUG: DB embedding first 10 chars: {str(db_chunk['embedding'])[:10]}")

        assert db_chunk["embedding"] is not None
        # The embedding is stored as a Postgres vector and retrieved as a string
        assert isinstance(db_chunk["embedding"], str)
        assert db_chunk["embedding"].startswith("[")
        assert db_chunk["embedding"].endswith("]")


def test_similarity_search_returns_expected_chunk(knowledge_manager, embedding_service):
    # Use the same content as above to ensure a high similarity
    query = "This is a test chunk for embedding."
    results = knowledge_manager.similarity_search(query, limit=3)
    assert results, "No results returned from similarity search"
    # The top result should have high similarity
    top = results[0]
    assert "similarity" in top
    assert top["similarity"] > 0.8
    assert query.lower()[:10] in top["content"].lower()
