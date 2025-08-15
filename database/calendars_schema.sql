-- ============================================
-- 🗓️ Calendars Table Schema
-- Comprehensive calendar management with media file support
-- ============================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create calendars table
CREATE TABLE IF NOT EXISTS calendars (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    
    -- Calendar basic information
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    color VARCHAR(7) DEFAULT '#3B82F6', -- Hex color code
    platform VARCHAR(50) DEFAULT 'custom', -- custom, notion, google, apple, outlook
    is_shared BOOLEAN DEFAULT false,
    
    -- Media file information
    media_filename VARCHAR(255) DEFAULT NULL, -- User-friendly filename
    media_file_path VARCHAR(500) DEFAULT NULL, -- Actual stored filename
    media_file_type VARCHAR(20) DEFAULT NULL, -- 'audio' or 'video'
    
    -- Metadata
    event_count INTEGER DEFAULT 0,
    sync_status VARCHAR(20) DEFAULT 'active', -- active, syncing, inactive
    last_sync_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

-- Create RLS policies
-- Users can only access their own calendars
CREATE POLICY "Users can view their own calendars" ON calendars
    FOR SELECT USING (user_id = auth.uid()::uuid);

CREATE POLICY "Users can insert their own calendars" ON calendars
    FOR INSERT WITH CHECK (user_id = auth.uid()::uuid);

CREATE POLICY "Users can update their own calendars" ON calendars
    FOR UPDATE USING (user_id = auth.uid()::uuid);

CREATE POLICY "Users can delete their own calendars" ON calendars
    FOR DELETE USING (user_id = auth.uid()::uuid);

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

-- Insert sample data (optional)
-- INSERT INTO calendars (user_id, name, description, color, platform) VALUES
-- (uuid_generate_v4(), 'Work Calendar', 'Professional meetings and deadlines', '#DC2626', 'google'),
-- (uuid_generate_v4(), 'Personal Calendar', 'Personal events and reminders', '#059669', 'apple'),
-- (uuid_generate_v4(), 'Team Calendar', 'Shared team events', '#7C3AED', 'notion');

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