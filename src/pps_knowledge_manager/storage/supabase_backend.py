"""
Supabase storage backend implementation.
"""

from typing import Any, Dict, List
from .base import StorageBackend, VectorStorage
from ..chunking.base import Chunk
from ..utils.supabase_client import SupabaseConnection


class SupabaseStorageBackend(VectorStorage):
    """Supabase storage backend for knowledge chunks."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url")
        self.key = config.get("key")
        # No client initialization - connections are stateless

    def store_chunk(self, chunk: Chunk) -> bool:
        """Store a chunk in Supabase."""
        try:
            # Store in chunks table
            chunk_data = {
                "id": chunk.chunk_id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "source_path": chunk.metadata.get("source_path", ""),
                "chunk_type": chunk.metadata.get("strategy", "unknown"),
                "created_at": chunk.metadata.get("created_at"),
            }

            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("chunks").insert(chunk_data).execute()
                return response.data is not None
        except Exception as e:
            print(f"Error storing chunk in Supabase: {e}")
            return False

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for chunks using full-text search."""
        try:
            # Use full-text search on content
            with SupabaseConnection(use_anon_key=False) as client:
                response = (
                    client.table("chunks")
                    .select("*")
                    .text_search("content", query)
                    .limit(limit)
                    .execute()
                )

                return response.data or []
        except Exception as e:
            print(f"Error searching chunks in Supabase: {e}")
            return []

    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk from Supabase."""
        try:
            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("chunks").delete().eq("id", chunk_id).execute()
                return response.data is not None
        except Exception as e:
            print(f"Error deleting chunk from Supabase: {e}")
            return False

    def health_check(self) -> bool:
        """Check if Supabase storage is healthy."""
        try:
            # Try to query the health_test table in the test schema
            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("health_test").select("*").limit(1).execute()
                return response is not None
        except Exception as e:
            print(f"Supabase health check failed: {e}")
            return False

    def store_embedding(self, chunk_id: str, embedding: List[float]) -> bool:
        """Store a vector embedding for a chunk."""
        try:
            # Store in embeddings table
            embedding_data = {
                "chunk_id": chunk_id,
                "embedding": embedding,
                "created_at": "now()",
            }

            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("embeddings").insert(embedding_data).execute()
                return response.data is not None
        except Exception as e:
            print(f"Error storing embedding in Supabase: {e}")
            return False

    def similarity_search(
        self, query_embedding: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        try:
            # Use vector similarity search
            with SupabaseConnection(use_anon_key=False) as client:
                response = client.rpc(
                    "match_embeddings",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": 0.7,
                        "match_count": limit,
                    },
                ).execute()

                return response.data or []
        except Exception as e:
            print(f"Error in vector similarity search: {e}")
            return []

    def get_client(self):
        """Get the underlying Supabase client for direct access."""
        # Return a new connection context manager instead of a persistent client
        return SupabaseConnection(use_anon_key=False)
