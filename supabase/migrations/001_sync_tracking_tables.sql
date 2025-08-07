-- Migration: Create sync tracking tables for NotionFlow
-- Version: 001
-- Date: 2025-01-25

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS sync_analytics CASCADE;
DROP TABLE IF EXISTS user_activity CASCADE;
DROP TABLE IF EXISTS platform_coverage CASCADE;
DROP TABLE IF EXISTS sync_events CASCADE;

-- 1. Create sync_events table - stores all synchronization events
CREATE TABLE sync_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
    'sync_started', 'sync_completed', 'sync_failed', 
    'item_created', 'item_updated', 'item_deleted',
    'platform_connected', 'platform_disconnected'
  )),
  platform VARCHAR(50) NOT NULL CHECK (platform IN (
    'notion', 'google', 'slack', 'outlook', 'todoist', 'apple'
  )),
  source_platform VARCHAR(50),
  target_platform VARCHAR(50),
  item_type VARCHAR(50) CHECK (item_type IN (
    'task', 'event', 'note', 'meeting', 'calendar', NULL
  )),
  item_id TEXT,
  item_title TEXT,
  status VARCHAR(20) CHECK (status IN ('success', 'failed', 'skipped', 'pending')),
  error_message TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  sync_job_id UUID
);

-- Create indexes for performance
CREATE INDEX idx_sync_events_user_created ON sync_events(user_id, created_at DESC);
CREATE INDEX idx_sync_events_platform ON sync_events(platform, created_at DESC);
CREATE INDEX idx_sync_events_type ON sync_events(event_type, created_at DESC);

-- 2. Create platform_coverage table - tracks platform usage and coverage
CREATE TABLE platform_coverage (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  platform VARCHAR(50) NOT NULL,
  is_connected BOOLEAN DEFAULT false,
  first_connected_at TIMESTAMP WITH TIME ZONE,
  last_active_at TIMESTAMP WITH TIME ZONE,
  total_synced_items INTEGER DEFAULT 0,
  total_failed_items INTEGER DEFAULT 0,
  sync_success_rate DECIMAL(5,2) DEFAULT 0.00,
  avg_sync_duration_ms INTEGER DEFAULT 0,
  feature_coverage JSONB DEFAULT '{
    "sync_tasks": false,
    "sync_events": false,
    "sync_notes": false,
    "bidirectional": false,
    "real_time": false,
    "webhooks": false
  }',
  platform_config JSONB DEFAULT '{}',
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, platform)
);

-- Create index for user lookups
CREATE INDEX idx_platform_coverage_user ON platform_coverage(user_id);

-- 3. Create user_activity table - tracks all user activities
CREATE TABLE user_activity (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  activity_type VARCHAR(50) NOT NULL CHECK (activity_type IN (
    'login', 'logout', 'sync_triggered', 'sync_scheduled',
    'settings_changed', 'platform_connected', 'platform_disconnected',
    'api_key_added', 'api_key_removed', 'subscription_changed'
  )),
  platform VARCHAR(50),
  activity_details JSONB DEFAULT '{}',
  ip_address INET,
  user_agent TEXT,
  session_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for activity queries
CREATE INDEX idx_user_activity_user_created ON user_activity(user_id, created_at DESC);
CREATE INDEX idx_user_activity_type ON user_activity(activity_type, created_at DESC);

-- 4. Create sync_analytics table - aggregated analytics data
CREATE TABLE sync_analytics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  period_type VARCHAR(20) NOT NULL CHECK (period_type IN (
    'hourly', 'daily', 'weekly', 'monthly'
  )),
  period_start TIMESTAMP WITH TIME ZONE NOT NULL,
  period_end TIMESTAMP WITH TIME ZONE NOT NULL,
  total_syncs INTEGER DEFAULT 0,
  successful_syncs INTEGER DEFAULT 0,
  failed_syncs INTEGER DEFAULT 0,
  items_created INTEGER DEFAULT 0,
  items_updated INTEGER DEFAULT 0,
  items_deleted INTEGER DEFAULT 0,
  avg_sync_time_ms INTEGER DEFAULT 0,
  platform_breakdown JSONB DEFAULT '{}',
  error_breakdown JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, period_type, period_start)
);

-- Create indexes for analytics queries
CREATE INDEX idx_sync_analytics_user_period ON sync_analytics(user_id, period_type, period_start DESC);

