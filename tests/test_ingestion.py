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
        return self.getStorageBackend()

    @pytest.fixture
    def chunking_strategy(self):
        """Create a LangChain chunking strategy."""
        return self.getChunkingStrategy()

    @pytest.fixture
    def ingestion_pipeline(self, storage_backend, chunking_strategy):
        """Create an ingestion pipeline."""
        return IngestionPipeline(storage_backend, chunking_strategy)

    def test_full_ingestion_pipeline(self, test_data_manager, ingestion_pipeline):
        """Test the complete ingestion pipeline with database validation."""
        # Arrange
        sample_file = self.getSampleFile()

        # Act
        result = ingestion_pipeline.process_file(sample_file)

        # Assert
        self._validatePipelineResults(result)
        self._validateDatabaseCounts(ingestion_pipeline, result)

    def test_ingestion_pipeline_handles_missing_file(self, ingestion_pipeline):
        """Test that ingestion pipeline handles missing files gracefully."""
        # Arrange
        missing_file = self.getMissingFile()

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ingestion_pipeline.process_file(missing_file)

    def test_ingestion_pipeline_creates_valid_chunks(
        self, test_data_manager, ingestion_pipeline
    ):
        """Test that ingestion creates valid chunk structure."""
        # Arrange
        test_file = self.createTestFile()

        try:
            # Act
            result = ingestion_pipeline.process_file(test_file)

            # Assert
            self._validateChunkCreation(result)
            self._validateDatabaseState(ingestion_pipeline, result)

        finally:
            self._cleanupTestFile(test_file)

    # Helper methods
    def getStorageBackend(self):
        """Get configured storage backend."""
        config = {"url": "https://your-project.supabase.co", "key": "your-service-key"}
        return SupabaseStorageBackend(config)

    def getChunkingStrategy(self):
        """Get configured chunking strategy."""
        config = {"chunk_size": 500, "chunk_overlap": 100}
        return LangChainSentenceSplitter(config)

    def getSampleFile(self):
        """Get the sample file for testing."""
        sample_file = Path("data/raw/ingest_steel_thread.txt")
        if not sample_file.exists():
            pytest.skip(f"Sample file not found: {sample_file}")
        return sample_file

    def getMissingFile(self):
        """Get a non-existent file path."""
        return Path("data/raw/nonexistent_file.txt")

    def createTestFile(self):
        """Create a temporary test file."""
        test_file = Path("data/raw/test_ingestion.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_content = self.getTestFileContent()

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        return test_file

    def getTestFileContent(self):
        """Get content for the test file."""
        return """
        This is the first paragraph of the test document.
        It contains multiple sentences to test chunking.
        
        This is the second paragraph.
        It should be chunked separately from the first.
        
        This is the third paragraph with more content.
        It will help verify that chunking works correctly.
        """

    def _validatePipelineResults(self, result):
        """Validate the results from the ingestion pipeline."""
        assert result["document_id"] is not None, "Should return a document ID"
        assert (
            result["filename"] == "ingest_steel_thread.txt"
        ), "Should return correct filename"
        assert result["chunks_created"] > 0, "Should create at least one chunk"
        assert (
            result["total_chunks"] == result["chunks_created"]
        ), "All chunks should be stored"

    def _validateDatabaseCounts(self, ingestion_pipeline, result):
        """Validate the database counts after ingestion."""
        final_doc_count = ingestion_pipeline.storage_backend.get_document_count()
        final_chunk_count = ingestion_pipeline.storage_backend.get_chunk_count()

        assert (
            final_doc_count == 1
        ), f"Should have exactly 1 document, got {final_doc_count}"
        assert (
            final_chunk_count == result["chunks_created"]
        ), f"Should have {result['chunks_created']} chunks, got {final_chunk_count}"

    def _validateChunkCreation(self, result):
        """Validate that chunks were created successfully."""
        assert result["chunks_created"] > 0, "Should create chunks"
        assert (
            result["total_chunks"] == result["chunks_created"]
        ), "All chunks should be stored"

    def _validateDatabaseState(self, ingestion_pipeline, result):
        """Validate the final database state."""
        doc_count = ingestion_pipeline.storage_backend.get_document_count()
        chunk_count = ingestion_pipeline.storage_backend.get_chunk_count()

        # Focus on what we're actually testing - that chunks were created and stored
        assert doc_count > 0, "Should have at least one document"
        assert (
            chunk_count >= result["chunks_created"]
        ), "Chunk count should include created chunks"

    def _cleanupTestFile(self, test_file):
        """Clean up the temporary test file."""
        if test_file.exists():
            test_file.unlink()
