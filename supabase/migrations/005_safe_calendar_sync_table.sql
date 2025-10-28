-- Safe creation of calendar_sync table (with IF NOT EXISTS checks)
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
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'calendar_sync_user_platform_calendar_key') THEN
        ALTER TABLE calendar_sync ADD CONSTRAINT calendar_sync_user_platform_calendar_key 
            UNIQUE(user_id, platform, calendar_id);
    END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_calendar_sync_user_id ON calendar_sync(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_platform ON calendar_sync(platform);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_status ON calendar_sync(sync_status);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_calendar_id ON calendar_sync(calendar_id);

-- Enable RLS if not already enabled
ALTER TABLE calendar_sync ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then recreate
DO $$
BEGIN
    -- Drop policies if they exist
    DROP POLICY IF EXISTS "Users can view their own sync records" ON calendar_sync;
    DROP POLICY IF EXISTS "Users can insert their own sync records" ON calendar_sync;
    DROP POLICY IF EXISTS "Users can update their own sync records" ON calendar_sync;
    DROP POLICY IF EXISTS "Users can delete their own sync records" ON calendar_sync;
EXCEPTION
    WHEN OTHERS THEN
        NULL; -- Ignore errors if policies don't exist
END $$;

-- Create policies
CREATE POLICY "Users can view their own sync records" ON calendar_sync
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own sync records" ON calendar_sync
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own sync records" ON calendar_sync
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own sync records" ON calendar_sync
    FOR DELETE USING (auth.uid()::text = user_id);

-- Add trigger for updated_at if function exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column') THEN
        DROP TRIGGER IF EXISTS update_calendar_sync_updated_at ON calendar_sync;
        CREATE TRIGGER update_calendar_sync_updated_at BEFORE UPDATE
            ON calendar_sync FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;