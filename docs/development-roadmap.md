# PPS Knowledge Manager - Development Roadmap

## Overview
This roadmap outlines the iterative development approach for the PPS Knowledge Manager, focusing on learning-driven evolution and test-driven development.

## Iteration 1: Foundation Setup ✅ COMPLETED
**Goal**: Establish local development environment and basic infrastructure

### Completed Tasks
1. **Supabase Local Setup** ✅
   - Installed and configured Supabase Docker container
   - Created initial database schema for knowledge storage
   - Tested basic connectivity and operations
   - Documented setup process

2. **Project Structure Setup** ✅
   - Implemented 3-layer architecture foundation
   - Set up configuration management system
   - Created comprehensive test framework with pytest
   - Established logging and monitoring

3. **Test Infrastructure Refactoring** ✅
   - Simplified architecture to single database approach
   - Implemented script-based test state management (`dropEntities.sql`)
   - Removed complex schema/database isolation logic
   - Achieved clean separation between test and production code

### Success Criteria ✅ ALL COMPLETED
- [x] Supabase container running and accessible
- [x] Basic project structure in place
- [x] All tests passing with simplified architecture
- [x] Configuration system operational
- [x] Test infrastructure with automated reset process
- [x] Health check system operational

### Key Learnings
- **Simplified Architecture**: Single database approach with script-based reset is more maintainable than complex schema isolation
- **Test-Driven Development**: Comprehensive test framework enables rapid iteration and confidence in changes
- **Configuration Management**: Environment-based configuration with dotenv provides flexibility for different environments
- **Stateless Connections**: Creating and closing Supabase connections per operation prevents resource leaks and import-time blocking

## Iteration 2: Basic Vector Ingest (Current)
**Goal**: Implement simple text processing pipeline using standard LangChain splitters

### Tasks
1. **Text Processing Pipeline**
   - Implement basic text file ingestion
   - Integrate LangChain text splitters (TextSplitter or RecursiveCharacterTextSplitter)
   - Build vector embedding generation
   - Store chunks in Supabase vector store

2. **Sample Data Processing**
   - Process sample ideation session transcript
   - Validate chunking quality and relevance
   - Test basic vector search functionality

### Success Criteria
- [x] Can ingest text files and generate chunks using LangChain splitters
- [x] Chunks stored in Supabase with metadata
- [x] Basic vector search returns relevant results
- [x] Sample ideation session fully processed
- [x] Tests are self-contained, do not reset the database per test, and only assert what they are responsible for
- [x] Metadata conventions are flat, canonical, and consistent across ingestion and chunking

### Learning Goals
- Understand LangChain text splitting capabilities and configuration
- Learn vector storage performance characteristics
- Identify metadata requirements for knowledge retrieval
- Establish baseline chunking quality for comparison with semantic approaches

## Iteration 2b: Baseline Hardening ✅ COMPLETED
**Goal**: Solidify vector-ingest foundation by enforcing security, idempotency, and code cleanup before enabling embeddings.

### Completed Tasks
1. **Security Baseline** ✅
   - Enabled Row-Level-Security (RLS) on `documents` and `chunks` tables
   - Added `security.sql` with minimal policies (anon read-only, service_role full access)
2. **Environment Hygiene** ✅
   - Removed Docker exec anon-key retrieval logic
   - Rely exclusively on `.env` variables (`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_ANON_KEY`)
3. **Idempotent Writes** ✅
   - Implemented explicit check-then-insert/update logic for `documents` (`file_path`) and `chunks` (`document_id, chunk_index`)
   - Updated ingestion pipeline to track created vs updated chunks
4. **Code Cleanup** ✅
   - Deleted obsolete `store_embedding()` helper and stale RPC calls
   - Merged embedding persistence into `store_chunk()` interface
5. **Smoke & Retry Tests** ✅
   - Added duplication tests ensuring re-ingest does not duplicate rows
   - Enhanced smoke tests to verify `idx_chunks_embedding` index exists after reset
6. **Deep Cycle Testing** ✅
   - Implemented conditional test execution with `deep_cycle` marker
   - Tests skip by default to preserve manual inspection data
   - Can be enabled via `DEEP_TEST_CYCLE=1` environment variable

### Success Criteria ✅ ALL COMPLETED
- [x] RLS policies active and enforced
- [x] Insertion retries are idempotent
- [x] Docker-specific auth code removed
- [x] All new tests pass
- [x] Deep cycle testing infrastructure operational

## Iteration 3: Richer Ingestion (Current)
**Goal**: Deepen text handling and onboard the first non-TXT format while keeping scope contained.

### Tracks & Tasks
1. **Semantic Chunking (Option A – Sentence Transformers)**
   - Integrate `sentence-transformers` (all-MiniLM-L6-v2) for semantic boundary detection
   - Implement `semantic` splitter alongside existing standard splitter
   - Extend config so each `file_type` can declare `chunking: semantic|standard`

