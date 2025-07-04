"""
Base chunking classes and interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a chunk of processed content."""

    content: str
    metadata: Dict[str, Any]
    source_path: Path
    chunk_id: str
    start_position: Optional[int] = None
    end_position: Optional[int] = None


class ChunkingStrategy(ABC):
    """Base class for chunking strategies."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def chunk(self, content: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Chunk the given content according to the strategy."""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of this chunking strategy."""
        pass


class FileTypeDetector:
    """Detects file types and routes to appropriate chunking strategies."""

    def __init__(self):
        self.strategies = {}

    def register_strategy(self, file_extension: str, strategy: ChunkingStrategy):
        """Register a chunking strategy for a file type."""
        self.strategies[file_extension.lower()] = strategy

    def get_strategy(self, file_path: Path) -> Optional[ChunkingStrategy]:
        """Get the appropriate chunking strategy for a file."""
        extension = file_path.suffix.lower()
        return self.strategies.get(extension)

    def can_process(self, file_path: Path) -> bool:
        """Check if we can process this file type."""
        return file_path.suffix.lower() in self.strategies
