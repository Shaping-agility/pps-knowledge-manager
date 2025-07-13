"""
Base storage classes and interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
from ..chunking.base import Chunk


class StorageBackend(ABC):
    """Base class for storage backends."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def store_document(self, document_metadata: Dict[str, Any]) -> str:
        """Store document metadata and return document ID."""
        pass

    @abstractmethod
    def store_chunk(self, chunk: Chunk) -> Dict[str, Any]:
        """Store a chunk in the backend and return operation result."""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for chunks in the backend."""
        pass

    @abstractmethod
    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk from the backend."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the storage backend is healthy."""
        pass

    @abstractmethod
    def get_document_count(self) -> int:
        """Get the total number of documents stored."""
        pass

    @abstractmethod
    def get_chunk_count(self) -> int:
        """Get the total number of chunks stored."""
        pass


class VectorStorage(StorageBackend):
    """Base class for vector storage backends."""

    @abstractmethod
    def store_embedding(self, chunk_id: str, embedding: List[float]) -> bool:
        """Store a vector embedding for a chunk."""
        pass

    @abstractmethod
    def similarity_search(
        self, query_embedding: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        pass


class GraphStorage(StorageBackend):
    """Base class for graph storage backends."""

    @abstractmethod
    def create_node(self, node_type: str, properties: Dict[str, Any]) -> str:
        """Create a node in the graph."""
        pass

    @abstractmethod
    def create_relationship(
        self,
        from_node: str,
        to_node: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a relationship between nodes."""
        pass

    @abstractmethod
    def graph_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a graph query."""
        pass
