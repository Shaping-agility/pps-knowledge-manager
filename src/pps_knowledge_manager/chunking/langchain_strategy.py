"""
LangChain-based chunking strategies for PPS Knowledge Manager.
"""

from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .base import ChunkingStrategy, Chunk


class LangChainSentenceSplitter(ChunkingStrategy):
    """LangChain-based sentence splitting strategy."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.get("chunk_size", 1000),
            chunk_overlap=config.get("chunk_overlap", 200),
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.supported_extensions = [".txt", ".md"]

    def chunk(self, content: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Chunk content using LangChain RecursiveCharacterTextSplitter."""
        # Split content into chunks
        text_chunks = self.splitter.split_text(content)

        # Convert to Chunk objects
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            # Create clean chunk metadata without duplicating parent fields
            chunk_metadata = {
                "chunk_index": i,
                "chunk_type": "langchain_sentence",
                "chunk_processed_at": datetime.now().isoformat(),
                "chunk_size": len(chunk_text),
            }

            # Add parent metadata fields that are relevant to chunks
            chunk_metadata.update(
                {
                    "filename": metadata.get("filename"),
                    "source_path": metadata.get("file_path"),
                    "file_type": metadata.get("file_type"),
                    "chunking_strategy": metadata.get("chunking_strategy"),
                }
            )

            chunk = Chunk(
                content=chunk_text,
                metadata=chunk_metadata,
                source_path=Path(metadata.get("source_path", "")),
                chunk_id=None,  # Let DB generate UUID
                start_position=content.find(chunk_text),
                end_position=content.find(chunk_text) + len(chunk_text),
            )
            chunks.append(chunk)

        return chunks

    def get_strategy_name(self) -> str:
        """Return the name of this chunking strategy."""
        return "langchain_sentence_splitter"
