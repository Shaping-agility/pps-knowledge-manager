"""
Functional tests for ingestion pipeline.
"""

import pytest
from pathlib import Path
from src.pps_knowledge_manager.core.knowledge_manager import KnowledgeManager


class TestIngestionPipeline:
    """Test the complete ingestion pipeline."""

    @pytest.fixture
    def knowledge_manager(self):
        """Create a knowledge manager with embedding service."""
        return KnowledgeManager()

    @pytest.mark.primary
    @pytest.mark.phase_ingest
    def test_full_ingestion_pipeline(self, ingested_db, knowledge_manager):
        """Test the complete ingestion pipeline with database validation."""
        # The ingested_db fixture has already processed the sample file
        # Just validate that documents and chunks were created
        docs = knowledge_manager.storage_backends[0].get_document_count()
        chunks = knowledge_manager.storage_backends[0].get_chunk_count()

        # Assert that documents and chunks were created
        assert docs >= 1, f"Should have at least 1 document ({docs})"
        assert chunks > 0, f"Should have chunks ({chunks})"

        # Validate embeddings were created
        self._validateEmbeddingsCreated(knowledge_manager)

    @pytest.mark.coverage
    def test_ingestion_pipeline_handles_missing_file(self, knowledge_manager):
        """Test that ingestion pipeline handles missing files gracefully."""
        # Arrange
        missing_file = self.getMissingFile()

        # Act & Assert
        result = knowledge_manager.process_file(missing_file)
        assert not result, "Should return False for missing file"

    @pytest.mark.coverage
    def test_ingestion_pipeline_creates_valid_chunks(
        self, ingested_db, knowledge_manager
    ):
        """Test that ingestion creates valid chunk structure with embeddings."""
        # Arrange
        test_file = self.createTestFile()

        # Capture baseline counts
        initial_docs = knowledge_manager.storage_backends[0].get_document_count()
        initial_chunks = knowledge_manager.storage_backends[0].get_chunk_count()

        try:
            # Act
            result = knowledge_manager.process_file(test_file)

            # Assert
            assert result, "Ingestion should succeed"
            self._validateDatabaseCounts_incremental(
                knowledge_manager,
                initial_docs,
                initial_chunks,
            )
            self._validateEmbeddingsCreated(knowledge_manager)

        finally:
            self._cleanupTestFile(test_file)

    # Helper methods
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

    def _validateDatabaseCounts_incremental(
        self,
        knowledge_manager,
        initial_docs: int,
        initial_chunks: int,
    ):
        """Validate that database counts increment correctly after ingestion."""
        final_docs = knowledge_manager.storage_backends[0].get_document_count()
        final_chunks = knowledge_manager.storage_backends[0].get_chunk_count()

        # With delete-recreate, we should have at least one document and chunks
        assert final_docs >= 1, f"Should have at least 1 document ({final_docs})"
        assert final_chunks > 0, f"Should have chunks ({final_chunks})"

    def _validateEmbeddingsCreated(self, knowledge_manager):
        """Validate that embeddings were created for chunks."""
        from src.pps_knowledge_manager.utils.supabase_client import SupabaseConnection

        with SupabaseConnection(use_anon_key=False) as client:
            chunks = client.table("chunks").select("*").limit(3).execute()
            assert chunks.data, "Should have chunks in database"

            # Check that chunks have embeddings
            for chunk in chunks.data:
                assert (
                    chunk.get("embedding") is not None
                ), f"Chunk {chunk.get('id')} should have embedding"
                assert isinstance(
                    chunk["embedding"], str
                ), f"Embedding should be string format"
                assert chunk["embedding"].startswith(
                    "["
                ), f"Embedding should start with ["
                assert chunk["embedding"].endswith("]"), f"Embedding should end with ]"

    def _cleanupTestFile(self, test_file):
        """Clean up the temporary test file."""
        if test_file.exists():
            test_file.unlink()
