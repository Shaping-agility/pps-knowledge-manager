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
        content = self._read_file(file_path)
        document_metadata = self._create_document_metadata(file_path, content)
        document_id = self._store_document(document_metadata)
        chunks = self._create_chunks(content, document_metadata)
        stored_chunks = self._store_chunks(chunks, document_id)
        return self._create_ingestion_result(
            file_path, document_id, stored_chunks, chunks
        )

    def _store_document(self, document_metadata: Dict[str, Any]) -> str:
        """Store document and return its ID."""
        return self.storage_backend.store_document(document_metadata)

    def _create_chunks(
        self, content: str, document_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Create chunks from content using the configured strategy."""
        return self.chunking_strategy.chunk(content, document_metadata)

    def _store_chunks(self, chunks: List[Chunk], document_id: str) -> List[Chunk]:
        """Store chunks and return successfully stored ones."""
        stored_chunks = []
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
            if self.storage_backend.store_chunk(chunk):
                stored_chunks.append(chunk)
        return stored_chunks

    def _create_ingestion_result(
        self,
        file_path: Path,
        document_id: str,
        stored_chunks: List[Chunk],
        total_chunks: List[Chunk],
    ) -> Dict[str, Any]:
        """Create the result summary for the ingestion process."""
        return {
            "document_id": document_id,
            "filename": file_path.name,
            "chunks_created": len(stored_chunks),
            "total_chunks": len(total_chunks),
        }

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
