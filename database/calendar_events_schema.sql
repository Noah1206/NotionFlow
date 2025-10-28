-- ============================================
-- 📅 Calendar Events Table Schema
-- Stores actual calendar events from all platforms
-- ============================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Events table for storing calendar events
CREATE TABLE IF NOT EXISTS calendar_events (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL, -- Match format from calendars table
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    
    -- Event basic information
    title VARCHAR(255) NOT NULL DEFAULT 'Untitled Event',
    description TEXT,
    location TEXT,
    
    -- Date and time information
    start_datetime TIMESTAMP WITH TIME ZONE,
    end_datetime TIMESTAMP WITH TIME ZONE,
    start_date DATE, -- For all-day events
    end_date DATE, -- For all-day events
    is_all_day BOOLEAN DEFAULT false,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Event type and status
    status VARCHAR(20) DEFAULT 'confirmed', -- confirmed, tentative, cancelled
    visibility VARCHAR(20) DEFAULT 'default', -- default, public, private, confidential
    
    -- Platform integration
    platform VARCHAR(50) DEFAULT 'notionflow', -- notionflow, google, outlook, apple, slack
    external_event_id VARCHAR(255), -- ID from external platform
    external_calendar_id VARCHAR(255), -- Calendar ID from external platform
    
    -- Recurrence information
    is_recurring BOOLEAN DEFAULT false,
    recurrence_rule TEXT, -- RRULE format
    parent_event_id UUID REFERENCES calendar_events(id), -- For recurring event instances
    
    -- Attendees and sharing
    attendees JSONB DEFAULT '[]', -- Array of attendee objects
    created_by TEXT, -- User who created the event
    
    -- Notification and reminder
    reminders JSONB DEFAULT '[]', -- Array of reminder objects
    
    -- Additional metadata
    event_metadata JSONB DEFAULT '{}', -- Additional platform-specific data
    html_link TEXT, -- Link to event in external platform
    
    -- Sync information
    sync_status VARCHAR(20) DEFAULT 'synced', -- synced, pending, failed, conflict
    last_synced_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_datetime_range CHECK (
        (start_datetime IS NULL OR end_datetime IS NULL) OR 
        (start_datetime <= end_datetime)
    ),
    CONSTRAINT valid_date_range CHECK (
        (start_date IS NULL OR end_date IS NULL) OR 
        (start_date <= end_date)
    ),
    CONSTRAINT valid_all_day_dates CHECK (
        (is_all_day = false AND start_datetime IS NOT NULL AND end_datetime IS NOT NULL) OR
        (is_all_day = true AND start_date IS NOT NULL AND end_date IS NOT NULL)
    ),
    
    -- Unique constraint for external events
    CONSTRAINT unique_external_event UNIQUE (user_id, platform, external_event_id)
);

-- ============================================
-- 📊 INDEXES (Performance Optimization)
-- ============================================

