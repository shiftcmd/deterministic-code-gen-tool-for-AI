-- Error logging table for React frontend
CREATE TABLE IF NOT EXISTS error_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    error_id TEXT NOT NULL,
    session_id TEXT,
    user_id TEXT DEFAULT 'anonymous',
    type TEXT NOT NULL,
    message TEXT,
    stack TEXT,
    endpoint TEXT,
    method TEXT,
    status INTEGER,
    response_data JSONB,
    request_data JSONB,
    context JSONB,
    browser_info JSONB,
    url TEXT,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_type ON error_logs(type);
CREATE INDEX IF NOT EXISTS idx_error_logs_session_id ON error_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_user_id ON error_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_status ON error_logs(status);
CREATE INDEX IF NOT EXISTS idx_error_logs_endpoint ON error_logs(endpoint);

-- React documentation table for vector search
CREATE TABLE IF NOT EXISTS react_docs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url TEXT,
    section TEXT,
    tags TEXT[],
    embedding vector(1536), -- OpenAI embedding dimension
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector search
CREATE INDEX IF NOT EXISTS idx_react_docs_embedding ON react_docs USING ivfflat (embedding vector_cosine_ops);

-- Function to search React docs using vector similarity
CREATE OR REPLACE FUNCTION search_react_docs(
    query_text TEXT,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    url TEXT,
    section TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
    query_embedding vector(1536);
BEGIN
    -- You would typically get this embedding from your application
    -- This is a placeholder for the actual embedding generation
    SELECT embedding INTO query_embedding 
    FROM react_docs 
    WHERE content ILIKE '%' || query_text || '%' 
    LIMIT 1;

    IF query_embedding IS NULL THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT 
        react_docs.id,
        react_docs.title,
        react_docs.content,
        react_docs.url,
        react_docs.section,
        1 - (react_docs.embedding <=> query_embedding) AS similarity
    FROM react_docs
    WHERE 1 - (react_docs.embedding <=> query_embedding) > match_threshold
    ORDER BY react_docs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get error statistics
CREATE OR REPLACE FUNCTION get_error_stats(timeframe TEXT DEFAULT '24h')
RETURNS TABLE (
    total_errors BIGINT,
    api_errors BIGINT,
    javascript_errors BIGINT,
    unique_sessions BIGINT,
    most_common_error TEXT,
    error_count_by_hour JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    interval_duration INTERVAL;
BEGIN
    -- Parse timeframe
    CASE timeframe
        WHEN '1h' THEN interval_duration := INTERVAL '1 hour';
        WHEN '24h' THEN interval_duration := INTERVAL '24 hours';
        WHEN '7d' THEN interval_duration := INTERVAL '7 days';
        WHEN '30d' THEN interval_duration := INTERVAL '30 days';
        ELSE interval_duration := INTERVAL '24 hours';
    END CASE;

    RETURN QUERY
    WITH error_stats AS (
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE type = 'api_error') as api,
            COUNT(*) FILTER (WHERE type = 'javascript_error') as js,
            COUNT(DISTINCT session_id) as sessions
        FROM error_logs 
        WHERE timestamp >= NOW() - interval_duration
    ),
    common_error AS (
        SELECT message
        FROM error_logs 
        WHERE timestamp >= NOW() - interval_duration
        GROUP BY message
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ),
    hourly_stats AS (
        SELECT jsonb_object_agg(
            EXTRACT(HOUR FROM timestamp)::TEXT,
            error_count
        ) as hourly_data
        FROM (
            SELECT 
                EXTRACT(HOUR FROM timestamp) as hour,
                COUNT(*) as error_count
            FROM error_logs 
            WHERE timestamp >= NOW() - interval_duration
            GROUP BY EXTRACT(HOUR FROM timestamp)
            ORDER BY hour
        ) hourly
    )
    SELECT 
        es.total,
        es.api,
        es.js,
        es.sessions,
        ce.message,
        hs.hourly_data
    FROM error_stats es
    CROSS JOIN common_error ce
    CROSS JOIN hourly_stats hs;
END;
$$;

-- Sample React documentation data
INSERT INTO react_docs (title, content, url, section, tags) VALUES
('React Router v6 Future Flags', 'React Router v6 includes future flags to help with migration to v7. The v7_startTransition flag wraps state updates in React.startTransition. Enable this by adding future={{ v7_startTransition: true }} to your router.', 'https://reactrouter.com/v6/upgrading/future', 'Migration', ARRAY['router', 'migration', 'v7', 'startTransition']),
('React Router Relative Splat Routes', 'The v7_relativeSplatPath flag changes how relative route resolution works within splat routes. Add future={{ v7_relativeSplatPath: true }} to your router to opt in early.', 'https://reactrouter.com/v6/upgrading/future', 'Migration', ARRAY['router', 'splat', 'relative', 'v7']),
('Antd Card Component Styles', 'The bodyStyle prop in Antd Card is deprecated. Use styles={{ body: {...} }} instead of bodyStyle={{...}}.', 'https://ant.design/components/card', 'Components', ARRAY['antd', 'card', 'styles', 'deprecated']),
('API Error Handling', 'Handle API errors by checking response.status and providing meaningful error messages to users. Implement retry logic for network errors.', 'https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API', 'API', ARRAY['api', 'error', 'handling', 'fetch']),
('React Error Boundaries', 'Use Error Boundaries to catch JavaScript errors in component trees. Create a class component with componentDidCatch or use react-error-boundary library.', 'https://reactjs.org/docs/error-boundaries.html', 'Error Handling', ARRAY['react', 'error', 'boundary', 'componentDidCatch']);

-- RLS (Row Level Security) policies
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE react_docs ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to insert their own errors
CREATE POLICY "Users can insert their own errors" ON error_logs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');

-- Allow authenticated users to read their own errors
CREATE POLICY "Users can read their own errors" ON error_logs
    FOR SELECT USING (auth.uid()::text = user_id OR user_id = 'anonymous');

-- Allow everyone to read React docs
CREATE POLICY "Everyone can read React docs" ON react_docs
    FOR SELECT USING (true);

-- Only admins can modify React docs
CREATE POLICY "Only admins can modify React docs" ON react_docs
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');