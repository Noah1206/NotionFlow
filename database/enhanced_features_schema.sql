-- Enhanced Features Database Schema for NotionFlow
-- Supports calendar creation, community sharing, AI notifications, and friend management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 📅 Calendars table
CREATE TABLE IF NOT EXISTS calendars (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(20) NOT NULL CHECK (type IN ('personal', 'community')),
    owner_id VARCHAR(255) NOT NULL,
    public_access BOOLEAN DEFAULT FALSE,
    allow_editing BOOLEAN DEFAULT FALSE,
    share_token VARCHAR(32) UNIQUE,
    icon VARCHAR(10) DEFAULT '📅',
    color VARCHAR(7) DEFAULT '#3b82f6',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    
    -- Indexes
    CONSTRAINT calendars_owner_id_idx FOREIGN KEY (owner_id) REFERENCES user_profiles(user_id)
);

-- Index for calendars
CREATE INDEX IF NOT EXISTS idx_calendars_owner_id ON calendars(owner_id);
CREATE INDEX IF NOT EXISTS idx_calendars_type ON calendars(type);
CREATE INDEX IF NOT EXISTS idx_calendars_share_token ON calendars(share_token);
CREATE INDEX IF NOT EXISTS idx_calendars_public_access ON calendars(public_access);

-- 🔗 Calendar shares table (for community calendars)
CREATE TABLE IF NOT EXISTS calendar_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calendar_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    access_level VARCHAR(20) NOT NULL DEFAULT 'view' CHECK (access_level IN ('view', 'edit', 'admin')),
    shared_by VARCHAR(255),
    shared_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Foreign keys
    CONSTRAINT fk_calendar_shares_calendar FOREIGN KEY (calendar_id) REFERENCES calendars(id) ON DELETE CASCADE,
    CONSTRAINT fk_calendar_shares_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_calendar_shares_shared_by FOREIGN KEY (shared_by) REFERENCES user_profiles(user_id),
    
    -- Unique constraint to prevent duplicate shares
    UNIQUE(calendar_id, user_id)
);

-- Index for calendar shares
CREATE INDEX IF NOT EXISTS idx_calendar_shares_calendar_id ON calendar_shares(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_shares_user_id ON calendar_shares(user_id);

-- 📝 Calendar events table (enhanced)
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calendar_id UUID NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    all_day BOOLEAN DEFAULT FALSE,
    location VARCHAR(500),
    created_by VARCHAR(255) NOT NULL,
    attendees JSONB DEFAULT '[]',
    recurring_rule VARCHAR(500),
    reminder_settings JSONB DEFAULT '{}',
    external_sync_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Foreign keys
    CONSTRAINT fk_calendar_events_calendar FOREIGN KEY (calendar_id) REFERENCES calendars(id) ON DELETE CASCADE,
    CONSTRAINT fk_calendar_events_created_by FOREIGN KEY (created_by) REFERENCES user_profiles(user_id)
);

-- Index for calendar events
CREATE INDEX IF NOT EXISTS idx_calendar_events_calendar_id ON calendar_events(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_created_by ON calendar_events(created_by);

-- 👥 Friendships table
CREATE TABLE IF NOT EXISTS friendships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    friend_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'blocked', 'declined')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    blocked_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    
    -- Foreign keys
    CONSTRAINT fk_friendships_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_friendships_friend FOREIGN KEY (friend_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Prevent self-friendship and duplicate requests
    CHECK (user_id != friend_id),
    UNIQUE(user_id, friend_id)
);

-- Index for friendships
CREATE INDEX IF NOT EXISTS idx_friendships_user_id ON friendships(user_id);
CREATE INDEX IF NOT EXISTS idx_friendships_friend_id ON friendships(friend_id);
CREATE INDEX IF NOT EXISTS idx_friendships_status ON friendships(status);

