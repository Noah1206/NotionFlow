-- Create calendar_events table for storing synced events from external calendars
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    external_id TEXT, -- ID from external platform (Google, Notion, etc.)
    calendar_id UUID, -- Reference to calendars table if applicable
    
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
    source_platform TEXT NOT NULL, -- 'google', 'notion', 'apple', etc.
    source_calendar_id TEXT, -- ID of the calendar on the source platform
    source_calendar_name TEXT, -- Name of the calendar on the source platform
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique events per user and platform
    UNIQUE(user_id, external_id, source_platform)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_datetime ON calendar_events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_calendar_id ON calendar_events(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_source ON calendar_events(source_platform, source_calendar_id);

-- Enable Row Level Security
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;

-- Create policy for users to see their own events
CREATE POLICY "Users can view their own events" ON calendar_events
    FOR SELECT USING (auth.uid() = user_id);

-- Create policy for users to insert their own events
CREATE POLICY "Users can insert their own events" ON calendar_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create policy for users to update their own events
CREATE POLICY "Users can update their own events" ON calendar_events
    FOR UPDATE USING (auth.uid() = user_id);

-- Create policy for users to delete their own events
CREATE POLICY "Users can delete their own events" ON calendar_events
    FOR DELETE USING (auth.uid() = user_id);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_calendar_events_updated_at BEFORE UPDATE
    ON calendar_events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();