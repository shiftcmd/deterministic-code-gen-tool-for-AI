-- Supabase Knowledge Assistant Database Schema
-- This schema creates tables for storing documents and their embeddings for the knowledge assistant

-- Enable the pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table for storing the actual document content
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    document_type TEXT DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Full text search
    content_tsvector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
);

-- Document embeddings table for vector similarity search
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimensions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_content_tsvector ON documents USING gin(content_tsvector);
CREATE INDEX IF NOT EXISTS idx_document_embeddings_document_id ON document_embeddings(document_id);

-- Create HNSW index for vector similarity search (requires pgvector)
CREATE INDEX IF NOT EXISTS idx_document_embeddings_embedding ON document_embeddings USING hnsw (embedding vector_cosine_ops);

-- Function to search for similar documents using vector similarity
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id int,
    title text,
    content text,
    document_type text,
    metadata jsonb,
    created_at timestamptz,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        d.id,
        d.title,
        d.content,
        d.document_type,
        d.metadata,
        d.created_at,
        1 - (de.embedding <=> query_embedding) as similarity
    FROM documents d
    JOIN document_embeddings de ON d.id = de.document_id
    WHERE 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Function to search documents using full text search (fallback when no embeddings)
CREATE OR REPLACE FUNCTION search_documents_fulltext(
    search_query text,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id int,
    title text,
    content text,
    document_type text,
    metadata jsonb,
    created_at timestamptz,
    rank float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        d.id,
        d.title,
        d.content,
        d.document_type,
        d.metadata,
        d.created_at,
        ts_rank(d.content_tsvector, plainto_tsquery('english', search_query)) as rank
    FROM documents d
    WHERE d.content_tsvector @@ plainto_tsquery('english', search_query)
    ORDER BY ts_rank(d.content_tsvector, plainto_tsquery('english', search_query)) DESC
    LIMIT match_count;
$$;

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
    total_documents int,
    total_embeddings int,
    document_types json
)
LANGUAGE sql STABLE
AS $$
    SELECT
        (SELECT COUNT(*)::int FROM documents) as total_documents,
        (SELECT COUNT(*)::int FROM document_embeddings) as total_embeddings,
        (SELECT json_agg(doc_type_stats) FROM (
            SELECT document_type, COUNT(*) as count
            FROM documents
            GROUP BY document_type
        ) as doc_type_stats) as document_types;
$$;

-- Trigger to update updated_at timestamp on documents
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample documents for testing (optional)
INSERT INTO documents (title, content, document_type, metadata) VALUES
    ('Welcome', 'Welcome to the Supabase Knowledge Assistant! This system helps you store and retrieve information using vector similarity search.', 'documentation', '{"tags": ["welcome", "introduction"]}'),
    ('Vector Search', 'Vector search uses embeddings to find semantically similar content. It converts text into high-dimensional vectors and uses cosine similarity to find matches.', 'technical', '{"tags": ["vector", "search", "embeddings"]}'),
    ('Database Schema', 'The knowledge assistant uses two main tables: documents for storing content and document_embeddings for storing vector representations.', 'documentation', '{"tags": ["database", "schema", "architecture"]}')
ON CONFLICT DO NOTHING;

-- Row Level Security (RLS) policies
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY;

-- Allow service role to access all data
CREATE POLICY "Service role can access all documents" ON documents FOR ALL TO service_role USING (true);
CREATE POLICY "Service role can access all embeddings" ON document_embeddings FOR ALL TO service_role USING (true);

-- Allow authenticated users to read documents
CREATE POLICY "Authenticated users can read documents" ON documents FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read embeddings" ON document_embeddings FOR SELECT TO authenticated USING (true);

-- Grant necessary permissions
GRANT ALL ON documents TO service_role;
GRANT ALL ON document_embeddings TO service_role;
GRANT USAGE ON SEQUENCE documents_id_seq TO service_role;
GRANT USAGE ON SEQUENCE document_embeddings_id_seq TO service_role;

GRANT SELECT ON documents TO authenticated;
GRANT SELECT ON document_embeddings TO authenticated;

-- Comments for documentation
COMMENT ON TABLE documents IS 'Stores document content with metadata for the knowledge assistant';
COMMENT ON TABLE document_embeddings IS 'Stores vector embeddings for semantic similarity search';
COMMENT ON FUNCTION search_documents IS 'Searches for similar documents using vector similarity';
COMMENT ON FUNCTION search_documents_fulltext IS 'Searches documents using PostgreSQL full-text search';
COMMENT ON FUNCTION get_document_stats IS 'Returns statistics about the document collection';