-- 📬 AI Notifications table (Premium feature)
CREATE TABLE IF NOT EXISTS ai_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    source_platform VARCHAR(50) NOT NULL CHECK (source_platform IN ('kakao', 'email', 'slack', 'teams', 'discord', 'telegram')),
    original_message TEXT NOT NULL,
    ai_summary TEXT,
    ai_analysis JSONB DEFAULT '{}',
    priority_level VARCHAR(20) DEFAULT 'medium' CHECK (priority_level IN ('low', 'medium', 'high', 'urgent')),
    tags TEXT[] DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key
    CONSTRAINT fk_ai_notifications_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- Index for AI notifications
CREATE INDEX IF NOT EXISTS idx_ai_notifications_user_id ON ai_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_notifications_is_read ON ai_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_ai_notifications_priority ON ai_notifications(priority_level);
CREATE INDEX IF NOT EXISTS idx_ai_notifications_source ON ai_notifications(source_platform);
CREATE INDEX IF NOT EXISTS idx_ai_notifications_created_at ON ai_notifications(created_at);

-- 💰 User subscriptions table (Premium features)
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('free', 'premium', 'pro', 'enterprise')),
    billing_cycle VARCHAR(20) DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'yearly')),
    price_cents INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    stripe_subscription_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'past_due', 'unpaid')),
    current_period_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    current_period_end TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    features JSONB DEFAULT '{}',
    
    -- Foreign key
    CONSTRAINT fk_user_subscriptions_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- Index for user subscriptions
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_type ON user_subscriptions(plan_type);

-- 🔔 Notification preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    ai_processing_enabled BOOLEAN DEFAULT FALSE,
    ai_summary_threshold VARCHAR(20) DEFAULT 'medium' CHECK (ai_summary_threshold IN ('low', 'medium', 'high')),
    source_platforms JSONB DEFAULT '{"kakao": false, "email": true, "slack": false}',
    notification_schedule JSONB DEFAULT '{"start_hour": 9, "end_hour": 18, "timezone": "UTC"}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key
    CONSTRAINT fk_notification_preferences_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Unique constraint
    UNIQUE(user_id)
);

-- Index for notification preferences
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences(user_id);

-- 📊 User activity log table
CREATE TABLE IF NOT EXISTS user_activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key
    CONSTRAINT fk_user_activity_log_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- Index for user activity log
CREATE INDEX IF NOT EXISTS idx_user_activity_log_user_id ON user_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_activity_type ON user_activity_log(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_created_at ON user_activity_log(created_at);

-- 🏷️ Tags table for organizing content
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#3b82f6',
    user_id VARCHAR(255) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key
    CONSTRAINT fk_tags_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Unique constraint
    UNIQUE(name, user_id)
);

-- Index for tags
CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- 🔗 Calendar event tags relationship
CREATE TABLE IF NOT EXISTS calendar_event_tags (
    calendar_event_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign keys
    CONSTRAINT fk_calendar_event_tags_event FOREIGN KEY (calendar_event_id) REFERENCES calendar_events(id) ON DELETE CASCADE,
    CONSTRAINT fk_calendar_event_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    
    -- Primary key
    PRIMARY KEY (calendar_event_id, tag_id)
);

-- 📈 Feature usage analytics
CREATE TABLE IF NOT EXISTS feature_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 1,
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key
    CONSTRAINT fk_feature_usage_user FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Unique constraint
    UNIQUE(user_id, feature_name)
);

-- Index for feature usage
CREATE INDEX IF NOT EXISTS idx_feature_usage_user_id ON feature_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_feature_name ON feature_usage(feature_name);

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
CREATE TRIGGER update_calendars_updated_at BEFORE UPDATE ON calendars FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_calendar_events_updated_at BEFORE UPDATE ON calendar_events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_preferences_updated_at BEFORE UPDATE ON notification_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to increment tag usage count
CREATE OR REPLACE FUNCTION increment_tag_usage()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE tags SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for tag usage
CREATE TRIGGER increment_tag_usage_trigger AFTER INSERT ON calendar_event_tags FOR EACH ROW EXECUTE FUNCTION increment_tag_usage();

-- Function to update feature usage
CREATE OR REPLACE FUNCTION update_feature_usage(p_user_id VARCHAR(255), p_feature_name VARCHAR(100))
RETURNS VOID AS $$
BEGIN
    INSERT INTO feature_usage (user_id, feature_name, usage_count, last_used_at)
    VALUES (p_user_id, p_feature_name, 1, NOW())
    ON CONFLICT (user_id, feature_name)
    DO UPDATE SET
        usage_count = feature_usage.usage_count + 1,
        last_used_at = NOW();
