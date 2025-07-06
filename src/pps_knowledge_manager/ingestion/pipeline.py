"""
Ingestion pipeline for PPS Knowledge Manager.
"""

from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from ..chunking.base import Chunk, ChunkingStrategy
from ..storage.base import StorageBackend


class IngestionPipeline:
    """Pipeline for ingesting documents and creating chunks."""

    def __init__(
        self, storage_backend: StorageBackend, chunking_strategy: ChunkingStrategy
    ):
        self.storage_backend = storage_backend
        self.chunking_strategy = chunking_strategy

    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a file through the complete ingestion pipeline."""
        # Read file content
        content = self._read_file(file_path)

        # Create document metadata
        document_metadata = self._create_document_metadata(file_path, content)

        # Store document
        document_id = self.storage_backend.store_document(document_metadata)

        # Chunk content
        chunks = self.chunk_content(content, document_metadata)

        # Store chunks
        stored_chunks = []
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
            if self.storage_backend.store_chunk(chunk):
                stored_chunks.append(chunk)

        return {
            "document_id": document_id,
            "filename": file_path.name,
            "chunks_created": len(stored_chunks),
            "total_chunks": len(chunks),
        }

    def chunk_content(self, content: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Chunk content using the configured chunking strategy."""
        return self.chunking_strategy.chunk(content, metadata)

    def _read_file(self, file_path: Path) -> str:
        """Read file content."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _create_document_metadata(
        self, file_path: Path, content: str
    ) -> Dict[str, Any]:
        """Create metadata for document storage."""
        return {
            "title": file_path.name,
            "file_path": str(file_path),
            "file_type": file_path.suffix,
            "file_size": len(content),
            "filename": file_path.name,
            "processed_at": datetime.now().isoformat(),
            "chunking_strategy": self.chunking_strategy.get_strategy_name(),
        }
