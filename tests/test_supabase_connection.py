"""
Test Supabase connection and basic operations.
"""

import pytest
from src.pps_knowledge_manager.utils.supabase_client import (
    get_supabase_client,
    supabase_health_check,
)


def test_supabase_connection():
    """Test that we can connect to Supabase and get a client instance."""
    client = get_supabase_client()
    assert client is not None


def test_supabase_connection_with_database():
    """Test that we can connect to Supabase with a specific database."""
    client = get_supabase_client("pps_km_test")
    assert client is not None


def test_supabase_health_check():
    """Test Supabase health check."""
    assert supabase_health_check() is True
