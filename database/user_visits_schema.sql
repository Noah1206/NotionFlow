-- 🚀 NotionFlow User Visit Tracking Schema
-- This tracks user calendar page visits and popup display status
-- Execute this SQL in your Supabase dashboard

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User visits tracking table
CREATE TABLE IF NOT EXISTS user_visits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    visit_type VARCHAR(50) NOT NULL DEFAULT 'calendar_page',
    visit_count INTEGER DEFAULT 1,
    first_visit_at TIMESTAMPTZ DEFAULT NOW(),
    last_visit_at TIMESTAMPTZ DEFAULT NOW(),
    popup_shown BOOLEAN DEFAULT false,
    popup_shown_at TIMESTAMPTZ,
    popup_dismissed BOOLEAN DEFAULT false,
    popup_dismissed_at TIMESTAMPTZ,
    calendar_created BOOLEAN DEFAULT false,
    calendar_created_at TIMESTAMPTZ,
    user_agent TEXT,
    ip_address INET,
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one record per user per visit type
    UNIQUE(user_id, visit_type)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_visits_user_id ON user_visits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_visits_visit_type ON user_visits(visit_type);
CREATE INDEX IF NOT EXISTS idx_user_visits_popup_shown ON user_visits(popup_shown);
CREATE INDEX IF NOT EXISTS idx_user_visits_first_visit ON user_visits(first_visit_at);

-- Row Level Security (RLS)
ALTER TABLE user_visits ENABLE ROW LEVEL SECURITY;

-- Create policy for users to access only their own visit records
CREATE POLICY IF NOT EXISTS "Users can view own visit records"
    ON user_visits FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY IF NOT EXISTS "Users can insert own visit records"
    ON user_visits FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY IF NOT EXISTS "Users can update own visit records"
    ON user_visits FOR UPDATE
    USING (auth.uid()::text = user_id);

-- Create function to update visit count and last visit time
CREATE OR REPLACE FUNCTION update_user_visit()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    
    -- If this is an update to visit_count, update last_visit_at
    IF OLD.visit_count IS DISTINCT FROM NEW.visit_count THEN
        NEW.last_visit_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic updates
DROP TRIGGER IF EXISTS trigger_update_user_visit ON user_visits;
CREATE TRIGGER trigger_update_user_visit
    BEFORE UPDATE ON user_visits
    FOR EACH ROW
    EXECUTE FUNCTION update_user_visit();

-- Insert comment for documentation
COMMENT ON TABLE user_visits IS 'Tracks user visits to calendar pages and popup display status for first-time user experience';
COMMENT ON COLUMN user_visits.user_id IS 'References the authenticated user ID from Supabase auth';
COMMENT ON COLUMN user_visits.visit_type IS 'Type of visit being tracked (calendar_page, dashboard, etc.)';
COMMENT ON COLUMN user_visits.visit_count IS 'Number of times user has visited this type of page';
COMMENT ON COLUMN user_visits.popup_shown IS 'Whether the welcome popup has been shown to this user';
COMMENT ON COLUMN user_visits.popup_dismissed IS 'Whether user has dismissed the popup (나중에 하기)';
COMMENT ON COLUMN user_visits.calendar_created IS 'Whether user created a calendar during their visits';