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
            document_data = self._prepare_document_data(document_metadata)
            return self._persist_document_with_upsert_logic(document_data)
        except Exception as e:
            print(f"Error storing document in Supabase: {e}")
            raise

    def _prepare_document_data(
        self, document_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare document data for storage."""
        return {
            "title": document_metadata.get("title"),
            "file_path": document_metadata.get("file_path"),
            "file_type": document_metadata.get("file_type"),
            "file_size": document_metadata.get("file_size"),
            "metadata": document_metadata.get("metadata", {}),
            "created_at": "now()",
        }

    def _persist_document_with_upsert_logic(self, document_data: Dict[str, Any]) -> str:
        """Persist document using upsert logic (return existing ID if found, insert if new)."""
        with SupabaseConnection(use_anon_key=False) as client:
            existing_document = self._find_existing_document(
                client, document_data["file_path"]
            )

            if existing_document:
                return existing_document["id"]
            else:
                return self._insert_new_document(client, document_data)

    def _find_existing_document(
        self, client, file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Find existing document by file_path."""
        response = (
            client.table("documents").select("id").eq("file_path", file_path).execute()
        )
        return response.data[0] if response.data else None

    def _insert_new_document(self, client, document_data: Dict[str, Any]) -> str:
        """Insert new document and return its ID."""
        response = client.table("documents").insert(document_data).execute()
        if response.data:
            return response.data[0]["id"]
        else:
            raise Exception("Failed to insert document")

    def store_chunk(
        self, chunk: Chunk, embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Store a chunk in Supabase and return operation result."""
        try:
            chunk_data = self._prepare_chunk_data(chunk, embedding)
            return self._persist_chunk_with_upsert_logic(chunk_data)
        except Exception as e:
            print(f"Error storing chunk in Supabase: {e}")
            return {"success": False, "operation": "error", "error": str(e)}

    def _prepare_chunk_data(
        self, chunk: Chunk, embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Prepare chunk data for storage."""
        chunk_data = {
            **({"id": chunk.chunk_id} if chunk.chunk_id else {}),
            "document_id": chunk.metadata.get("document_id"),
            "content": chunk.content,
            "chunk_index": chunk.metadata.get("chunk_index", 0),
            "start_position": chunk.start_position,
            "end_position": chunk.end_position,
            "chunk_type": chunk.metadata.get("chunk_type", "unknown"),
            "metadata": chunk.metadata,
        }

        if embedding is not None:
            chunk_data["embedding"] = self._format_embedding_for_storage(embedding)

        return chunk_data

    def _format_embedding_for_storage(self, embedding: List[float]) -> str:
        """Format embedding list as PostgreSQL vector string."""
        self._validate_embedding_format(embedding)
        return "[" + ",".join(str(x) for x in embedding) + "]"

    def _validate_embedding_format(self, embedding: List[float]) -> None:
        """Validate that embedding is a list of floats."""
        if not isinstance(embedding, list) or not all(
            isinstance(x, float) for x in embedding
        ):
            raise ValueError("Embedding must be a list of floats.")

    def _persist_chunk_with_upsert_logic(
        self, chunk_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Persist chunk using upsert logic (insert if new, update if exists)."""
        with SupabaseConnection(use_anon_key=False) as client:
            existing_chunk = self._find_existing_chunk(client, chunk_data)

            if existing_chunk:
                return self._update_existing_chunk(client, chunk_data, existing_chunk)
            else:
                return self._insert_new_chunk(client, chunk_data)

    def _find_existing_chunk(
        self, client, chunk_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find existing chunk by document_id and chunk_index."""
        response = (
            client.table("chunks")
            .select("id")
            .eq("document_id", chunk_data["document_id"])
            .eq("chunk_index", chunk_data["chunk_index"])
            .execute()
        )
        return response.data[0] if response.data else None

    def _update_existing_chunk(
        self, client, chunk_data: Dict[str, Any], existing_chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing chunk and return success result."""
        response = (
            client.table("chunks")
            .update(chunk_data)
            .eq("id", existing_chunk["id"])
            .execute()
        )
        return {
            "success": True,
            "operation": "updated",
            "chunk_id": existing_chunk["id"],
        }

    def _insert_new_chunk(self, client, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert new chunk and return success result."""
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
            with SupabaseConnection(use_anon_key=False) as client:
                response = (
                    client.table("chunks")
                    .select("*")
                    .text_search("content", query)
                    .execute()
                )
                return self._apply_limit_to_results(response.data, limit)
        except Exception as e:
            print(f"Error searching chunks in Supabase: {e}")
            return []

    def _apply_limit_to_results(
        self, data: Optional[List[Dict[str, Any]]], limit: int
    ) -> List[Dict[str, Any]]:
        """Apply limit to search results manually since limit() method may not be available."""
        return (data or [])[:limit]

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
            with SupabaseConnection(use_anon_key=False) as client:
                response = client.table("health_test").select("*").limit(1).execute()
                return response is not None
        except Exception as e:
            print(f"Supabase health check failed: {e}")
            return False

    def store_embedding(self, chunk_id: str, embedding: List[float]) -> bool:
        """Store a vector embedding for a chunk."""
        try:
            embedding_str = self._format_embedding_for_storage(embedding)
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
        return SupabaseConnection(use_anon_key=False)
