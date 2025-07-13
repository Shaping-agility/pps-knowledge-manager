"""
Supabase storage backend implementation.
"""

from typing import Any, Dict, List, Optional
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
                # First try to find existing document
                existing = (
                    client.table("documents")
                    .select("id")
                    .eq("file_path", document_data["file_path"])
                    .execute()
                )

                if existing.data:
                    # Document exists, return existing ID
                    return existing.data[0]["id"]
                else:
                    # Document doesn't exist, insert new one
                    response = client.table("documents").insert(document_data).execute()
                    if response.data:
                        return response.data[0]["id"]
                    else:
                        raise Exception("Failed to insert document")
        except Exception as e:
            print(f"Error storing document in Supabase: {e}")
            raise

    def store_chunk(
        self, chunk: Chunk, embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Store a chunk in Supabase and return operation result."""
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

            # Add embedding if provided
            if embedding is not None:
                # Ensure embedding is a list of floats
                if not isinstance(embedding, list) or not all(
                    isinstance(x, float) for x in embedding
                ):
                    raise ValueError("Embedding must be a list of floats.")
                # Convert to string format that PostgreSQL vector type expects
                embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                chunk_data["embedding"] = embedding_str

            with SupabaseConnection(use_anon_key=False) as client:
                # First try to find existing chunk
                existing = (
                    client.table("chunks")
                    .select("id")
                    .eq("document_id", chunk_data["document_id"])
                    .eq("chunk_index", chunk_data["chunk_index"])
                    .execute()
                )

                if existing.data:
                    # Chunk exists, update it
                    response = (
                        client.table("chunks")
                        .update(chunk_data)
                        .eq("id", existing.data[0]["id"])
                        .execute()
                    )
                    return {
                        "success": True,
                        "operation": "updated",
                        "chunk_id": existing.data[0]["id"],
                    }
                else:
                    # Chunk doesn't exist, insert new one
                    response = client.table("chunks").insert(chunk_data).execute()
                    if response.data:
                        return {
                            "success": True,
                            "operation": "created",
                            "chunk_id": response.data[0]["id"],
                        }
                    else:
                        return {
                            "success": False,
                            "operation": "failed",
                            "error": "No data returned",
                        }
        except Exception as e:
            print(f"Error storing chunk in Supabase: {e}")
            return {"success": False, "operation": "error", "error": str(e)}

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
            # Convert to string format that PostgreSQL vector type expects
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            with SupabaseConnection(use_anon_key=False) as client:
                response = (
                    client.table("chunks")
                    .update({"embedding": embedding_str})
                    .eq("id", chunk_id)
                    .execute()
                )
                return response.data is not None
        except Exception as e:
            print(f"Error storing embedding in Supabase: {e}")
            return False

    def similarity_search(
        self, query_embedding: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity via match_chunks RPC."""
        try:
            with SupabaseConnection(use_anon_key=False) as client:
                response = client.rpc(
                    "match_chunks",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": 0.7,
                        "match_count": limit,
                    },
                ).execute()
                return response.data or []
        except Exception as e:
            print(f"Error performing similarity search in Supabase: {e}")
            return []

    def get_client(self):
        """Get the underlying Supabase client for direct access."""
        # Return a new connection context manager instead of a persistent client
        return SupabaseConnection(use_anon_key=False)
