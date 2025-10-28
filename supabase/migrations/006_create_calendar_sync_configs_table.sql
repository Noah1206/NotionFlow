-- Migration: Create calendar_sync_configs table
-- This table is heavily used by the application but was missing from the schema

-- Create calendar_sync_configs table
CREATE TABLE IF NOT EXISTS calendar_sync_configs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL, -- 'notion', 'google', 'apple', 'outlook', etc.
    calendar_id UUID, -- Reference to calendars table (nullable for when no calendar selected yet)

    -- Credentials stored as JSONB
    credentials JSONB DEFAULT '{}',

    -- Sync configuration
    is_enabled BOOLEAN DEFAULT true,
    sync_status TEXT DEFAULT 'active', -- 'active', 'paused', 'error', 'disconnected', 'needs_calendar_selection'
    sync_frequency_minutes INTEGER DEFAULT 15,
    real_time_sync BOOLEAN DEFAULT false,

    -- Sync tracking
    last_sync_at TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    consecutive_failures INTEGER DEFAULT 0,

    -- Settings and metadata
    sync_settings JSONB DEFAULT '{}',
    sync_errors JSONB DEFAULT '[]',
    health_status TEXT DEFAULT 'healthy', -- 'healthy', 'warning', 'error'
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique sync per user-platform
    UNIQUE(user_id, platform)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_user_id ON calendar_sync_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_platform ON calendar_sync_configs(platform);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_status ON calendar_sync_configs(sync_status);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_calendar_id ON calendar_sync_configs(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_enabled ON calendar_sync_configs(is_enabled);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_last_sync ON calendar_sync_configs(last_sync_at);

-- Enable Row Level Security
ALTER TABLE calendar_sync_configs ENABLE ROW LEVEL SECURITY;

-- Create policies for users to access their own sync configs
CREATE POLICY "Users can view their own sync configs" ON calendar_sync_configs
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own sync configs" ON calendar_sync_configs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own sync configs" ON calendar_sync_configs
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own sync configs" ON calendar_sync_configs
    FOR DELETE USING (auth.uid()::text = user_id);

-- Service role policies (for backend operations)
CREATE POLICY "Service role full access calendar_sync_configs" ON calendar_sync_configs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Add trigger for updated_at
CREATE TRIGGER update_calendar_sync_configs_updated_at BEFORE UPDATE
    ON calendar_sync_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comment
COMMENT ON TABLE calendar_sync_configs IS 'Platform synchronization configuration and credentials storage';