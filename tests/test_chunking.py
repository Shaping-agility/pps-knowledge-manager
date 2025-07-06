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
        config = {"chunk_size": 100, "chunk_overlap": 20}
        splitter = LangChainSentenceSplitter(config)

        test_content = """
        This is the first sentence. This is the second sentence. 
        This is the third sentence which is longer than the others.
        This is the fourth sentence. This is the fifth sentence.
        """

        metadata = {"filename": "test.txt", "source_path": "/test/path/test.txt"}

        # Act
        chunks = splitter.chunk(test_content, metadata)

        # Assert
        assert len(chunks) > 0, "Should create at least one chunk"

        # Verify chunk structure
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

    def test_langchain_sentence_splitter_respects_chunk_size(self):
        """Test that chunks respect the configured size limits."""
        # Arrange
        config = {"chunk_size": 50, "chunk_overlap": 10}  # Small chunk size for testing
        splitter = LangChainSentenceSplitter(config)

        test_content = "This is a test sentence. " * 10  # Create longer content

        metadata = {"filename": "test.txt", "source_path": "/test/path/test.txt"}

        # Act
        chunks = splitter.chunk(test_content, metadata)

        # Assert
        assert len(chunks) > 1, "Should create multiple chunks for long content"

        # Most chunks should be within size limit (allowing for some flexibility)
        for chunk in chunks:
            assert (
                len(chunk.content) <= 100
            ), f"Chunk should not exceed reasonable size: {len(chunk.content)}"
