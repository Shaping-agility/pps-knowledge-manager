"""
Unit tests for health and connectivity functionality.
"""

import pytest
from src.pps_knowledge_manager.utils.supabase_client import supabase_health_check
from src.pps_knowledge_manager.storage.supabase_backend import SupabaseStorageBackend


@pytest.mark.primary
@pytest.mark.phase_reset
def test_supabase_connectivity():
    """Test basic Supabase connectivity."""
    assert supabase_health_check(), "Supabase connectivity check failed"


@pytest.mark.primary
@pytest.mark.phase_reset
def test_storage_backend_health():
    """Test storage backend health check."""
    config = {"url": "https://your-project.supabase.co", "key": "your-service-key"}
    backend = SupabaseStorageBackend(config)
    assert backend.health_check(), "Storage backend health check failed"


@pytest.mark.coverage
def test_storage_backend_initialization():
    """Test storage backend initialization with various configs."""
    # Test with minimal config
    config = {"url": "https://test.supabase.co", "key": "test-key"}
    backend = SupabaseStorageBackend(config)
    assert backend.url == "https://test.supabase.co"
    assert backend.key == "test-key"


@pytest.mark.coverage
def test_storage_backend_counts_initial():
    """Test that storage backend can handle count operations."""
    config = {"url": "https://your-project.supabase.co", "key": "your-service-key"}
    backend = SupabaseStorageBackend(config)

    # Should not raise exceptions even if tables don't exist
    doc_count = backend.get_document_count()
    chunk_count = backend.get_chunk_count()

    assert isinstance(doc_count, int)
    assert isinstance(chunk_count, int)
    assert doc_count >= 0
    assert chunk_count >= 0
