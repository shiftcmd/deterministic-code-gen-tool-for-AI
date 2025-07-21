-- Add vector search RPC functions for existing project tables
-- Run this in your Supabase SQL Editor to add the missing vector search functions

-- Enable the pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Function to search crawled_pages using vector similarity
CREATE OR REPLACE FUNCTION match_crawled_pages(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    similarity_threshold float DEFAULT 0.7,
    filter jsonb DEFAULT '{}'::jsonb,
    source_filter text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    url text,
    content text,
    metadata jsonb,
    source_id text,
    created_at timestamptz,
    chunk_number int,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cp.id,
        cp.url,
        cp.content,
        cp.metadata,
        cp.source_id,
        cp.created_at,
        cp.chunk_number,
        1 - (cp.embedding <=> query_embedding) AS similarity
    FROM crawled_pages cp
    WHERE 
        (cp.embedding IS NOT NULL) AND
        (1 - (cp.embedding <=> query_embedding)) > similarity_threshold AND
        (source_filter IS NULL OR cp.source_id = source_filter)
    ORDER BY cp.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to search code_examples using vector similarity
CREATE OR REPLACE FUNCTION match_code_examples(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    similarity_threshold float DEFAULT 0.7,
    filter jsonb DEFAULT '{}'::jsonb,
    source_filter text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    url text,
    content text,
    summary text,
    metadata jsonb,
    source_id text,
    created_at timestamptz,
    chunk_number int,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ce.id,
        ce.url,
        ce.content,
        ce.summary,
        ce.metadata,
        ce.source_id,
        ce.created_at,
        ce.chunk_number,
        1 - (ce.embedding <=> query_embedding) AS similarity
    FROM code_examples ce
    WHERE 
        (ce.embedding IS NOT NULL) AND
        (1 - (ce.embedding <=> query_embedding)) > similarity_threshold AND
        (source_filter IS NULL OR ce.source_id = source_filter)
    ORDER BY ce.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Add embedding columns to existing tables if they don't exist
-- Note: This assumes your tables might not have embedding columns yet
DO $$
BEGIN
    -- Add embedding column to crawled_pages if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'crawled_pages' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE crawled_pages ADD COLUMN embedding vector(1536);
    END IF;
    
    -- Add embedding column to code_examples if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'code_examples' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE code_examples ADD COLUMN embedding vector(1536);
    END IF;
END $$;

-- Create vector indexes for better performance
-- Note: These will only work if you have embeddings in your tables
CREATE INDEX IF NOT EXISTS idx_crawled_pages_embedding ON crawled_pages USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_code_examples_embedding ON code_examples USING hnsw (embedding vector_cosine_ops);

-- Grant necessary permissions to service role
GRANT EXECUTE ON FUNCTION match_crawled_pages TO service_role;
GRANT EXECUTE ON FUNCTION match_code_examples TO service_role;

-- Optional: Grant to authenticated users if needed
GRANT EXECUTE ON FUNCTION match_crawled_pages TO authenticated;
GRANT EXECUTE ON FUNCTION match_code_examples TO authenticated;

-- Comments for documentation
COMMENT ON FUNCTION match_crawled_pages IS 'Searches crawled_pages using vector similarity with OpenAI embeddings';
COMMENT ON FUNCTION match_code_examples IS 'Searches code_examples using vector similarity with OpenAI embeddings';