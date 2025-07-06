"""
Test Supabase connection and basic operations.
"""

import pytest
from src.pps_knowledge_manager.utils.supabase_client import (
    get_supabase_client,
    supabase_health_check,
)
from src.pps_knowledge_manager.utils.knowledge_manager_health_check import (
    knowledge_manager_health_check,
)


def test_supabase_connection():
    """Test that we can connect to Supabase and get a client instance."""
    client = get_supabase_client()
    assert client is not None


def test_supabase_health_check():
    """Test Supabase basic connectivity health check."""
    assert supabase_health_check() is True


def test_knowledge_manager_health_check():
    """Test health check using KnowledgeManager's configured storage backend."""
    assert knowledge_manager_health_check() is True
