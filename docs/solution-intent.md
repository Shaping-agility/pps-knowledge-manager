# PPS Knowledge Manager - Solution Intent

## Vision Statement
A flexible, multi-modal knowledge management system that serves as the cognitive foundation for agentic systems, supporting diverse knowledge ingestion, intelligent chunking, and sophisticated retrieval strategies while maintaining clear separation between triggers, processing, and storage layers. The system will evolve from basic transcript processing to comprehensive multi-format knowledge management with sophisticated configuration-driven processing pipelines.

## Core Principles
1. **Modular Architecture**: Clean separation between triggers, chunking, and storage layers
2. **Multi-Modal Storage**: Support for vector, graph, and structured storage with rich metadata
3. **Configuration-Driven Processing**: Pluggable chunking strategies and storage backends with declarative configuration
4. **Agentic Integration**: Designed for RAG and context management in agent workflows
5. **Iterative Development**: Test-driven approach with learning-driven evolution
6. **Client-Ready Patterns**: Build patterns that can be rapidly deployed for client solutions
7. **Source Preservation**: Maintain references to original sources for "find relevant" queries
8. **Batch Processing**: Optimized for batch operations with real-time capabilities where needed
9. **Simplified Test Management**: Clean test state management using script-based reset approach
10. **Production-Ready Architecture**: Lambda-compatible design patterns for seamless cloud deployment
11. **Robust DDL/Test Infrastructure**: DDL scripts and test data manager support multi-line SQL, inline/full-line comments, and complex schema evolution

## Knowledge Types & Processing Requirements

Below is an evergreen snapshot of the high-level roadmap.  For sprint-level detail (tasks, success criteria, status) **see `docs/development-roadmap.md`.**

| Phase | Theme                              | Status |
|-------|------------------------------------|--------|
| 1     | TXT with standard splitter         | ✅ Completed |
| 2     | Semantic TXT + Markdown            | 🔄 In progress |
| 3     | PDF text ingestion + doc metrics   | ⏭️ Planned |
| 4+    | DOCX / PPTX / OCR images / Hybrid  | 🚧 Future |

---

(Architectural principles, configuration approach, and layer descriptions remain below; they are considered stable and should rarely change.)

## Storage Configuration Approach
The system supports declarative configuration for storage strategies:

```yaml
# Example configuration
registration:
  source: "documents/ideation_sessions"
  file_types:
    txt:
      chunking: "lda_semantic_boundaries"
      metadata_model: "transcript_default"
      storage:
        vector: "supabase"
        graph: "neo4j_with_pps_schema"
        auto_update: true
    pdf:
      chunking: "semantic_sections"
      preserve_source: true
      metadata_model: "document_with_source"
```

## Three-Layer Architecture

### Triggers Layer
- **Development Phase**: Python tests serve as the trigger/UI layer for rapid iteration
- **Production Phase**: Webhook endpoints for storage requests, file system monitors, API endpoints for direct ingestion
- **Event-driven architecture** for location monitoring and real-time processing

### Chunking Layer
- File type detection and routing
- Configurable chunking strategies (LDA, semantic boundaries, etc.)
- Metadata extraction and enrichment
- Source reference preservation
- Lambda-optimized chunking for execution time limits

### Storage Layer
- Multi-backend storage (Supabase, Neo4J)
- Metadata management
- Graph schema extensions (PPS Schema + Person, etc.)
- Vector embedding generation and storage
- Idempotent operations for Lambda retry scenarios
- **Unified Vector Schema** ✅ Implemented – Chunks table now stores both content and vector embedding for direct LangChain/RAG compatibility
- **PII/PIA Checks**: Deferred for now – controlled via configuration flag `require_pii_check` (default: `false`)

## Test Infrastructure & State Management

### Layered Test Architecture ✅ IMPLEMENTED
- **Directory Structure**: Organized into `unit/`, `functional/`, and `deep_cycle/` test categories
- **Session-Scoped Fixtures**: Heavy operations (DB reset, ingestion) run once per test session
- **Incremental Count Strategy**: Tests validate count increments rather than absolute database state
- **Order-Independent Execution**: Tests can run in any order or parallel without dependencies
- **Intent-Based Marking**: Clear separation between `primary`, `coverage`, and `deep_cycle` tests

### Test Categories & Phases
- **Primary Tests** (`@pytest.mark.primary`): Core functional behavior - quick smoke tests
- **Coverage Tests** (`@pytest.mark.coverage`): Additional edge-case coverage
- **Deep Cycle Tests** (`@pytest.mark.deep_cycle`): Tests that reset DB or run >10s
- **Phase Marks**: `phase_reset`, `phase_ingest`, `phase_retrieval` for test categorization

### Fixture Architecture
```python
# tests/conftest.py - Global fixtures
@pytest.fixture(scope="session")
def fresh_db():
    """Ensure database is reset to clean state once per test session."""
    
@pytest.fixture(scope="session") 
def ingested_db(fresh_db):
    """Populate DB with sample data once per test session."""
```

### Data Isolation Strategy
- **Baseline Capture**: Each test captures initial document and chunk counts before operations
- **Incremental Validation**: Tests verify that counts increment by expected amounts
- **Shared Database State**: Tests run against shared database, enabling realistic scenarios
- **Idempotent Handling**: Tests gracefully handle duplicate file ingestion (0 chunks created)

