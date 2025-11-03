-- 🔄 Sync Status Tracking Tables
-- Enhanced synchronization tracking system for NodeFlow

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main sync status table
CREATE TABLE IF NOT EXISTS sync_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('notion', 'google_calendar', 'apple_calendar', 'slack', 'outlook')),
    is_synced BOOLEAN DEFAULT false,
    is_connected BOOLEAN DEFAULT false,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    next_sync_at TIMESTAMP WITH TIME ZONE,
    sync_frequency INTEGER DEFAULT 15, -- minutes
    is_active BOOLEAN DEFAULT true,
    error_message TEXT,
    items_synced INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    sync_duration_ms INTEGER, -- milliseconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one status per user/platform combination
    UNIQUE(user_id, platform)
);

-- Create indexes for performance
CREATE INDEX idx_sync_status_user_id ON sync_status(user_id);
CREATE INDEX idx_sync_status_platform ON sync_status(platform);
CREATE INDEX idx_sync_status_is_synced ON sync_status(is_synced);
CREATE INDEX idx_sync_status_last_sync ON sync_status(last_sync_at);

-- Sync logs table for detailed history
CREATE TABLE IF NOT EXISTS sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('sync_started', 'sync_completed', 'sync_failed', 'connection_added', 'connection_removed')),
    details JSONB DEFAULT '{}',
    items_processed INTEGER DEFAULT 0,
    items_created INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for logs
CREATE INDEX idx_sync_logs_user_id ON sync_logs(user_id);
CREATE INDEX idx_sync_logs_platform ON sync_logs(platform);
CREATE INDEX idx_sync_logs_action ON sync_logs(action);
CREATE INDEX idx_sync_logs_created_at ON sync_logs(created_at);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_sync_status_updated_at 
    BEFORE UPDATE ON sync_status 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE sync_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_logs ENABLE ROW LEVEL SECURITY;

-- Users can only see their own sync status
CREATE POLICY "Users can view own sync status" ON sync_status
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own sync status" ON sync_status
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sync status" ON sync_status
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only see their own sync logs
CREATE POLICY "Users can view own sync logs" ON sync_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sync logs" ON sync_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- View for platform sync summary
CREATE OR REPLACE VIEW platform_sync_summary AS
SELECT 
    user_id,
    COUNT(*) as total_platforms,
    COUNT(*) FILTER (WHERE is_connected) as connected_platforms,
    COUNT(*) FILTER (WHERE is_synced) as synced_platforms,
    COUNT(*) FILTER (WHERE is_active) as active_platforms,
    MAX(last_sync_at) as latest_sync,
    SUM(items_synced) as total_items_synced,
    SUM(items_failed) as total_items_failed
FROM sync_status
GROUP BY user_id;

-- Grant permissions
GRANT SELECT ON platform_sync_summary TO authenticated;