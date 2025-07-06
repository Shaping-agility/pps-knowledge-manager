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

    def store_document(self, document_metadata: Dict[str, Any]) -> str:
        """Store document metadata in Supabase and return document ID."""
        try:
            document_data = {
                "title": document_metadata.get("title"),
                "file_path": document_metadata.get("file_path"),
                "file_type": document_metadata.get("file_type"),
                "file_size": document_metadata.get("file_size"),
                "metadata": document_metadata.get("metadata", {}),
                "created_at": "now()",
            }

            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("documents").insert(document_data).execute()
                if response.data:
                    return response.data[0]["id"]
                else:
                    raise Exception("Failed to insert document")
        except Exception as e:
            print(f"Error storing document in Supabase: {e}")
            raise

    def store_chunk(self, chunk: Chunk) -> bool:
        """Store a chunk in Supabase."""
        try:
            # Store in chunks table - match the actual schema
            chunk_data = {
                # Only include id if chunk.chunk_id is not None
                **({"id": chunk.chunk_id} if chunk.chunk_id else {}),
                "document_id": chunk.metadata.get("document_id"),
                "content": chunk.content,
                "chunk_index": chunk.metadata.get("chunk_index", 0),
                "start_position": chunk.start_position,
                "end_position": chunk.end_position,
                "chunk_type": chunk.metadata.get("chunk_type", "unknown"),
                "metadata": chunk.metadata,
            }

            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("chunks").insert(chunk_data).execute()
                return response.data is not None
        except Exception as e:
            print(f"Error storing chunk in Supabase: {e}")
            return False

    def get_document_count(self) -> int:
        """Get the total number of documents stored."""
        try:
            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("documents").select("*").execute()
                return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0

    def get_chunk_count(self) -> int:
        """Get the total number of chunks stored."""
        try:
            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("chunks").select("*").execute()
                return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error getting chunk count: {e}")
            return 0

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for chunks using full-text search."""
        try:
            # Use full-text search on content
            with SupabaseConnection(use_anon_key=False) as client:
                response = (
                    client.table("chunks")
                    .select("*")
                    .text_search("content", query)
                    .execute()
                )

                # Apply limit manually since limit() method may not be available
                data = response.data or []
                return data[:limit]
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
