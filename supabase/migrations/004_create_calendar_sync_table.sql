-- Create calendar_sync table for tracking calendar synchronization status
CREATE TABLE IF NOT EXISTS calendar_sync (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL, -- 'notion', 'google', 'apple', 'outlook', etc.
    calendar_id UUID NOT NULL, -- Reference to calendars table
    sync_status TEXT DEFAULT 'active', -- 'active', 'paused', 'error', 'disconnected'
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    last_sync_at TIMESTAMPTZ,
    sync_frequency_minutes INTEGER DEFAULT 15,
    consecutive_failures INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique sync per user-platform-calendar
    UNIQUE(user_id, platform, calendar_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_calendar_sync_user_id ON calendar_sync(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_platform ON calendar_sync(platform);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_status ON calendar_sync(sync_status);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_calendar_id ON calendar_sync(calendar_id);

-- Enable Row Level Security
ALTER TABLE calendar_sync ENABLE ROW LEVEL SECURITY;

-- Create policies for users to access their own sync records
CREATE POLICY "Users can view their own sync records" ON calendar_sync
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own sync records" ON calendar_sync
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own sync records" ON calendar_sync
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own sync records" ON calendar_sync
    FOR DELETE USING (auth.uid()::text = user_id);

-- Add trigger for updated_at
CREATE TRIGGER update_calendar_sync_updated_at BEFORE UPDATE
    ON calendar_sync FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();