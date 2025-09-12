-- Create master_auth table for password storage
CREATE TABLE IF NOT EXISTS master_auth (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create searches table for search campaigns
CREATE TABLE IF NOT EXISTS searches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT,
    search_keywords TEXT NOT NULL,
    location TEXT,
    resume_last_updated_days INTEGER,
    target_candidates INTEGER,
    max_radius INTEGER,
    recipient_email TEXT,
    user_prompt TEXT,
    system_prompt TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    results JSONB,
    filters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Enable Row Level Security
ALTER TABLE master_auth ENABLE ROW LEVEL SECURITY;
ALTER TABLE searches ENABLE ROW LEVEL SECURITY;

-- Create policies for anonymous access (adjust as needed)
CREATE POLICY "Allow anonymous read master_auth" ON master_auth
    FOR SELECT USING (true);

CREATE POLICY "Allow anonymous insert master_auth" ON master_auth
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow anonymous all searches" ON searches
    FOR ALL USING (true);