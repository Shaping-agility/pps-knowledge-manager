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

## Knowledge Types & Processing Requirements

### Phase 1 (Current Focus)
- Text files (transcripts) with LDA chunking
- Structured markdown documents from Obsidian vault
- Business and methodology IP as primary content

### Phase 2 (Future Expansion)
- PDF files with source reference preservation
- DOCx files with metadata extraction
- PowerPoint files with slide-level chunking
- Images with OCR and visual content analysis
- Web scraping capabilities
- Hybrid search returning source references

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
- Webhook endpoints for storage requests
- File system monitors
- API endpoints for direct ingestion
- Event-driven architecture for location monitoring

### Chunking Layer
- File type detection and routing
- Configurable chunking strategies (LDA, semantic boundaries, etc.)
- Metadata extraction and enrichment
- Source reference preservation

### Storage Layer
- Multi-backend storage (Supabase, Neo4J)
- Metadata management
- Graph schema extensions (PPS Schema + Person, etc.)
- Vector embedding generation and storage

## Test Infrastructure & State Management

### Simplified Test Architecture
- **Single Database Approach**: All operations use the default Supabase database and `public` schema
- **Script-Based Reset**: Test state management through `dropEntities.sql` script
- **Clean Separation**: Test data management separated from production logic
- **Stateless Connections**: Supabase connections created and closed per operation

### Test Data Management
```sql
-- data/DDL/dropEntities.sql
DROP TABLE IF EXISTS health_test CASCADE;
-- Add more DROP statements as needed for additional test entities
```

### Reset Process
1. Execute `dropEntities.sql` to clear test state
2. Run `rolemanagement.sql` for schema setup
3. Execute `tables.sql` to recreate required tables
4. Run smoke tests to verify setup

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

### Current Stack
- **Supabase**: Primary storage backend (structured + vector storage)
- **Neo4J**: Graph storage backend (planned)
- **OpenAI**: Model provider (planned)
- **LangChain**: Agent framework (planned)
- **Slack**: Primary UI (planned)

### Infrastructure Status
- ✅ **Supabase Local**: Operational with test infrastructure
- ✅ **Test Framework**: Complete with automated reset process
- ✅ **Configuration System**: Operational with environment variable support
- ✅ **Storage Backend**: SupabaseStorageBackend implemented and integrated
- ✅ **Health Checks**: Comprehensive health monitoring implemented

## Success Criteria & Milestones

### Phase 1 Success ✅ COMPLETED
- [x] Local Supabase container operational
- [x] Test infrastructure with automated reset process
- [x] Basic configuration-driven processing
- [x] SupabaseStorageBackend integrated with KnowledgeManager
- [x] Health check system operational
- [x] All tests passing with simplified architecture

### Phase 2 Success (Next)
- [ ] Vector ingest of sample ideation session with LDA chunking
- [ ] n8n chatbot integration for RAG testing
- [ ] Topic analysis with LDA and other algorithms
- [ ] Graph ingest with PPS Schema extensions

### Phase 3 Success
- [ ] Agent tool selection based on knowledge type
- [ ] Hybrid search capabilities
- [ ] Multi-format file processing (PDF, DOCx, PPT)
- [ ] Source reference preservation and retrieval

### Phase 4 Success
- [ ] Advanced RAG strategies (GraphRAG, reranking)
- [ ] Production deployment patterns
- [ ] Performance optimization and scaling 