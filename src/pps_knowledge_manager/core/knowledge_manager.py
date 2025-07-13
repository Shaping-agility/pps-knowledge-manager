"""
Main knowledge manager class that orchestrates the three layers.
"""

from typing import Dict, Any, List, Optional, cast
from pathlib import Path
import os

from ..config import ConfigManager
from ..triggers.base import Trigger
from ..chunking.base import ChunkingStrategy, FileTypeDetector, Chunk
from ..storage.base import StorageBackend, VectorStorage
from ..storage.supabase_backend import SupabaseStorageBackend
from ..utils.embedding_service import EmbeddingService


class KnowledgeManager:
    """Main orchestrator for the knowledge management system."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config = ConfigManager(config_path)
        self.triggers: List[Trigger] = []
        self.chunking_strategies: Dict[str, ChunkingStrategy] = {}
        self.storage_backends: List[StorageBackend] = []
        self.file_detector = FileTypeDetector()
        self.embedding_service: Optional[EmbeddingService] = None

        self._initialize_components()

    def _initialize_components(self):
        """Initialize all components based on configuration."""
        # Initialize storage backends
        self._initialize_storage_backends()
        # Initialize embedding service
        self._initialize_embedding_service()
        # Initialize chunking strategies
        self._initialize_chunking_strategies()

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

    def _initialize_embedding_service(self):
        """Initialize embedding service based on configuration."""
        embedding_config = self.config.get("embeddings")
        if embedding_config and embedding_config.get("enabled", False):
            try:
                # Check if OpenAI API key is available
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    print("Warning: OPENAI_API_KEY not set, embedding service disabled")
                    return

                model = embedding_config.get("model", "text-embedding-3-small")
                self.embedding_service = EmbeddingService(api_key=api_key, model=model)
                print(f"Initialized embedding service with model: {model}")
            except Exception as e:
                print(f"Failed to initialize embedding service: {e}")

    def _initialize_chunking_strategies(self):
        """Initialize default chunking strategies."""
        try:
            from ..chunking.langchain_strategy import LangChainSentenceSplitter

            # Register LangChain strategy with default config
            config = {"chunk_size": 1000, "chunk_overlap": 200}
            langchain_strategy = LangChainSentenceSplitter(config)
            self.add_chunking_strategy("langchain_sentence", langchain_strategy)
            print("Initialized LangChain sentence splitting strategy")
        except Exception as e:
            print(f"Failed to initialize chunking strategies: {e}")

    def add_trigger(self, trigger: Trigger) -> None:
        """Add a trigger to the system."""
        self.triggers.append(trigger)

    def add_chunking_strategy(self, name: str, strategy: ChunkingStrategy) -> None:
        """Add a chunking strategy to the system."""
        self.chunking_strategies[name] = strategy
        strategy_any = cast(Any, strategy)
        if (
            hasattr(strategy_any, "supported_extensions")
            and strategy_any.supported_extensions
        ):
            for ext in strategy_any.supported_extensions:
                self.file_detector.register_strategy(ext, strategy)

    def add_storage_backend(self, backend: StorageBackend) -> None:
        """Add a storage backend to the system."""
        self.storage_backends.append(backend)

    def process_file(self, file_path: Path) -> bool:
        """Process a single file through the pipeline."""
        if not file_path.exists():
            return False

        strategy = self._get_chunking_strategy_for_file(file_path)
        if not strategy:
            return False

        content = self._read_file_content(file_path)
        if content is None:
            return False

        metadata = self._create_file_metadata(file_path, strategy)
        chunks = strategy.chunk(content, metadata)

        # Create document first, then store chunks with document_id
        return self._create_document_and_store_chunks(file_path, metadata, chunks)

    def _get_chunking_strategy_for_file(
        self, file_path: Path
    ) -> Optional[ChunkingStrategy]:
        """Get appropriate chunking strategy for the file."""
        return self.file_detector.get_strategy(file_path)

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with error handling."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def _create_file_metadata(
        self, file_path: Path, strategy: ChunkingStrategy
    ) -> Dict[str, Any]:
        """Create metadata for file processing."""
        return {
            "title": file_path.name,
            "file_path": str(file_path),
            "source_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix,
            "strategy": strategy.get_strategy_name(),
        }

    def _create_document_and_store_chunks(
        self, file_path: Path, metadata: Dict[str, Any], chunks: List[Chunk]
    ) -> bool:
        """Create document first, then store chunks with document_id."""
        success = True

        for backend in self.storage_backends:
            # Create document first
            document_id = backend.store_document(metadata)
            if not document_id:
                success = False
                continue

            # Update chunk metadata with document_id
            for chunk in chunks:
                chunk.metadata["document_id"] = document_id

            # Store chunks with embeddings
            for chunk in chunks:
                embedding = self._generate_embedding_for_chunk(chunk)

                if isinstance(backend, SupabaseStorageBackend):
                    result = backend.store_chunk(chunk, embedding)
                    if not result.get("success", False):
                        success = False
                else:
                    if not backend.store_chunk(chunk):
                        success = False

        return success

    def _store_chunks_with_embeddings(self, chunks: List[Chunk]) -> bool:
        """Store chunks in all backends with embeddings if available."""
        success = True
        for backend in self.storage_backends:
            for chunk in chunks:
                embedding = self._generate_embedding_for_chunk(chunk)

                if isinstance(backend, SupabaseStorageBackend):
                    result = backend.store_chunk(chunk, embedding)
                    if not result.get("success", False):
                        success = False
                else:
                    if not backend.store_chunk(chunk):
                        success = False
        return success

    def _generate_embedding_for_chunk(self, chunk: Chunk) -> Optional[List[float]]:
        """Generate embedding for a chunk if embedding service is available."""
        if not self.embedding_service:
            return None

        try:
            return self.embedding_service.generate_embedding(chunk.content)
        except Exception as e:
            print(f"Failed to generate embedding for chunk: {e}")
            return None

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search across all storage backends."""
        results = []
        for backend in self.storage_backends:
            try:
                backend_results = backend.search(query, limit)
                results.extend(backend_results)
            except Exception as e:
                print(f"Error searching backend {backend.__class__.__name__}: {e}")

        return results[:limit]

    def similarity_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        if not self.embedding_service:
            print("Embedding service not available for similarity search")
            return []

        try:
            query_embedding = self.embedding_service.generate_embedding(query)
            return self._search_vector_backends(query_embedding, limit)
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []

    def _search_vector_backends(
        self, query_embedding: List[float], limit: int
    ) -> List[Dict[str, Any]]:
        """Search across vector storage backends."""
        results = []
        for backend in self.storage_backends:
            if isinstance(backend, VectorStorage):
                try:
                    backend_results = backend.similarity_search(query_embedding, limit)
                    results.extend(backend_results)
                except Exception as e:
                    print(
                        f"Error in similarity search for backend {backend.__class__.__name__}: {e}"
                    )
        return results[:limit]

    def health_check(self) -> Dict[str, bool]:
        """Check health of all components."""
        health = {
            "triggers": all(trigger.is_running() for trigger in self.triggers),
            "storage": all(backend.health_check() for backend in self.storage_backends),
        }
        return health
