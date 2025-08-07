-- 🔑 API Keys & Platform Integration Schema for NotionFlow
-- Secure storage and management of external platform credentials

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 🔐 Calendar sync configurations table
CREATE TABLE IF NOT EXISTS calendar_sync_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('notion', 'google', 'outlook', 'apple', 'slack')),
    
    -- Encrypted credential storage
    credentials JSONB NOT NULL,
    encrypted_credentials TEXT, -- AES-256 encrypted backup
    
    -- Platform-specific settings
    credential_type VARCHAR(20) NOT NULL CHECK (credential_type IN ('api_key', 'oauth', 'webhook_url', 'caldav')),
    oauth_tokens JSONB DEFAULT '{}', -- For OAuth platforms
    
    -- Sync configuration
    is_enabled BOOLEAN DEFAULT TRUE,
    sync_frequency_minutes INTEGER DEFAULT 15,
    last_sync_at TIMESTAMPTZ,
    next_sync_at TIMESTAMPTZ,
    
    -- Health monitoring
    consecutive_failures INTEGER DEFAULT 0,
    last_error_message TEXT,
    last_error_at TIMESTAMPTZ,
    health_status VARCHAR(20) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'warning', 'error', 'disabled', 'unknown')),
    
    -- Connection validation
    connection_tested_at TIMESTAMPTZ,
    connection_test_result JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_user_platform UNIQUE(user_id, platform),
    CONSTRAINT fk_calendar_sync_configs_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- Indexes for calendar_sync_configs
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_user_id ON calendar_sync_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_platform ON calendar_sync_configs(platform);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_enabled ON calendar_sync_configs(is_enabled);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_health ON calendar_sync_configs(health_status);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_next_sync ON calendar_sync_configs(next_sync_at);

-- 📊 Platform sync history table
CREATE TABLE IF NOT EXISTS platform_sync_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID NOT NULL,
    user_id TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    
    -- Sync details
    sync_type VARCHAR(20) DEFAULT 'scheduled' CHECK (sync_type IN ('manual', 'scheduled', 'webhook', 'test')),
    sync_direction VARCHAR(20) DEFAULT 'bidirectional' CHECK (sync_direction IN ('import', 'export', 'bidirectional')),
    
    -- Results
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'partial', 'failed', 'cancelled')),
    events_imported INTEGER DEFAULT 0,
    events_exported INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    events_deleted INTEGER DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    
    -- Performance metrics
    duration_ms INTEGER,
    memory_usage_mb DECIMAL(8,2),
    
    -- Metadata
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Foreign keys
    CONSTRAINT fk_platform_sync_history_config FOREIGN KEY (config_id) REFERENCES calendar_sync_configs(id) ON DELETE CASCADE,
    CONSTRAINT fk_platform_sync_history_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- Indexes for platform_sync_history
CREATE INDEX IF NOT EXISTS idx_platform_sync_history_config_id ON platform_sync_history(config_id);
CREATE INDEX IF NOT EXISTS idx_platform_sync_history_user_id ON platform_sync_history(user_id);
CREATE INDEX IF NOT EXISTS idx_platform_sync_history_platform ON platform_sync_history(platform);
CREATE INDEX IF NOT EXISTS idx_platform_sync_history_status ON platform_sync_history(status);
CREATE INDEX IF NOT EXISTS idx_platform_sync_history_started_at ON platform_sync_history(started_at);

-- 🔔 Webhook subscriptions table (for real-time sync)
CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID NOT NULL,
    user_id TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    
    -- Webhook details
    webhook_url TEXT NOT NULL,
    webhook_secret TEXT,
    external_subscription_id TEXT, -- Platform-specific subscription ID
    
    -- Event filters
    event_types TEXT[] DEFAULT '{}', -- Which events to listen for
    resource_filters JSONB DEFAULT '{}', -- Additional filtering criteria
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_received_at TIMESTAMPTZ,
    total_events_received INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    -- Foreign keys
    CONSTRAINT fk_webhook_subscriptions_config FOREIGN KEY (config_id) REFERENCES calendar_sync_configs(id) ON DELETE CASCADE,
    CONSTRAINT fk_webhook_subscriptions_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Unique constraint
    UNIQUE(config_id, external_subscription_id)
);

-- Indexes for webhook_subscriptions
CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_config_id ON webhook_subscriptions(config_id);
CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_platform ON webhook_subscriptions(platform);
CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_active ON webhook_subscriptions(is_active);
CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_expires_at ON webhook_subscriptions(expires_at);

-- 🔧 Functions and Triggers

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_calendar_sync_configs_updated_at 
    BEFORE UPDATE ON calendar_sync_configs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_webhook_subscriptions_updated_at 
    BEFORE UPDATE ON webhook_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate next sync time
CREATE OR REPLACE FUNCTION calculate_next_sync(p_config_id UUID)
RETURNS VOID AS $$
DECLARE
    v_frequency INTEGER;
BEGIN
    SELECT sync_frequency_minutes INTO v_frequency
    FROM calendar_sync_configs
    WHERE id = p_config_id;
    
    UPDATE calendar_sync_configs
    SET next_sync_at = NOW() + (v_frequency || ' minutes')::INTERVAL
    WHERE id = p_config_id;
END;
$$ language 'plpgsql';

