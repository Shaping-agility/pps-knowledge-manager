#!/usr/bin/env python3
"""
Test script to ingest the sample file and show metadata structure.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from src.pps_knowledge_manager.ingestion.pipeline import IngestionPipeline
from src.pps_knowledge_manager.chunking.langchain_strategy import (
    LangChainSentenceSplitter,
)
from src.pps_knowledge_manager.storage.supabase_backend import SupabaseStorageBackend
from src.pps_knowledge_manager.utils.test_data_manager import SupabaseTestDataManager

# Load environment variables
load_dotenv()


def main():
    """Test ingestion with sample file."""
    print("Setting up test environment...")

    # Reset database
    test_manager = SupabaseTestDataManager()
    test_manager.reset()

    # Create storage backend and chunking strategy
    storage_config = {
        "url": os.getenv("SUPABASE_URL"),
        "key": os.getenv("SUPABASE_KEY"),
    }
    storage_backend = SupabaseStorageBackend(storage_config)

    chunking_config = {"chunk_size": 500, "chunk_overlap": 100}
    chunking_strategy = LangChainSentenceSplitter(chunking_config)

    # Create ingestion pipeline
    pipeline = IngestionPipeline(storage_backend, chunking_strategy)

    # Process the sample file
    sample_file = Path("data/raw/ingest_steel_thread.txt")
    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return

    print(f"Processing file: {sample_file}")
    result = pipeline.process_file(sample_file)

    print(f"Ingestion result: {result}")

    # Show database counts
    doc_count = storage_backend.get_document_count()
    chunk_count = storage_backend.get_chunk_count()
    print(f"Database state: {doc_count} documents, {chunk_count} chunks")

    # Query and show chunk metadata
    print("\nChunk metadata structure:")
    try:
        with storage_backend.get_client() as client:
            response = client.table("chunks").select("*").limit(1).execute()
            if response.data:
                chunk = response.data[0]
                import json

                print(json.dumps(chunk["metadata"], indent=2))
            else:
                print("No chunks found in database")
    except Exception as e:
        print(f"Error querying chunks: {e}")


if __name__ == "__main__":
    main()
