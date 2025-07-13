-- Enable Row Level Security on tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

-- Public read access via anon key
CREATE POLICY anon_read_documents ON documents FOR SELECT USING (TRUE);
CREATE POLICY anon_read_chunks ON chunks FOR SELECT USING (TRUE);

-- Allow service_role full access (INSERT, UPDATE, DELETE)
CREATE POLICY service_role_full_access_documents ON documents FOR ALL USING (TRUE);
CREATE POLICY service_role_full_access_chunks ON chunks FOR ALL USING (TRUE); 