-- User and calendar indexes
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_calendar_id ON calendar_events(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_calendar ON calendar_events(user_id, calendar_id);

-- Date and time indexes for queries
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_datetime ON calendar_events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_end_datetime ON calendar_events(end_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_date_range ON calendar_events(start_datetime, end_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_date ON calendar_events(start_date);

-- Platform and sync indexes
CREATE INDEX IF NOT EXISTS idx_calendar_events_platform ON calendar_events(platform);
CREATE INDEX IF NOT EXISTS idx_calendar_events_external_id ON calendar_events(external_event_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_sync_status ON calendar_events(sync_status);

-- Recurring events index
CREATE INDEX IF NOT EXISTS idx_calendar_events_parent_id ON calendar_events(parent_event_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_recurring ON calendar_events(is_recurring);

-- Status and metadata indexes
CREATE INDEX IF NOT EXISTS idx_calendar_events_status ON calendar_events(status);
CREATE INDEX IF NOT EXISTS idx_calendar_events_created_at ON calendar_events(created_at);
CREATE INDEX IF NOT EXISTS idx_calendar_events_updated_at ON calendar_events(updated_at);

-- ============================================
-- 🔄 TRIGGERS (Auto-update timestamps)
-- ============================================

-- Updated at trigger function (reuse existing function)
CREATE TRIGGER update_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 🔐 ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;

-- Users can manage their own events
CREATE POLICY "Users can view their own events" ON calendar_events
    FOR SELECT USING (user_id = auth.uid()::text);
    
CREATE POLICY "Users can insert their own events" ON calendar_events
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);
    
CREATE POLICY "Users can update their own events" ON calendar_events
    FOR UPDATE USING (user_id = auth.uid()::text);
    
CREATE POLICY "Users can delete their own events" ON calendar_events
    FOR DELETE USING (user_id = auth.uid()::text);

-- Service role policies (for backend operations)
CREATE POLICY "Service role full access calendar events" ON calendar_events
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- 🔧 UTILITY FUNCTIONS
-- ============================================

-- Function to get events in date range
CREATE OR REPLACE FUNCTION get_calendar_events_in_range(
    p_user_id TEXT,
    p_calendar_id UUID DEFAULT NULL,
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    event_id UUID,
    calendar_id UUID,
    title VARCHAR(255),
    description TEXT,
    start_datetime TIMESTAMP WITH TIME ZONE,
    end_datetime TIMESTAMP WITH TIME ZONE,
    is_all_day BOOLEAN,
    status VARCHAR(20),
    platform VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ce.id,
        ce.calendar_id,
        ce.title,
        ce.description,
        ce.start_datetime,
        ce.end_datetime,
        ce.is_all_day,
        ce.status,
        ce.platform
    FROM calendar_events ce
    WHERE ce.user_id = p_user_id
      AND (p_calendar_id IS NULL OR ce.calendar_id = p_calendar_id)
      AND (p_start_date IS NULL OR ce.end_datetime >= p_start_date)
      AND (p_end_date IS NULL OR ce.start_datetime <= p_end_date)
      AND ce.status != 'cancelled'
    ORDER BY ce.start_datetime ASC NULLS LAST, ce.start_date ASC NULLS LAST;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create event from Google Calendar data
CREATE OR REPLACE FUNCTION create_event_from_google(
    p_user_id TEXT,
    p_calendar_id UUID,
    p_google_event JSONB
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
    v_start_datetime TIMESTAMP WITH TIME ZONE;
    v_end_datetime TIMESTAMP WITH TIME ZONE;
    v_start_date DATE;
    v_end_date DATE;
    v_is_all_day BOOLEAN := false;
BEGIN
    -- Parse datetime or date fields
    IF p_google_event->'start'->>'dateTime' IS NOT NULL THEN
        v_start_datetime := (p_google_event->'start'->>'dateTime')::TIMESTAMP WITH TIME ZONE;
        v_end_datetime := (p_google_event->'end'->>'dateTime')::TIMESTAMP WITH TIME ZONE;
        v_is_all_day := false;
    ELSE
        v_start_date := (p_google_event->'start'->>'date')::DATE;
        v_end_date := (p_google_event->'end'->>'date')::DATE;
        v_is_all_day := true;
    END IF;

    INSERT INTO calendar_events (
        user_id,
        calendar_id,
        title,
        description,
        location,
        start_datetime,
        end_datetime,
        start_date,
        end_date,
        is_all_day,
        platform,
        external_event_id,
        status,
        attendees,
        event_metadata,
        html_link,
        sync_status,
        last_synced_at
    ) VALUES (
        p_user_id,
        p_calendar_id,
        COALESCE(p_google_event->>'summary', 'Untitled Event'),
        p_google_event->>'description',
        p_google_event->>'location',
        v_start_datetime,
        v_end_datetime,
        v_start_date,
        v_end_date,
        v_is_all_day,
        'google',
        p_google_event->>'id',
        COALESCE(p_google_event->>'status', 'confirmed'),
        COALESCE(p_google_event->'attendees', '[]'),
        p_google_event,
        p_google_event->>'htmlLink',
        'synced',
        NOW()
    ) 
    ON CONFLICT (user_id, platform, external_event_id) 
    DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        location = EXCLUDED.location,
        start_datetime = EXCLUDED.start_datetime,
        end_datetime = EXCLUDED.end_datetime,
        start_date = EXCLUDED.start_date,
        end_date = EXCLUDED.end_date,
        is_all_day = EXCLUDED.is_all_day,
        status = EXCLUDED.status,
        attendees = EXCLUDED.attendees,
        event_metadata = EXCLUDED.event_metadata,
        html_link = EXCLUDED.html_link,
        last_synced_at = NOW(),
        updated_at = NOW()
    RETURNING id INTO v_event_id;
    
    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 📝 TABLE COMMENTS (Documentation)
-- ============================================

COMMENT ON TABLE calendar_events IS 'Stores calendar events from all platforms';
COMMENT ON COLUMN calendar_events.external_event_id IS 'ID from external platform (Google, Outlook, etc.)';
COMMENT ON COLUMN calendar_events.is_all_day IS 'True for all-day events, uses start_date/end_date instead of datetime';
COMMENT ON COLUMN calendar_events.recurrence_rule IS 'RRULE format for recurring events';
COMMENT ON COLUMN calendar_events.attendees IS 'JSON array of attendee objects with email, name, status';
COMMENT ON COLUMN calendar_events.reminders IS 'JSON array of reminder objects with method and minutes';
COMMENT ON COLUMN calendar_events.event_metadata IS 'Additional platform-specific metadata';

-- Grant necessary permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON calendar_events TO service_role;

-- ============================================
-- 🎉 CALENDAR EVENTS SCHEMA COMPLETE
-- ============================================