END;
$$ language 'plpgsql';

-- 📝 Insert default data

-- Insert default notification preferences for existing users
INSERT INTO notification_preferences (user_id, email_notifications, push_notifications, ai_processing_enabled)
SELECT user_id, TRUE, TRUE, FALSE
FROM user_profiles
WHERE user_id NOT IN (SELECT user_id FROM notification_preferences)
ON CONFLICT (user_id) DO NOTHING;

-- Insert default free subscription for existing users
INSERT INTO user_subscriptions (user_id, plan_type, price_cents, current_period_start, current_period_end)
SELECT user_id, 'free', 0, NOW(), NOW() + INTERVAL '1 year'
FROM user_profiles
WHERE user_id NOT IN (SELECT user_id FROM user_subscriptions WHERE is_active = TRUE)
ON CONFLICT DO NOTHING;

-- 📊 Views for easier querying

-- View for user calendar access (personal + shared)
CREATE OR REPLACE VIEW user_calendar_access AS
SELECT 
    c.id as calendar_id,
    c.name,
    c.description,
    c.type,
    c.owner_id,
    c.public_access,
    c.allow_editing,
    c.created_at,
    u.user_id,
    CASE 
        WHEN c.owner_id = u.user_id THEN 'owner'
        WHEN cs.access_level IS NOT NULL THEN cs.access_level
        WHEN c.public_access = TRUE THEN 'view'
        ELSE NULL
    END as access_level
FROM calendars c
CROSS JOIN user_profiles u
LEFT JOIN calendar_shares cs ON c.id = cs.calendar_id AND cs.user_id = u.user_id AND cs.is_active = TRUE
WHERE 
    c.is_active = TRUE 
    AND (
        c.owner_id = u.user_id 
        OR (cs.user_id IS NOT NULL AND cs.is_active = TRUE)
        OR c.public_access = TRUE
    );

-- View for friendship status
CREATE OR REPLACE VIEW friendship_status AS
SELECT 
    f1.user_id,
    f1.friend_id,
    f1.status,
    f1.created_at,
    f1.accepted_at,
    CASE 
        WHEN f1.status = 'accepted' AND f2.status = 'accepted' THEN 'mutual'
        WHEN f1.status = 'pending' THEN 'sent_request'
        WHEN f2.status = 'pending' THEN 'received_request'
        ELSE f1.status
    END as friendship_type
FROM friendships f1
LEFT JOIN friendships f2 ON f1.user_id = f2.friend_id AND f1.friend_id = f2.user_id;

-- 🔍 Sample queries for testing

-- Get all calendars accessible to a user
-- SELECT * FROM user_calendar_access WHERE user_id = 'your_user_id';

-- Get mutual friends
-- SELECT * FROM friendship_status WHERE user_id = 'your_user_id' AND friendship_type = 'mutual';

-- Get AI notifications summary
-- SELECT priority_level, COUNT(*) as count FROM ai_notifications WHERE user_id = 'your_user_id' AND is_read = FALSE GROUP BY priority_level;

COMMENT ON TABLE calendars IS 'Stores personal and community calendars';
COMMENT ON TABLE calendar_shares IS 'Manages sharing permissions for community calendars';
COMMENT ON TABLE calendar_events IS 'Stores calendar events with enhanced features';
COMMENT ON TABLE friendships IS 'Manages user friendships and requests';
COMMENT ON TABLE ai_notifications IS 'AI-processed notifications (Premium feature)';
COMMENT ON TABLE user_subscriptions IS 'User subscription and billing information';
COMMENT ON TABLE notification_preferences IS 'User notification preferences and AI settings';
COMMENT ON TABLE user_activity_log IS 'Tracks user activities for analytics';
COMMENT ON TABLE tags IS 'User-defined tags for organizing content';
COMMENT ON TABLE feature_usage IS 'Tracks feature usage for analytics';