2. **PDF (Text-only) Ingestion**
   - Use `pypdf` to extract page-level text
   - Re-use existing splitter pipeline; attach metadata: `page_number`, `source_type: pdf`
   - Gracefully skip image-only PDFs (emit warning, no failure)

3. **Enrichment Metrics**
   - Detect language with `langdetect` → store `lang` in `documents`
   - Compute `word_count`, `reading_minutes` and persist to metadata

4. **Test & Fixture Updates**
   - Add unit tests for semantic splitter selection via config
   - Add functional tests for PDF ingestion path
   - Register pytest marks in `pytest.ini` (header switched to `[pytest]`)

### Success Criteria
- [ ] Semantic chunking operational and selectable via config
- [ ] PDF files ingested with correct page-level metadata
- [ ] Language + doc-level metrics stored
- [ ] All new tests pass without DB reset per test

### Learning Goals
- Evaluate quality/latency trade-offs of semantic chunking
- Understand PDF text extraction quirks and limitations
- Establish metadata groundwork for future retrieval tuning

---

## Iteration 4: Semantic Search Hardening
*(formerly Iteration 4, renumbered)*
**Goal**: Implement sentence transformers and semantic chunking strategies

### Tasks
1. **Sentence Transformers Integration**
   - Implement sentence transformer models for semantic analysis
   - Create semantic chunking strategies
   - Compare with standard LangChain splitters

2. **Chunking Strategy Evaluation**
   - Test semantic boundary detection
   - Evaluate chunk quality metrics
   - Implement configurable chunking strategies

### Success Criteria
- [ ] Sentence transformer-based chunking operational
- [ ] Multiple chunking strategies available (standard + semantic)
- [ ] Chunk quality metrics implemented
- [ ] Configurable chunking pipeline

### Learning Goals
- Understand semantic chunking approaches and their benefits
- Identify optimal chunking strategies for different content types
- Learn about chunk quality evaluation methods
- Compare performance between standard and semantic approaches

## Iteration 5: Graph Storage Integration
**Goal**: Implement Neo4J integration with PPS Schema extensions

### Tasks
1. **Neo4J Setup**
   - Configure Neo4J Docker container
   - Implement PPS Schema with Person extensions
   - Create graph storage layer

2. **Graph Ingest Pipeline**
   - Build graph ingestion from processed chunks
   - Implement relationship extraction
   - Store metadata in graph structure

### Success Criteria
- [ ] Neo4J container operational with PPS Schema
- [ ] Graph ingestion pipeline functional
- [ ] Relationships properly extracted and stored
- [ ] Graph queries return relevant results

### Learning Goals
- Understand graph storage for knowledge management
- Learn relationship extraction techniques
- Validate PPS Schema design

## Iteration 6: Agent Tool Selection
**Goal**: Implement intelligent tool selection based on knowledge type

### Tasks
1. **Tool Selection Logic**
   - Implement knowledge type detection
   - Create tool selection algorithms
   - Build comparison and contrast capabilities

2. **Agent Integration**
   - Develop agent tools for knowledge access
   - Implement memory management tools
   - Create ingestion by attachment functionality

### Success Criteria
- [ ] Agents can intelligently select knowledge tools
- [ ] Tool selection improves RAG performance
- [ ] Memory management tools operational
- [ ] Attachment ingestion working

### Learning Goals
- Understand optimal tool selection strategies
- Learn about agent memory management patterns
- Identify best practices for agent knowledge integration

## Current Status
- **Current Iteration**: 3 - Embedding Enrichment
- **Previous Iteration**: ✅ 2b - Baseline Hardening (COMPLETED)
- **Next Milestone**: Embedding enrichment – compute and store OpenAI embeddings
- **Current Blocker**: None - Foundation complete and ready for next phase
- **Recent Progress**: 
  - ✅ **Foundation Complete**: All infrastructure operational
  - ✅ **Simplified Architecture**: Removed complex schema/database isolation
  - ✅ **Test Infrastructure**: Automated reset process with `dropEntities.sql`
  - ✅ **Health Monitoring**: Comprehensive health checks implemented
  - ✅ **Configuration System**: Environment-based configuration operational
  - ✅ **Storage Backend**: SupabaseStorageBackend integrated with KnowledgeManager
  - ✅ **All Tests Passing**: 7/7 tests passing with clean architecture

## Architecture Decisions & Patterns

### Test State Management
- **Approach**: Script-based reset using `dropEntities.sql` (run once per test cycle, not per test)
- **Benefits**: Simple, explicit, easy to extend, and high performance
- **Pattern**: Add DROP statements to `dropEntities.sql` for new test entities; tests should not assume a clean DB state except at the start of the cycle

### Database Architecture
- **Approach**: Single database with `