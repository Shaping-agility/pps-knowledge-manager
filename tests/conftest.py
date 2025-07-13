"""
Global test fixtures for PPS Knowledge Manager.
Provides layered, session-scoped fixtures for clean test architecture.
"""

import pytest
from pathlib import Path
from src.pps_knowledge_manager.utils.test_data_manager import SupabaseTestDataManager
from src.pps_knowledge_manager.core.knowledge_manager import KnowledgeManager


# ── Phase 1: Clean DB ───────────────────────────────────────────────
@pytest.fixture(scope="session")
def fresh_db():
    """Ensure database is reset to clean state once per test session."""
    mgr = SupabaseTestDataManager()
    assert mgr.reset(), "DB reset failed"
    yield  # nothing to return


# ── Phase 2: Baseline ingestion (with embeddings) ─────────────────────────
@pytest.fixture(scope="session")
def ingested_db(fresh_db):
    """Populate DB with sample data once per test session."""
    sample = Path("data/raw/ingest_steel_thread.txt")

    # Create knowledge manager with embedding service
    knowledge_manager = KnowledgeManager()

    # Always process the sample file for deep cycle tests
    # The fresh_db fixture ensures we start with a clean state
    result = knowledge_manager.process_file(sample)
    yield result  # provide ingest stats if needed


# ── Generic helpers ─────────────────────────────────────────────────
@pytest.fixture
def knowledge_manager():
    """Provide a KnowledgeManager instance for tests."""
    return KnowledgeManager()
