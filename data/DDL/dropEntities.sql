-- Drop test entities in dependency order
DROP TABLE IF EXISTS health_test CASCADE;

-- Drop indexes first (they depend on tables)
DROP INDEX IF EXISTS idx_chunks_embedding;
DROP INDEX IF EXISTS idx_chunks_metadata_gin;
DROP INDEX IF EXISTS idx_chunks_type;
DROP INDEX IF EXISTS idx_chunks_document_id;
DROP INDEX IF EXISTS idx_documents_metadata_gin;
DROP INDEX IF EXISTS idx_documents_file_path;

-- Drop tables (chunks depends on documents)
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

-- Drop functions that depend on vector extension
DROP FUNCTION IF EXISTS match_chunks(VECTOR, FLOAT, INTEGER);

-- Drop extensions last
DROP EXTENSION IF EXISTS vector; 