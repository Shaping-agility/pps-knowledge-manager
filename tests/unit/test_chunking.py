"""
Tests for chunking functionality.
"""

import pytest
from pathlib import Path
from src.pps_knowledge_manager.chunking.langchain_strategy import (
    LangChainSentenceSplitter,
)


class TestLangChainChunking:
    """Test LangChain-based chunking strategies."""

    def test_langchain_sentence_splitter_creates_chunks(self):
        """Test that LangChain sentence splitter creates chunks from text."""
        # Arrange
        config = self.getSplitterConfig()
        splitter = LangChainSentenceSplitter(config)
        test_content = self.getSplitterTestContent()
        metadata = self.getTestMetadata()

        # Act
        chunks = splitter.chunk(test_content, metadata)

        # Assert
        assert len(chunks) > 0, "Should create at least one chunk"

        # Verify chunk structure
        self._validate_chunk_structure(chunks)

    def test_langchain_sentence_splitter_respects_chunk_size(self):
        """Test that chunks respect the configured size limits."""
        # Arrange
        config = self.getSmallChunkConfig()
        splitter = LangChainSentenceSplitter(config)
        test_content = self.getLongTestContent()
        metadata = self.getTestMetadata()

        # Act
        chunks = splitter.chunk(test_content, metadata)

        # Assert
        assert len(chunks) > 1, "Should create multiple chunks for long content"
        self._validate_chunk_sizes(chunks)

    def test_langchain_sentence_splitter_preserves_metadata(self):
        """Test that chunking preserves and extends metadata correctly."""
        # Arrange
        config = self.getSplitterConfig()
        splitter = LangChainSentenceSplitter(config)
        test_content = self.getSimpleTestContent()
        original_metadata = self.getExtendedTestMetadata()

        # Act
        chunks = splitter.chunk(test_content, original_metadata)

        # Assert
        assert len(chunks) > 0, "Should create chunks"
        self._validate_metadata_preservation(chunks, original_metadata)

    # Helper methods
    def getSplitterConfig(self):
        """Get standard splitter configuration."""
        return {"chunk_size": 100, "chunk_overlap": 20}

    def getSmallChunkConfig(self):
        """Get configuration for small chunk testing."""
        return {"chunk_size": 50, "chunk_overlap": 10}

    def getSplitterTestContent(self):
        """Get test content for basic chunking."""
        return """
        This is the first sentence. This is the second sentence. 
        This is the third sentence which is longer than the others.
        This is the fourth sentence. This is the fifth sentence.
        """

    def getLongTestContent(self):
        """Get longer test content for size testing."""
        return "This is a test sentence. " * 10

    def getSimpleTestContent(self):
        """Get simple test content for metadata testing."""
        return "This is a test sentence. This is another test sentence."

    def getTestMetadata(self):
        """Get basic test metadata."""
        return {"filename": "test.txt", "file_path": "/test/path/test.txt"}

    def getExtendedTestMetadata(self):
        """Get extended test metadata with custom fields."""
        return {
            "filename": "test.txt",
            "file_path": "/test/path/test.txt",
            "custom_field": "custom_value",
        }

    def _validate_chunk_structure(self, chunks):
        """Validate the structure of created chunks."""
        for i, chunk in enumerate(chunks):
            assert chunk.content is not None, f"Chunk {i} should have content"
            assert len(chunk.content) > 0, f"Chunk {i} should not be empty"
            assert (
                chunk.metadata["chunk_index"] == i
            ), f"Chunk {i} should have correct index"
            assert (
                chunk.metadata["chunk_type"] == "langchain_sentence"
            ), f"Chunk {i} should have correct type"
            assert (
                chunk.metadata["filename"] == "test.txt"
            ), f"Chunk {i} should preserve filename"

    def _validate_chunk_sizes(self, chunks):
        """Validate that chunks respect size limits."""
        for chunk in chunks:
            assert (
                len(chunk.content) <= 100
            ), f"Chunk should not exceed reasonable size: {len(chunk.content)}"

    def _validate_metadata_preservation(self, chunks, original_metadata):
        """Validate that metadata is preserved and extended correctly."""
        for chunk in chunks:
            # Original metadata should be preserved
            assert chunk.metadata["filename"] == "test.txt"
            assert chunk.metadata["file_path"] == "/test/path/test.txt"
            assert chunk.metadata["custom_field"] == "custom_value"

            # New metadata should be added
            assert "chunk_index" in chunk.metadata
            assert "chunk_type" in chunk.metadata
            assert "chunk_processed_at" in chunk.metadata
            assert "chunk_size" in chunk.metadata
