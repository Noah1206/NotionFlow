-- ============================================
-- 🗓️ Calendars Table Schema
-- Comprehensive calendar management with media file support
-- ============================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create calendars table (compatible with current JSON structure)
CREATE TABLE IF NOT EXISTS calendars (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL, -- Changed to TEXT to match current session user_id
    
    -- Calendar basic information  
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#2563eb', -- Match current default color
    platform VARCHAR(50) DEFAULT 'custom', -- custom, notion, google, apple, outlook
    is_shared BOOLEAN DEFAULT false,
    
    -- Current JSON structure fields
    event_count INTEGER DEFAULT 0,
    sync_status VARCHAR(20) DEFAULT 'synced', -- synced, syncing, error, active
    last_sync_display TEXT DEFAULT 'Just now', -- Human readable sync time
    is_enabled BOOLEAN DEFAULT true, -- Calendar enabled/disabled status
    shared_with_count INTEGER DEFAULT 0, -- For shared calendars
    
    -- Media file information (for future use)
    media_filename VARCHAR(255) DEFAULT NULL, -- User-friendly filename
    media_file_path VARCHAR(500) DEFAULT NULL, -- Actual stored filename
    media_file_type VARCHAR(20) DEFAULT NULL, -- 'audio' or 'video'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint for user + calendar name
    CONSTRAINT calendars_user_name_unique UNIQUE (user_id, name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_calendars_user_id ON calendars(user_id);
CREATE INDEX IF NOT EXISTS idx_calendars_platform ON calendars(platform);
CREATE INDEX IF NOT EXISTS idx_calendars_sync_status ON calendars(sync_status);
CREATE INDEX IF NOT EXISTS idx_calendars_created_at ON calendars(created_at);
CREATE INDEX IF NOT EXISTS idx_calendars_media_file_path ON calendars(media_file_path);

-- Add foreign key constraint to users table (if exists)
-- ALTER TABLE calendars 
-- ADD CONSTRAINT fk_calendars_user_id 
-- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Enable Row Level Security (RLS)
ALTER TABLE calendars ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (updated for TEXT user_id)
-- Users can only access their own calendars
CREATE POLICY "Users can view their own calendars" ON calendars
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert their own calendars" ON calendars
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update their own calendars" ON calendars
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "Users can delete their own calendars" ON calendars
    FOR DELETE USING (user_id = auth.uid()::text);

-- Additional policy for shared calendars (for future expansion)
CREATE POLICY "Users can view shared calendars" ON calendars
    FOR SELECT USING (is_shared = true);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_calendars_updated_at
    BEFORE UPDATE ON calendars
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 🔄 Migration Functions
-- ============================================

-- Function to create default calendar for new users
CREATE OR REPLACE FUNCTION create_default_calendar_for_user(p_user_id TEXT)
RETURNS UUID AS $$
DECLARE
    calendar_id UUID;
BEGIN
    INSERT INTO calendars (
        user_id,
        name,
        platform,
        color,
        event_count,
        sync_status,
        last_sync_display,
        is_enabled
    ) VALUES (
        p_user_id,
        'Todo List',
        'notion',
        '#2563eb',
        24,
        'synced',
        'Synced 2 min ago',
        TRUE
    ) RETURNING id INTO calendar_id;
    
    RETURN calendar_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to migrate JSON calendar data to database
CREATE OR REPLACE FUNCTION migrate_calendar_from_json(
    p_user_id TEXT,
    p_calendar_data JSONB
)
RETURNS UUID AS $$
DECLARE
    calendar_id UUID;
    calendar_uuid UUID;
BEGIN
    -- Try to parse existing UUID, or generate new one
    BEGIN
        calendar_uuid := (p_calendar_data->>'id')::UUID;
    EXCEPTION WHEN invalid_text_representation THEN
        calendar_uuid := uuid_generate_v4();
    END;
    
    INSERT INTO calendars (
        id,
        user_id,
        name,
        color,
        platform,
        is_shared,
        event_count,
        sync_status,
        last_sync_display,
        is_enabled,
        shared_with_count,
        created_at
    ) VALUES (
        calendar_uuid,
        p_user_id,
        p_calendar_data->>'name',
        COALESCE(p_calendar_data->>'color', '#2563eb'),
        COALESCE(p_calendar_data->>'platform', 'custom'),
        COALESCE((p_calendar_data->>'is_shared')::BOOLEAN, FALSE),
        COALESCE((p_calendar_data->>'event_count')::INTEGER, 0),
        COALESCE(p_calendar_data->>'sync_status', 'synced'),
        COALESCE(p_calendar_data->>'last_sync_display', 'Just now'),
        COALESCE((p_calendar_data->>'is_enabled')::BOOLEAN, TRUE),
        COALESCE((p_calendar_data->>'shared_with_count')::INTEGER, 0),
        COALESCE((p_calendar_data->>'created_at')::TIMESTAMPTZ, NOW())
    ) 
    ON CONFLICT (user_id, name) DO UPDATE SET
        color = EXCLUDED.color,
        platform = EXCLUDED.platform,
        is_shared = EXCLUDED.is_shared,
        event_count = EXCLUDED.event_count,
        sync_status = EXCLUDED.sync_status,
        last_sync_display = EXCLUDED.last_sync_display,
        is_enabled = EXCLUDED.is_enabled,
        shared_with_count = EXCLUDED.shared_with_count,
        updated_at = NOW()
    RETURNING id INTO calendar_id;
    
    RETURN calendar_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comments for documentation
COMMENT ON TABLE calendars IS 'User calendars with media file support';
COMMENT ON COLUMN calendars.id IS 'Unique calendar identifier';
COMMENT ON COLUMN calendars.user_id IS 'Owner of the calendar';
COMMENT ON COLUMN calendars.name IS 'Calendar display name';
COMMENT ON COLUMN calendars.description IS 'Calendar description';
COMMENT ON COLUMN calendars.color IS 'Calendar color in hex format';
COMMENT ON COLUMN calendars.platform IS 'Connected platform (custom, notion, google, apple, outlook)';
COMMENT ON COLUMN calendars.is_shared IS 'Whether calendar is shared with others';
COMMENT ON COLUMN calendars.media_filename IS 'User-friendly media file name';
COMMENT ON COLUMN calendars.media_file_path IS 'Actual stored media file path';
COMMENT ON COLUMN calendars.media_file_type IS 'Media file type (audio/video)';
COMMENT ON COLUMN calendars.event_count IS 'Number of events in calendar';
COMMENT ON COLUMN calendars.sync_status IS 'Calendar synchronization status';
COMMENT ON COLUMN calendars.last_sync_at IS 'Last synchronization timestamp';
COMMENT ON COLUMN calendars.created_at IS 'Calendar creation timestamp';
COMMENT ON COLUMN calendars.updated_at IS 'Last update timestamp';

-- Grant necessary permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON calendars TO authenticated;
-- GRANT USAGE ON SEQUENCE calendars_id_seq TO authenticated;