-- Function to record sync attempt
CREATE OR REPLACE FUNCTION record_sync_attempt(
    p_config_id UUID,
    p_status VARCHAR(20),
    p_error_message TEXT DEFAULT NULL,
    p_events_count INTEGER DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    -- Update config status
    UPDATE calendar_sync_configs
    SET 
        last_sync_at = NOW(),
        consecutive_failures = CASE 
            WHEN p_status = 'success' THEN 0
            ELSE consecutive_failures + 1
        END,
        health_status = CASE
            WHEN p_status = 'success' THEN 'healthy'
            WHEN consecutive_failures >= 3 THEN 'error'
            ELSE 'warning'
        END,
        last_error_message = CASE 
            WHEN p_status != 'success' THEN p_error_message
            ELSE NULL
        END,
        last_error_at = CASE 
            WHEN p_status != 'success' THEN NOW()
            ELSE last_error_at
        END
    WHERE id = p_config_id;
    
    -- Calculate next sync time
    PERFORM calculate_next_sync(p_config_id);
END;
$$ language 'plpgsql';

-- 📝 Views for easier querying

-- View for active sync configurations
CREATE OR REPLACE VIEW active_sync_configs AS
SELECT 
    csc.*,
    up.username,
    up.display_name,
    EXTRACT(EPOCH FROM (next_sync_at - NOW()))/60 as minutes_until_next_sync,
    CASE 
        WHEN consecutive_failures = 0 THEN 'Healthy'
        WHEN consecutive_failures < 3 THEN 'Warning (' || consecutive_failures || ' failures)'
        ELSE 'Error (' || consecutive_failures || ' failures)'
    END as health_display
FROM calendar_sync_configs csc
LEFT JOIN user_profiles up ON csc.user_id = up.user_id
WHERE csc.is_enabled = TRUE
ORDER BY csc.next_sync_at ASC;

-- View for sync statistics
CREATE OR REPLACE VIEW sync_statistics AS
SELECT 
    csc.user_id,
    csc.platform,
    COUNT(psh.id) as total_syncs,
    COUNT(CASE WHEN psh.status = 'success' THEN 1 END) as successful_syncs,
    COUNT(CASE WHEN psh.status = 'failed' THEN 1 END) as failed_syncs,
    AVG(psh.duration_ms) as avg_duration_ms,
    MAX(psh.started_at) as last_sync_at,
    SUM(psh.events_imported + psh.events_exported + psh.events_updated) as total_events_processed
FROM calendar_sync_configs csc
LEFT JOIN platform_sync_history psh ON csc.id = psh.config_id
WHERE psh.started_at >= NOW() - INTERVAL '30 days'
GROUP BY csc.user_id, csc.platform;

-- 🔍 Sample queries for testing and monitoring

-- Get user's platform configurations
-- SELECT * FROM calendar_sync_configs WHERE user_id = 'your_user_id';

-- Get sync health overview
-- SELECT platform, health_status, COUNT(*) FROM calendar_sync_configs GROUP BY platform, health_status;

-- Get upcoming syncs
-- SELECT * FROM active_sync_configs WHERE minutes_until_next_sync < 60;

-- Get sync performance metrics
-- SELECT * FROM sync_statistics WHERE total_syncs > 0 ORDER BY avg_duration_ms DESC;

-- 📋 Comments for documentation
COMMENT ON TABLE calendar_sync_configs IS 'Stores encrypted credentials and sync configuration for external platforms';
COMMENT ON COLUMN calendar_sync_configs.credentials IS 'JSONB storage for platform credentials (encrypted sensitive fields)';
COMMENT ON COLUMN calendar_sync_configs.encrypted_credentials IS 'AES-256 encrypted backup of credentials';
COMMENT ON COLUMN calendar_sync_configs.consecutive_failures IS 'Number of consecutive sync failures (resets on success)';
COMMENT ON COLUMN calendar_sync_configs.health_status IS 'Overall health status based on recent sync attempts';

COMMENT ON TABLE platform_sync_history IS 'Detailed history of all sync attempts with performance metrics';
COMMENT ON COLUMN platform_sync_history.sync_type IS 'Type of sync: manual, scheduled, webhook, or test';
COMMENT ON COLUMN platform_sync_history.sync_direction IS 'Direction of data flow: import, export, or bidirectional';

COMMENT ON TABLE webhook_subscriptions IS 'Real-time webhook subscriptions for supported platforms';
COMMENT ON COLUMN webhook_subscriptions.external_subscription_id IS 'Platform-specific subscription identifier';
COMMENT ON COLUMN webhook_subscriptions.event_types IS 'Array of event types to listen for';

-- Row Level Security (RLS) Policies
ALTER TABLE calendar_sync_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_sync_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_subscriptions ENABLE ROW LEVEL SECURITY;

-- Users can only access their own sync configurations
CREATE POLICY calendar_sync_configs_user_access ON calendar_sync_configs
    FOR ALL USING (auth.uid()::text = user_id);

-- Users can only access their own sync history
CREATE POLICY platform_sync_history_user_access ON platform_sync_history
    FOR ALL USING (auth.uid()::text = user_id);

-- Users can only access their own webhook subscriptions
CREATE POLICY webhook_subscriptions_user_access ON webhook_subscriptions
    FOR ALL USING (auth.uid()::text = user_id);