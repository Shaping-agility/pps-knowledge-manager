"""
Global test fixtures for PPS Knowledge Manager.
Provides layered, session-scoped fixtures for clean test architecture.
"""

import pytest
from pathlib import Path
from src.pps_knowledge_manager.utils.test_data_manager import SupabaseTestDataManager
from src.pps_knowledge_manager.ingestion.pipeline import IngestionPipeline
from src.pps_knowledge_manager.chunking.langchain_strategy import (
    LangChainSentenceSplitter,
)
from src.pps_knowledge_manager.core.knowledge_manager import KnowledgeManager


# ── Phase 1: Clean DB ───────────────────────────────────────────────
@pytest.fixture(scope="session")
def fresh_db():
    """Ensure database is reset to clean state once per test session."""
    mgr = SupabaseTestDataManager()
    assert mgr.reset(), "DB reset failed"
    yield  # nothing to return


# ── Phase 2: Baseline ingestion (text only) ─────────────────────────
@pytest.fixture(scope="session")
def ingested_db(fresh_db):
    """Populate DB with sample data once per test session."""
    sample = Path("data/raw/ingest_steel_thread.txt")

    # Create storage backend and chunking strategy
    from src.pps_knowledge_manager.storage.supabase_backend import (
        SupabaseStorageBackend,
    )

    storage_backend = SupabaseStorageBackend({})
    chunking_strategy = LangChainSentenceSplitter({"chunk_size": 500})

    pipeline = IngestionPipeline(storage_backend, chunking_strategy)
    result = pipeline.process_file(sample)
    yield result  # provide ingest stats if needed


# ── Generic helpers ─────────────────────────────────────────────────
@pytest.fixture
def knowledge_manager():
    """Provide a KnowledgeManager instance for tests."""
    return KnowledgeManager()
