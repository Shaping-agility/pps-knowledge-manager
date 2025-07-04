"""
Tests for the foundation components of PPS Knowledge Manager.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.pps_knowledge_manager.config import ConfigManager
from src.pps_knowledge_manager.core.knowledge_manager import KnowledgeManager
from src.pps_knowledge_manager.chunking.base import Chunk, ChunkingStrategy
from src.pps_knowledge_manager.storage.base import StorageBackend


class TestChunkingStrategy(ChunkingStrategy):
    """Test implementation of chunking strategy."""

    def chunk(self, content: str, metadata: dict) -> list[Chunk]:
        return [
            Chunk(
                content=content,
                metadata=metadata,
                source_path=Path(metadata["source_path"]),
                chunk_id="test-chunk-1",
            )
        ]

    def get_strategy_name(self) -> str:
        return "test_strategy"


class TestStorageBackend(StorageBackend):
    """Test implementation of storage backend."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.stored_chunks = []

    def store_chunk(self, chunk: Chunk) -> bool:
        self.stored_chunks.append(chunk)
        return True

    def search(self, query: str, limit: int = 10) -> list[dict]:
        return [{"content": "test result", "score": 0.9}]

    def delete_chunk(self, chunk_id: str) -> bool:
        return True

    def health_check(self) -> bool:
        return True


class TestTrigger:
    """Test implementation of trigger."""

    def __init__(self, config: dict):
        self.config = config
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def is_running(self) -> bool:
        return self.running


def test_config_manager_default_config():
    """Test that ConfigManager loads default config when no file exists."""
    with patch("pathlib.Path.exists", return_value=False):
        config = ConfigManager()
        assert config.get("storage.supabase.enabled") is True
        assert config.get("storage.neo4j.enabled") is False


def test_knowledge_manager_initialization():
    """Test that KnowledgeManager can be initialized."""
    km = KnowledgeManager()
    assert km.config is not None
    assert len(km.triggers) == 0
    assert len(km.storage_backends) == 0


def test_knowledge_manager_add_components():
    """Test adding components to KnowledgeManager."""
    km = KnowledgeManager()

    # Add test components
    strategy = TestChunkingStrategy({})
    backend = TestStorageBackend({})
    trigger = TestTrigger({})

    km.add_chunking_strategy("test", strategy)
    km.add_storage_backend(backend)
    km.add_trigger(trigger)

    assert "test" in km.chunking_strategies
    assert len(km.storage_backends) == 1
    assert len(km.triggers) == 1


def test_knowledge_manager_health_check():
    """Test health check functionality."""
    km = KnowledgeManager()

    # Add test components
    backend = TestStorageBackend({})
    trigger = TestTrigger({})

    km.add_storage_backend(backend)
    km.add_trigger(trigger)

    # Start trigger
    trigger.start()

    health = km.health_check()
    assert health["triggers"] is True
    assert health["storage"] is True


def test_chunk_creation():
    """Test Chunk dataclass creation."""
    chunk = Chunk(
        content="Test content",
        metadata={"source": "test.txt"},
        source_path=Path("test.txt"),
        chunk_id="test-1",
    )

    assert chunk.content == "Test content"
    assert chunk.metadata["source"] == "test.txt"
    assert chunk.chunk_id == "test-1"
