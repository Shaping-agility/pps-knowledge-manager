"""
Main knowledge manager class that orchestrates the three layers.
"""

from typing import Dict, Any, List
from pathlib import Path

from ..config import ConfigManager
from ..triggers.base import Trigger
from ..chunking.base import ChunkingStrategy, FileTypeDetector, Chunk
from ..storage.base import StorageBackend
from ..storage.supabase_backend import SupabaseStorageBackend


class KnowledgeManager:
    """Main orchestrator for the knowledge management system."""

    def __init__(self, config_path: Path = None):
        self.config = ConfigManager(config_path)
        self.triggers: List[Trigger] = []
        self.chunking_strategies: Dict[str, ChunkingStrategy] = {}
        self.storage_backends: List[StorageBackend] = []
        self.file_detector = FileTypeDetector()

        self._initialize_components()

    def _initialize_components(self):
        """Initialize all components based on configuration."""
        # Initialize storage backends
        self._initialize_storage_backends()

    def _initialize_storage_backends(self):
        """Initialize storage backends based on configuration."""
        # Initialize Supabase backend if enabled
        supabase_config = self.config.get("storage.supabase")
        if supabase_config and supabase_config.get("enabled", False):
            try:
                # Use environment variables for credentials
                import os

                supabase_config["url"] = os.getenv(
                    "SUPABASE_URL", supabase_config.get("url")
                )
                supabase_config["key"] = os.getenv(
                    "SUPABASE_KEY", supabase_config.get("key")
                )

                supabase_backend = SupabaseStorageBackend(supabase_config)
                self.add_storage_backend(supabase_backend)
                print(
                    f"Initialized Supabase storage backend for database: {supabase_config.get('database_name')}"
                )
            except Exception as e:
                print(f"Failed to initialize Supabase storage backend: {e}")

    def add_trigger(self, trigger: Trigger) -> None:
        """Add a trigger to the system."""
        self.triggers.append(trigger)

    def add_chunking_strategy(self, name: str, strategy: ChunkingStrategy) -> None:
        """Add a chunking strategy to the system."""
        self.chunking_strategies[name] = strategy
        # Register with file detector if it has file type associations
        if hasattr(strategy, "supported_extensions"):
            for ext in strategy.supported_extensions:
                self.file_detector.register_strategy(ext, strategy)

    def add_storage_backend(self, backend: StorageBackend) -> None:
        """Add a storage backend to the system."""
        self.storage_backends.append(backend)

    def process_file(self, file_path: Path) -> bool:
        """Process a single file through the pipeline."""
        if not file_path.exists():
            return False

        # Get appropriate chunking strategy
        strategy = self.file_detector.get_strategy(file_path)
        if not strategy:
            return False

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return False

        # Create metadata
        metadata = {
            "source_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix,
            "strategy": strategy.get_strategy_name(),
        }

        # Chunk the content
        chunks = strategy.chunk(content, metadata)

        # Store chunks in all backends
        success = True
        for backend in self.storage_backends:
            for chunk in chunks:
                if not backend.store_chunk(chunk):
                    success = False

        return success

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search across all storage backends."""
        results = []
        for backend in self.storage_backends:
            try:
                backend_results = backend.search(query, limit)
                results.extend(backend_results)
            except Exception as e:
                print(f"Error searching backend {backend.__class__.__name__}: {e}")

        # Sort by relevance (this will be enhanced later)
        return results[:limit]

    def health_check(self) -> Dict[str, bool]:
        """Check health of all components."""
        health = {
            "triggers": all(trigger.is_running() for trigger in self.triggers),
            "storage": all(backend.health_check() for backend in self.storage_backends),
        }
        return health
