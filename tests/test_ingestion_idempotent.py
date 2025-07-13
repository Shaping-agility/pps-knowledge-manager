"""
Test idempotent ingestion behavior.
"""

import os
import pytest
from pathlib import Path
from src.pps_knowledge_manager.core.knowledge_manager import KnowledgeManager
from src.pps_knowledge_manager.chunking.langchain_strategy import (
    LangChainSentenceSplitter,
)
from src.pps_knowledge_manager.storage.supabase_backend import SupabaseStorageBackend
from src.pps_knowledge_manager.ingestion.pipeline import IngestionPipeline


def deep_cycle_required():
    """Check if deep cycle tests should be run."""
    return os.getenv("DEEP_TEST_CYCLE") == "1"


@pytest.mark.deep_cycle
@pytest.mark.skipif(
    not deep_cycle_required(), reason="Set DEEP_TEST_CYCLE=1 to run deep cycle tests"
)
class TestIdempotentIngestion:
    """Test that re-ingesting the same file doesn't create duplicates."""

    def setup_method(self):
        """Reset database before each test."""
        from src.pps_knowledge_manager.utils.test_data_manager import (
            SupabaseTestDataManager,
        )

        tdm = SupabaseTestDataManager()
        tdm.reset()

    def test_duplicate_ingestion_does_not_create_duplicates(self):
        """Test that ingesting the same file twice doesn't create duplicate rows."""
        # Create a simple test file
        test_content = "This is a test document. It has multiple sentences. We will ingest it twice."
        test_file = Path("test_document.txt")

        try:
            # Write test content
            with open(test_file, "w") as f:
                f.write(test_content)

            # Setup knowledge manager
            config = {
                "storage": {
                    "backend": "supabase",
                    "url": "http://localhost:54321",
                    "key": "test_key",
                },
                "chunking": {
                    "strategy": "langchain",
                    "chunk_size": 50,
                    "chunk_overlap": 10,
                },
            }

            storage_backend = SupabaseStorageBackend(config["storage"])
            chunking_strategy = LangChainSentenceSplitter(config["chunking"])
            pipeline = IngestionPipeline(storage_backend, chunking_strategy)

            # First ingestion
            result1 = pipeline.process_file(test_file)
            initial_chunk_count = result1["chunks_created"]

            # Second ingestion of the same file
            result2 = pipeline.process_file(test_file)
            second_chunk_count = result2["chunks_created"]

            # Verify no new chunks were created
            assert (
                second_chunk_count == 0
            ), f"Expected 0 new chunks, got {second_chunk_count}"

            # Verify total chunk count hasn't increased
            total_chunks = storage_backend.get_chunk_count()
            assert (
                total_chunks == initial_chunk_count
            ), f"Expected {initial_chunk_count} total chunks, got {total_chunks}"

        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()

    def test_different_file_paths_create_separate_documents(self):
        """Test that files with different paths create separate documents even with same content."""
        test_content = "This is a test document with identical content."

        # Create two files with same content but different paths
        test_file1 = Path("test_document_1.txt")
        test_file2 = Path("test_document_2.txt")

        try:
            # Write identical content to both files
            with open(test_file1, "w") as f:
                f.write(test_content)
            with open(test_file2, "w") as f:
                f.write(test_content)

            # Setup knowledge manager
            config = {
                "storage": {
                    "backend": "supabase",
                    "url": "http://localhost:54321",
                    "key": "test_key",
                },
                "chunking": {
                    "strategy": "langchain",
                    "chunk_size": 50,
                    "chunk_overlap": 10,
                },
            }

            storage_backend = SupabaseStorageBackend(config["storage"])
            chunking_strategy = LangChainSentenceSplitter(config["chunking"])
            pipeline = IngestionPipeline(storage_backend, chunking_strategy)

            # Ingest both files
            result1 = pipeline.process_file(test_file1)
            result2 = pipeline.process_file(test_file2)

            # Verify both created chunks
            assert result1["chunks_created"] > 0, "First file should create chunks"
            assert result2["chunks_created"] > 0, "Second file should create chunks"

            # Verify total chunk count is sum of both
            total_chunks = storage_backend.get_chunk_count()
            expected_total = result1["chunks_created"] + result2["chunks_created"]
            assert (
                total_chunks == expected_total
            ), f"Expected {expected_total} total chunks, got {total_chunks}"

        finally:
            # Cleanup
            for test_file in [test_file1, test_file2]:
                if test_file.exists():
                    test_file.unlink()
