-- Check if calendar_events table exists and add missing columns if needed

-- First, create the table if it doesn't exist
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    external_id TEXT,
    
    -- Event details
    title TEXT NOT NULL,
    description TEXT,
    start_datetime TIMESTAMPTZ NOT NULL,
    end_datetime TIMESTAMPTZ NOT NULL,
    is_all_day BOOLEAN DEFAULT false,
    
    -- Location and attendees
    location TEXT,
    attendees JSONB,
    
    -- Categorization
    category TEXT,
    priority TEXT,
    status TEXT DEFAULT 'confirmed',
    
    -- Source information
    source_platform TEXT NOT NULL,
    source_calendar_id TEXT,
    source_calendar_name TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add columns if they don't exist (safe to run multiple times)
DO $$ 
BEGIN
    -- Add external_id if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='calendar_events' AND column_name='external_id') THEN
        ALTER TABLE calendar_events ADD COLUMN external_id TEXT;
    END IF;
    
    -- Add source_calendar_id if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='calendar_events' AND column_name='source_calendar_id') THEN
        ALTER TABLE calendar_events ADD COLUMN source_calendar_id TEXT;
    END IF;
    
    -- Add source_calendar_name if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='calendar_events' AND column_name='source_calendar_name') THEN
        ALTER TABLE calendar_events ADD COLUMN source_calendar_name TEXT;
    END IF;
    
    -- Add source_platform if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='calendar_events' AND column_name='source_platform') THEN
        ALTER TABLE calendar_events ADD COLUMN source_platform TEXT;
    END IF;
    
    -- Add attendees if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='calendar_events' AND column_name='attendees') THEN
        ALTER TABLE calendar_events ADD COLUMN attendees JSONB;
    END IF;
END $$;

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'calendar_events_user_external_platform_key') THEN
        ALTER TABLE calendar_events ADD CONSTRAINT calendar_events_user_external_platform_key 
            UNIQUE(user_id, external_id, source_platform);
    END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_datetime ON calendar_events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_source ON calendar_events(source_platform, source_calendar_id);

-- Enable RLS if not already enabled
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist and recreate them
DROP POLICY IF EXISTS "Users can view their own events" ON calendar_events;
DROP POLICY IF EXISTS "Users can insert their own events" ON calendar_events;
DROP POLICY IF EXISTS "Users can update their own events" ON calendar_events;
DROP POLICY IF EXISTS "Users can delete their own events" ON calendar_events;

-- Create policies
CREATE POLICY "Users can view their own events" ON calendar_events
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own events" ON calendar_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own events" ON calendar_events
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own events" ON calendar_events
    FOR DELETE USING (auth.uid() = user_id);