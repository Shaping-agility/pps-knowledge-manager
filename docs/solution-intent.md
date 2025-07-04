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
The system will support declarative configuration for storage strategies:

```yaml
# Example configuration
registration:
  source: "documents/ideation_sessions"
  file_types:
    txt:
      chunking: "lda_semantic_boundaries"
      metadata_model: "transcript_default"
      storage:
        vector: "neo4j"
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
- Supabase (structured + vector storage)
- Neo4J (graph + vector storage)
- OpenAI (model provider)
- LangChain (agent framework)
- Slack (primary UI)

## Success Criteria & Milestones

### Phase 1 Success
- [ ] Local Supabase and Neo4J containers operational
- [ ] Vector ingest of sample ideation session with LDA chunking
- [ ] n8n chatbot integration for RAG testing
- [ ] Basic configuration-driven processing

### Phase 2 Success
- [ ] Topic analysis with LDA and other algorithms
- [ ] Graph ingest with PPS Schema extensions
- [ ] Agent tool selection based on knowledge type
- [ ] Hybrid search capabilities

### Phase 3 Success
- [ ] Multi-format file processing (PDF, DOCx, PPT)
- [ ] Source reference preservation and retrieval
- [ ] Advanced RAG strategies (GraphRAG, reranking)
- [ ] Production deployment patterns 