-- 5. Create helper function to update platform coverage
CREATE OR REPLACE FUNCTION update_platform_coverage()
RETURNS TRIGGER AS $$
BEGIN
  -- Update platform coverage when sync events are recorded
  IF NEW.event_type IN ('sync_completed', 'sync_failed') THEN
    INSERT INTO platform_coverage (
      user_id, 
      platform, 
      is_connected, 
      first_connected_at,
      last_active_at, 
      total_synced_items,
      total_failed_items
    )
    VALUES (
      NEW.user_id, 
      NEW.platform, 
      true,
      NOW(),
      NOW(), 
      CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
      CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END
    )
    ON CONFLICT (user_id, platform) 
    DO UPDATE SET
      last_active_at = NOW(),
      total_synced_items = platform_coverage.total_synced_items + 
        CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
      total_failed_items = platform_coverage.total_failed_items + 
        CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
      sync_success_rate = CASE 
        WHEN (platform_coverage.total_synced_items + platform_coverage.total_failed_items) > 0 
        THEN ROUND(
          (platform_coverage.total_synced_items::numeric / 
          (platform_coverage.total_synced_items + platform_coverage.total_failed_items)) * 100, 
          2
        )
        ELSE 0.00
      END,
      updated_at = NOW();
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic platform coverage updates
CREATE TRIGGER trigger_update_coverage
AFTER INSERT ON sync_events
FOR EACH ROW EXECUTE FUNCTION update_platform_coverage();

-- 6. Create function to record user activity
CREATE OR REPLACE FUNCTION record_activity(
  p_user_id UUID,
  p_activity_type VARCHAR(50),
  p_platform VARCHAR(50) DEFAULT NULL,
  p_details JSONB DEFAULT '{}',
  p_ip_address INET DEFAULT NULL,
  p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  v_activity_id UUID;
BEGIN
  INSERT INTO user_activity (
    user_id,
    activity_type,
    platform,
    activity_details,
    ip_address,
    user_agent
  ) VALUES (
    p_user_id,
    p_activity_type,
    p_platform,
    p_details,
    p_ip_address,
    p_user_agent
  ) RETURNING id INTO v_activity_id;
  
  RETURN v_activity_id;
END;
$$ LANGUAGE plpgsql;

-- 7. Create function to get recent sync activity
CREATE OR REPLACE FUNCTION get_recent_sync_activity(
  p_user_id UUID,
  p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
  event_id UUID,
  event_type VARCHAR(50),
  platform VARCHAR(50),
  item_title TEXT,
  status VARCHAR(20),
  created_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    id,
    sync_events.event_type,
    sync_events.platform,
    sync_events.item_title,
    sync_events.status,
    sync_events.created_at,
    sync_events.error_message
  FROM sync_events
  WHERE user_id = p_user_id
  ORDER BY created_at DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 8. Create view for platform sync summary
CREATE OR REPLACE VIEW platform_sync_summary AS
SELECT 
  pc.user_id,
  pc.platform,
  pc.is_connected,
  pc.last_active_at,
  pc.sync_success_rate,
  pc.total_synced_items,
  pc.total_failed_items,
  COUNT(DISTINCT se.sync_job_id) as total_sync_sessions,
  MAX(se.created_at) as last_sync_event
FROM platform_coverage pc
LEFT JOIN sync_events se ON pc.user_id = se.user_id AND pc.platform = se.platform
GROUP BY 
  pc.user_id, pc.platform, pc.is_connected, 
  pc.last_active_at, pc.sync_success_rate, 
  pc.total_synced_items, pc.total_failed_items;

-- 9. Enable Row Level Security (RLS)
ALTER TABLE sync_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_coverage ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_analytics ENABLE ROW LEVEL SECURITY;

-- 10. Create RLS policies
-- Users can only see their own data
CREATE POLICY "Users can view own sync events" ON sync_events
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own platform coverage" ON platform_coverage
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own activity" ON user_activity
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own analytics" ON sync_analytics
  FOR ALL USING (auth.uid() = user_id);

-- 11. Grant permissions for the view
GRANT SELECT ON platform_sync_summary TO authenticated;

-- Migration complete message
DO $$
BEGIN
  RAISE NOTICE 'Sync tracking tables created successfully!';
END $$;