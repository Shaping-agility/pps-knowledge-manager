"""
Deep cycle tests for ingestion delete-recreate behavior.
These tests verify that duplicate document processing uses delete-recreate strategy.
"""

import pytest
from pathlib import Path
from src.pps_knowledge_manager.core.knowledge_manager import KnowledgeManager


@pytest.mark.deep_cycle
@pytest.mark.primary
def test_delete_recreate_behavior(ingested_db, knowledge_manager):
    """Test that duplicate document inserts use delete-recreate strategy."""
    # Test file path
    test_file = Path("data/raw/ingest_steel_thread.txt")
    if not test_file.exists():
        pytest.skip(f"Test file not found: {test_file}")

    # Use relative file path for all queries (matches ingestion logic)
    file_path = str(test_file)

    # Get initial counts for this specific document
    storage = knowledge_manager.storage_backends[0]
    initial_docs = storage.get_document_count_by_path(file_path)
    initial_chunks = storage.get_chunk_count_by_document_path(file_path)

    assert (
        initial_docs == 1
    ), f"Should have 1 document for {file_path}, got {initial_docs}"
    assert (
        initial_chunks > 0
    ), f"Should have chunks for {file_path}, got {initial_chunks}"

    # Second ingestion (should delete and recreate)
    result = knowledge_manager.process_file(test_file)
    assert result, "Second ingestion should succeed"

    # Verify document count remains the same (delete + recreate)
    final_docs = storage.get_document_count_by_path(file_path)
    final_chunks = storage.get_chunk_count_by_document_path(file_path)

    assert (
        final_docs == 1
    ), f"Should still have 1 document for {file_path} after delete-recreate, got {final_docs}"
    assert (
        final_chunks == initial_chunks
    ), f"Should have same chunk count for {file_path} after delete-recreate ({initial_chunks} → {final_chunks})"

    # Verify embeddings were created (check a few chunks)
    from src.pps_knowledge_manager.utils.supabase_client import SupabaseConnection

    with SupabaseConnection(use_anon_key=False) as client:
        # Get document ID first
        doc_response = (
            client.table("documents").select("id").eq("file_path", file_path).execute()
        )
        assert doc_response.data, f"Document should exist for {file_path}"
        document_id = doc_response.data[0]["id"]

        # Get chunks for this document
        chunks_response = (
            client.table("chunks").select("*").eq("document_id", document_id).execute()
        )
        assert chunks_response.data, f"Should have chunks for document {document_id}"

        # Check that chunks have embeddings
        for chunk in chunks_response.data[:3]:  # Check first 3 chunks
            assert (
                chunk.get("embedding") is not None
            ), f"Chunk {chunk.get('id')} should have embedding"
            assert isinstance(
                chunk["embedding"], str
            ), f"Embedding should be string format"
            assert chunk["embedding"].startswith("["), f"Embedding should start with ["
            assert chunk["embedding"].endswith("]"), f"Embedding should end with ]"
