-- Migration: Add missing sync_status column to calendar_sync_configs table
-- This column is required by the OAuth callback code but was missing from the original table

-- Add sync_status column if it doesn't exist
ALTER TABLE calendar_sync_configs
ADD COLUMN IF NOT EXISTS sync_status TEXT DEFAULT 'active';

-- Update existing records to have a default sync_status based on is_enabled
UPDATE calendar_sync_configs
SET sync_status = CASE
    WHEN is_enabled = true THEN 'active'
    WHEN is_enabled = false AND calendar_id IS NULL THEN 'needs_calendar_selection'
    ELSE 'paused'
END
WHERE sync_status IS NULL;

-- Add other missing columns that the code expects
ALTER TABLE calendar_sync_configs
ADD COLUMN IF NOT EXISTS real_time_sync BOOLEAN DEFAULT false;

ALTER TABLE calendar_sync_configs
ADD COLUMN IF NOT EXISTS sync_settings JSONB DEFAULT '{}';

ALTER TABLE calendar_sync_configs
ADD COLUMN IF NOT EXISTS health_status TEXT DEFAULT 'healthy';

-- Create index on sync_status for performance
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_sync_status ON calendar_sync_configs(sync_status);

-- Update any existing indexes if needed
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_health_status ON calendar_sync_configs(health_status);

-- Add check constraint for sync_status values
ALTER TABLE calendar_sync_configs
ADD CONSTRAINT IF NOT EXISTS chk_sync_status
CHECK (sync_status IN ('active', 'paused', 'error', 'disconnected', 'needs_calendar_selection'));

-- Add check constraint for health_status values
ALTER TABLE calendar_sync_configs
ADD CONSTRAINT IF NOT EXISTS chk_health_status
CHECK (health_status IN ('healthy', 'warning', 'error'));

-- Add comment about the migration
COMMENT ON COLUMN calendar_sync_configs.sync_status IS 'Synchronization status: active, paused, error, disconnected, needs_calendar_selection';
COMMENT ON COLUMN calendar_sync_configs.health_status IS 'Health status: healthy, warning, error';