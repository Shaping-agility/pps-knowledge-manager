"""
Deep cycle tests for ingestion idempotency.
These tests reset the database and run full ingestion cycles.
"""

import pytest
from pathlib import Path
from src.pps_knowledge_manager.ingestion.pipeline import IngestionPipeline
from src.pps_knowledge_manager.chunking.langchain_strategy import (
    LangChainSentenceSplitter,
)
from src.pps_knowledge_manager.storage.supabase_backend import SupabaseStorageBackend
from src.pps_knowledge_manager.utils.test_data_manager import SupabaseTestDataManager


@pytest.mark.deep_cycle
def test_duplicate_insert_handled():
    """Test that duplicate document inserts are handled idempotently."""
    # Reset database for this test
    manager = SupabaseTestDataManager()
    assert manager.reset(), "Database reset failed"

    # Create pipeline
    storage_backend = SupabaseStorageBackend({})
    chunking_strategy = LangChainSentenceSplitter({"chunk_size": 500})
    pipeline = IngestionPipeline(storage_backend, chunking_strategy)

    # Test file
    test_file = Path("data/raw/ingest_steel_thread.txt")
    if not test_file.exists():
        pytest.skip(f"Test file not found: {test_file}")

    # First ingestion
    result1 = pipeline.process_file(test_file)
    assert result1["chunks_created"] > 0

    # Second ingestion (should be idempotent)
    result2 = pipeline.process_file(test_file)
    assert result2["chunks_created"] == 0  # No new chunks created
    assert result2["chunks_updated"] > 0  # Existing chunks updated

    # Verify document count didn't increase
    doc_count = storage_backend.get_document_count()
    assert doc_count == 1, f"Should have exactly 1 document, got {doc_count}"