### Test Execution Patterns
- **Quick Smoke**: `pytest -m primary -q` (seconds)
- **Full Functional**: `pytest -m "primary or coverage" -q` (no deep reset)
- **Deep Cycle**: `pytest -m deep_cycle -q` (nightly)
- **Complete Suite**: `pytest -q` (all tests)

### Test Data Management
```sql
-- data/DDL/dropEntities.sql
-- Drop test entities in dependency order
DROP TABLE IF EXISTS health_test CASCADE;
DROP INDEX IF EXISTS idx_chunks_embedding;
DROP INDEX IF EXISTS idx_chunks_metadata_gin;
DROP INDEX IF EXISTS idx_chunks_type;
DROP INDEX IF EXISTS idx_chunks_document_id;
DROP INDEX IF EXISTS idx_documents_metadata_gin;
DROP INDEX IF EXISTS idx_documents_file_path;
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP FUNCTION IF EXISTS match_chunks(VECTOR, FLOAT, INTEGER);
DROP EXTENSION IF EXISTS vector;
```

### Reset Process
1. Execute `dropEntities.sql` to clear test state
2. Run `rolemanagement.sql` for schema setup
3. Execute `tables.sql` to recreate required tables
4. Run `vector_search.sql` for RPC functions
5. Execute `security.sql` for RLS policies
6. Run smoke tests to verify setup

### DDL/Schema Notes
- DDL scripts can use both full-line and inline comments (`-- comment`)
- Multi-line SQL statements are supported
- Test data manager parses and executes statements robustly, ensuring reliable test cycles
- Vector extension and RPC functions are properly managed in dependency order

## Metadata Handling & Chunking Patterns
- **Canonical Metadata Structure**: All ingestion and chunking operations use a flat, consistent metadata structure (e.g., `file_path`, `filename`, `file_type`, `processed_at`, `chunking_strategy`).
- **No Nested or Remapped Fields**: Chunking strategies extend the parent metadata with chunk-specific fields (e.g., `chunk_index`, `chunk_type`, `chunk_processed_at`, `chunk_size`) but do not introduce new field names or nested metadata.
- **Test Patterns**: Tests are written to be self-contained, assert only what they are responsible for, and do not make unnecessary assumptions about global database state.

## Production-Ready Architecture Patterns

### Lambda-Ready Design Principles
- **Stateless Operations**: All operations designed to work with Lambda's stateless execution model
- **Idempotent Storage** ✅ Implemented – Storage operations handle Lambda retries gracefully with explicit check-then-insert/update logic
- **Connection Efficiency**: Stateless connections prevent resource leaks in Lambda environment
- **Execution Time Optimization**: Chunking strategies respect Lambda's 15-minute execution limit
- **Parallelism Support**: Architecture supports high-concurrency Lambda deployments

### Connection Management Strategy
- **REST API Pattern**: Primary choice for business logic operations (Supabase client)
- **Direct PostgreSQL**: Secondary choice for administrative tasks (DDL, test management)
- **Stateless Connections**: Context managers ensure proper resource cleanup
- **No Connection Pooling**: Lambda-appropriate pattern with fresh connections per invocation

### Storage Backend Selection
- **Supabase REST API**: Optimal for Lambda deployment due to HTTP-based stateless nature
- **Built-in Retry Logic**: Handles transient failures automatically
- **Rate Limiting**: Built-in protection against overwhelming the database
- **Vector Operations**: Native support for similarity search and embeddings
- **Unified Table for RAG**: Chunks table stores both content and embedding for direct LangChain compatibility

### Development-to-Production Transition
- **Current Environment**: Local Docker containers with test-driven development
- **Production Target**: AWS Lambda with Supabase cloud deployment
- **Architecture Continuity**: Same patterns work in both environments
- **Incremental Evolution**: Gradual transition without architectural changes

## RAG Strategy Evolution
1. **Traditional Naive RAG**: Basic vector similarity search
2. **Hybrid RAG**: Vector + full-text/keyword search
3. **GraphRAG**: Leveraging graph relationships for context
4. **Reranking**: Sophisticated result ranking and filtering

## Technical Stack & Deployment

### Development Environment
- Python virtual environment
- Local Docker containers (Neo4J, Supabase)
- Test-driven development with pytest
- Local sandbox for rapid iteration
- Tests as primary trigger mechanism

### Current Stack
- **Supabase**: Primary storage backend (structured + vector storage)
- **Neo4J**: Graph storage backend (planned)
- **OpenAI**: Model provider (planned)
- **LangChain**: Agent framework (planned)
- **Slack**: Primary UI (planned)

### Production Stack (Future)
- **AWS Lambda**: Serverless compute for processing and storage operations
- **Supabase Cloud**: Production database with enhanced features
- **API Gateway**: REST API endpoints for external integrations
- **S3**: File storage for large documents and assets
- **CloudWatch**: Monitoring and observability

### Infrastructure Status
- ✅ **Supabase Local**: Operational with test infrastructure
- ✅ **Test Framework**: Complete with automated reset process and deep cycle testing
- ✅ **Configuration System**: Operational with environment variable support
- ✅ **Storage Backend**: SupabaseStorageBackend implemented and integrated
- ✅ **Health Checks**: Comprehensive health monitoring implemented
- ✅ **Lambda-Ready Architecture**: Stateless patterns implemented for cloud deployment
- ✅ **Robust DDL/Test Infrastructure**: DDL/test manager supports complex SQL and comments
- ✅ **Security Baseline**: RLS policies and environment hygiene implemented
- ✅ **Idempotent Operations**: Storage operations handle retries gracefully 