-- 📅 NotionFlow Calendar System Database Schema (Corrected)
-- Execute this SQL in your Supabase dashboard to create the required tables
-- This schema matches the calendar_service.py implementation

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Calendars table
CREATE TABLE IF NOT EXISTS calendars (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id TEXT NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('personal', 'shared')),
    name VARCHAR(255) DEFAULT 'My Calendar',
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6',
    share_link TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Calendar members table (for shared calendars)
CREATE TABLE IF NOT EXISTS calendar_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calendar_id UUID REFERENCES calendars(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    permissions JSON DEFAULT '{"read": true, "write": false, "delete": false}',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by TEXT,
    UNIQUE(calendar_id, user_id)
);

-- 3. Calendar events table
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calendar_id UUID REFERENCES calendars(id) ON DELETE CASCADE,
    creator_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    start_time TIME,
    end_date DATE,
    end_time TIME,
    all_day BOOLEAN DEFAULT false,
    location TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6',
    status VARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'tentative', 'cancelled')),
    recurring_rule TEXT,
    external_id TEXT,
    external_source VARCHAR(50),
    metadata JSON,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Event attendees table (for meeting events)
CREATE TABLE IF NOT EXISTS event_attendees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES calendar_events(id) ON DELETE CASCADE,
    user_id TEXT,
    email VARCHAR(255),
    name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'tentative')),
    is_organizer BOOLEAN DEFAULT false,
    added_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Calendar sharing tokens (for public sharing)
CREATE TABLE IF NOT EXISTS calendar_share_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calendar_id UUID REFERENCES calendars(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    permissions JSON DEFAULT '{"read": true}',
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_calendars_owner_id ON calendars(owner_id);
CREATE INDEX IF NOT EXISTS idx_calendars_type ON calendars(type);
CREATE INDEX IF NOT EXISTS idx_calendar_members_user_id ON calendar_members(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_members_calendar_id ON calendar_members(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_calendar_id ON calendar_events(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_creator_id ON calendar_events(creator_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_date ON calendar_events(start_date);
CREATE INDEX IF NOT EXISTS idx_calendar_events_external_id ON calendar_events(external_id);
CREATE INDEX IF NOT EXISTS idx_event_attendees_event_id ON event_attendees(event_id);
CREATE INDEX IF NOT EXISTS idx_event_attendees_user_id ON event_attendees(user_id);
CREATE INDEX IF NOT EXISTS idx_share_tokens_token ON calendar_share_tokens(token);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_calendars_updated_at 
    BEFORE UPDATE ON calendars 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calendar_events_updated_at 
    BEFORE UPDATE ON calendar_events 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE calendars ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_attendees ENABLE ROW LEVEL SECURITY;

-- Calendar policies
CREATE POLICY "Users can view calendars they own or are members of" ON calendars
    FOR SELECT USING (
        owner_id = auth.uid()::text OR 
        id IN (SELECT calendar_id FROM calendar_members WHERE user_id = auth.uid()::text)
    );

CREATE POLICY "Users can create their own calendars" ON calendars
    FOR INSERT WITH CHECK (owner_id = auth.uid()::text);

CREATE POLICY "Calendar owners can update their calendars" ON calendars
    FOR UPDATE USING (owner_id = auth.uid()::text);

CREATE POLICY "Calendar owners can delete their calendars" ON calendars
    FOR DELETE USING (owner_id = auth.uid()::text);

-- Calendar members policies
CREATE POLICY "Users can view calendar memberships they're part of" ON calendar_members
    FOR SELECT USING (
        user_id = auth.uid()::text OR 
        calendar_id IN (SELECT id FROM calendars WHERE owner_id = auth.uid()::text)
    );

CREATE POLICY "Calendar owners can manage members" ON calendar_members
    FOR ALL USING (
        calendar_id IN (SELECT id FROM calendars WHERE owner_id = auth.uid()::text)
    );

-- Calendar events policies
CREATE POLICY "Users can view events in their calendars" ON calendar_events
    FOR SELECT USING (
        calendar_id IN (
            SELECT calendar_id FROM calendar_members WHERE user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can create events in calendars they have write access to" ON calendar_events
    FOR INSERT WITH CHECK (
        calendar_id IN (
            SELECT cm.calendar_id FROM calendar_members cm
            WHERE cm.user_id = auth.uid()::text 
            AND (cm.permissions->>'write')::boolean = true
        )
    );

CREATE POLICY "Event creators and calendar owners can update events" ON calendar_events
    FOR UPDATE USING (
        creator_id = auth.uid()::text OR
        calendar_id IN (SELECT id FROM calendars WHERE owner_id = auth.uid()::text)
    );

CREATE POLICY "Event creators and calendar owners can delete events" ON calendar_events
    FOR DELETE USING (
        creator_id = auth.uid()::text OR
        calendar_id IN (SELECT id FROM calendars WHERE owner_id = auth.uid()::text)
    );

-- Verification queries (run these to check if tables were created successfully)
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%calendar%';
-- SELECT * FROM calendars LIMIT 5;
-- SELECT * FROM calendar_members LIMIT 5;
-- SELECT * FROM calendar_events LIMIT 5;