"""
Tests for ingestion functionality.
"""

import pytest
from pathlib import Path
from src.pps_knowledge_manager.ingestion.pipeline import IngestionPipeline
from src.pps_knowledge_manager.chunking.langchain_strategy import (
    LangChainSentenceSplitter,
)
from src.pps_knowledge_manager.storage.supabase_backend import SupabaseStorageBackend
from src.pps_knowledge_manager.utils.test_data_manager import SupabaseTestDataManager


class TestIngestionPipeline:
    """Test the complete ingestion pipeline."""

    @pytest.fixture
    def test_data_manager(self):
        """Create a test data manager for database setup."""
        return SupabaseTestDataManager()

    @pytest.fixture
    def storage_backend(self):
        """Create a Supabase storage backend."""
        config = {"url": "https://your-project.supabase.co", "key": "your-service-key"}
        return SupabaseStorageBackend(config)

    @pytest.fixture
    def chunking_strategy(self):
        """Create a LangChain chunking strategy."""
        config = {"chunk_size": 500, "chunk_overlap": 100}
        return LangChainSentenceSplitter(config)

    @pytest.fixture
    def ingestion_pipeline(self, storage_backend, chunking_strategy):
        """Create an ingestion pipeline."""
        return IngestionPipeline(storage_backend, chunking_strategy)

    def test_full_ingestion_pipeline(self, test_data_manager, ingestion_pipeline):
        """Test the complete ingestion pipeline with database validation."""
        # Arrange - Reset database to clean state
        test_data_manager.reset()

        # Verify clean state
        initial_doc_count = ingestion_pipeline.storage_backend.get_document_count()
        initial_chunk_count = ingestion_pipeline.storage_backend.get_chunk_count()
        assert initial_doc_count == 0, "Database should start with 0 documents"
        assert initial_chunk_count == 0, "Database should start with 0 chunks"

        # Act - Process the sample file
        sample_file = Path("data/raw/ingest_steel_thread.txt")
        if not sample_file.exists():
            pytest.skip(f"Sample file not found: {sample_file}")

        result = ingestion_pipeline.process_file(sample_file)

        # Assert - Verify pipeline results
        assert result["document_id"] is not None, "Should return a document ID"
        assert (
            result["filename"] == "ingest_steel_thread.txt"
        ), "Should return correct filename"
        assert result["chunks_created"] > 0, "Should create at least one chunk"
        assert (
            result["total_chunks"] == result["chunks_created"]
        ), "All chunks should be stored"

        # Assert - Verify database counts
        final_doc_count = ingestion_pipeline.storage_backend.get_document_count()
        final_chunk_count = ingestion_pipeline.storage_backend.get_chunk_count()

        assert (
            final_doc_count == 1
        ), f"Should have exactly 1 document, got {final_doc_count}"
        assert (
            final_chunk_count == result["chunks_created"]
        ), f"Should have {result['chunks_created']} chunks, got {final_chunk_count}"

        # Verify the document was stored correctly
        assert final_doc_count > initial_doc_count, "Document count should increase"
        assert final_chunk_count > initial_chunk_count, "Chunk count should increase"

    def test_ingestion_pipeline_handles_missing_file(self, ingestion_pipeline):
        """Test that ingestion pipeline handles missing files gracefully."""
        # Arrange
        missing_file = Path("data/raw/nonexistent_file.txt")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ingestion_pipeline.process_file(missing_file)

    def test_ingestion_pipeline_creates_valid_chunks(
        self, test_data_manager, ingestion_pipeline
    ):
        """Test that ingestion creates valid chunk structure."""
        # Arrange - Reset database
        test_data_manager.reset()

        # Create a simple test file
        test_file = Path("data/raw/test_ingestion.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_content = """
        This is the first paragraph of the test document.
        It contains multiple sentences to test chunking.
        
        This is the second paragraph.
        It should be chunked separately from the first.
        
        This is the third paragraph with more content.
        It will help verify that chunking works correctly.
        """

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        try:
            # Act
            print(f"Processing file: {test_file}")
            print(f"File content length: {len(test_content)}")

            # Test chunking separately
            chunks = ingestion_pipeline.chunk_content(
                test_content, {"filename": test_file.name}
            )
            print(f"Chunks created by chunking strategy: {len(chunks)}")

            result = ingestion_pipeline.process_file(test_file)
            print(f"Ingestion result: {result}")

            # Assert
            assert result["chunks_created"] > 0, "Should create chunks"
            assert (
                result["total_chunks"] == result["chunks_created"]
            ), "All chunks should be stored"

            # Verify database state
            doc_count = ingestion_pipeline.storage_backend.get_document_count()
            chunk_count = ingestion_pipeline.storage_backend.get_chunk_count()

            assert doc_count == 1, "Should have one document"
            assert (
                chunk_count == result["chunks_created"]
            ), "Chunk count should match created chunks"

        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
