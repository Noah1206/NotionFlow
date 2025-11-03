-- ============================================
-- 🚀 NodeFlow Master Database Schema
-- Consolidated schema file combining all table definitions
-- and common functions to eliminate duplication
-- ============================================

-- ============================================
-- 🔧 EXTENSIONS & COMMON FUNCTIONS
-- ============================================

-- Enable required extensions (centralized)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Common updated_at trigger function (single definition for all tables)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- 📊 USER MANAGEMENT TABLES
-- ============================================

-- Users table (central user management)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles for personalized dashboard URLs
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    username VARCHAR(20) UNIQUE NOT NULL,
    display_name VARCHAR(50),
    avatar_url TEXT,
    bio TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Username format validation: 3-20 characters, alphanumeric + underscore
    CONSTRAINT username_format CHECK (username ~ '^[a-zA-Z0-9_]{3,20}$'),
    
    -- Reserved usernames protection
    CONSTRAINT no_reserved_usernames CHECK (username NOT IN (
        'admin', 'api', 'www', 'dashboard', 'login', 'signup', 'logout',
        'settings', 'profile', 'help', 'support', 'about', 'contact',
        'privacy', 'terms', 'legal', 'pricing', 'billing', 'payment',
        'app', 'mobile', 'desktop', 'web', 'ios', 'android',
        'notionflow', 'notion', 'flow', 'calendar', 'schedule',
        'root', 'system', 'config', 'static', 'assets', 'public'
    ))
);

-- ============================================
-- 🗓️ CALENDAR SYSTEM TABLES
-- ============================================

-- Calendars table with media file support
CREATE TABLE IF NOT EXISTS calendars (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL, -- Changed to TEXT to match current session user_id
    
    -- Calendar basic information  
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#2563eb',
    platform VARCHAR(50) DEFAULT 'custom', -- custom, notion, google, apple, outlook
    is_shared BOOLEAN DEFAULT false,
    
    -- Current JSON structure fields
    event_count INTEGER DEFAULT 0,
    sync_status VARCHAR(20) DEFAULT 'synced', -- synced, syncing, error, active
    last_sync_display TEXT DEFAULT 'Just now',
    is_enabled BOOLEAN DEFAULT true,
    shared_with_count INTEGER DEFAULT 0,
    
    -- Media file information
    media_filename VARCHAR(255) DEFAULT NULL,
    media_file_path VARCHAR(500) DEFAULT NULL,
    media_file_type VARCHAR(20) DEFAULT NULL, -- 'audio' or 'video'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint for user + calendar name
    CONSTRAINT calendars_user_name_unique UNIQUE (user_id, name)
);

-- ============================================
-- 🔐 API & SECURITY TABLES
-- ============================================

-- API keys storage with encryption
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL, -- google, outlook, notion, zoom, slack, etc.
    key_name VARCHAR(100) NOT NULL,
    encrypted_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT api_keys_user_platform_name_unique UNIQUE (user_id, platform, key_name)
);

-- ============================================
-- 💳 PAYMENT & BILLING TABLES
-- ============================================

-- Payment subscriptions
CREATE TABLE IF NOT EXISTS payment_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    plan_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, canceled, past_due, etc.
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 📈 ANALYTICS & TRACKING TABLES
-- ============================================

-- User visits tracking
CREATE TABLE IF NOT EXISTS user_visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    session_id TEXT,
    page_path TEXT NOT NULL,
    user_agent TEXT,
    ip_address INET,
    referrer TEXT,
    visit_duration INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Smart detection cache for performance
CREATE TABLE IF NOT EXISTS smart_detection_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_data JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced features tracking
CREATE TABLE IF NOT EXISTS enhanced_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    feature_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT enhanced_features_user_feature_unique UNIQUE (user_id, feature_name)
);

-- ============================================
-- 📊 INDEXES (Performance Optimization)
-- ============================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- User profiles indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- Calendars indexes
CREATE INDEX IF NOT EXISTS idx_calendars_user_id ON calendars(user_id);
CREATE INDEX IF NOT EXISTS idx_calendars_platform ON calendars(platform);
CREATE INDEX IF NOT EXISTS idx_calendars_sync_status ON calendars(sync_status);
CREATE INDEX IF NOT EXISTS idx_calendars_created_at ON calendars(created_at);
CREATE INDEX IF NOT EXISTS idx_calendars_media_file_path ON calendars(media_file_path);

-- API keys indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_platform ON api_keys(platform);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- Payment indexes
CREATE INDEX IF NOT EXISTS idx_payment_subscriptions_user_id ON payment_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_subscriptions_stripe_customer_id ON payment_subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_subscriptions_status ON payment_subscriptions(status);

-- Visits indexes
CREATE INDEX IF NOT EXISTS idx_user_visits_user_id ON user_visits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_visits_created_at ON user_visits(created_at);
CREATE INDEX IF NOT EXISTS idx_user_visits_page_path ON user_visits(page_path);

-- Enhanced features indexes
CREATE INDEX IF NOT EXISTS idx_enhanced_features_user_id ON enhanced_features(user_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_features_feature_name ON enhanced_features(feature_name);

-- Cache indexes
CREATE INDEX IF NOT EXISTS idx_smart_detection_cache_key ON smart_detection_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_smart_detection_cache_expires_at ON smart_detection_cache(expires_at);

-- ============================================
-- 🔐 ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendars ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE enhanced_features ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view own record" ON users
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own record" ON users
    FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own record" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- User profiles policies
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Calendars policies
CREATE POLICY "Users can view their own calendars" ON calendars
    FOR SELECT USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert their own calendars" ON calendars
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update their own calendars" ON calendars
    FOR UPDATE USING (user_id = auth.uid()::text);
CREATE POLICY "Users can delete their own calendars" ON calendars
    FOR DELETE USING (user_id = auth.uid()::text);
CREATE POLICY "Users can view shared calendars" ON calendars
    FOR SELECT USING (is_shared = true);

-- API keys policies
CREATE POLICY "Users can manage their own API keys" ON api_keys
    FOR ALL USING (user_id = auth.uid()::text);

-- Payment subscriptions policies
CREATE POLICY "Users can view their own subscriptions" ON payment_subscriptions
    FOR SELECT USING (user_id = auth.uid()::text);

-- Enhanced features policies
CREATE POLICY "Users can manage their own features" ON enhanced_features
    FOR ALL USING (user_id = auth.uid()::text);

-- Service role policies (for backend operations)
CREATE POLICY "Service role full access users" ON users
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access profiles" ON user_profiles
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access calendars" ON calendars
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access api_keys" ON api_keys
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access payments" ON payment_subscriptions
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access visits" ON user_visits
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access features" ON enhanced_features
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- 🔄 TRIGGERS (Auto-update timestamps)
-- ============================================

-- Apply updated_at triggers to all relevant tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calendars_updated_at
    BEFORE UPDATE ON calendars
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_subscriptions_updated_at
    BEFORE UPDATE ON payment_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_enhanced_features_updated_at
    BEFORE UPDATE ON enhanced_features
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 🔧 UTILITY FUNCTIONS
-- ============================================

-- Function to create default calendar for new users
CREATE OR REPLACE FUNCTION create_default_calendar_for_user(p_user_id TEXT)
RETURNS UUID AS $$
DECLARE
    calendar_id UUID;
BEGIN
    INSERT INTO calendars (
        user_id, name, platform, color, event_count, 
        sync_status, last_sync_display, is_enabled
    ) VALUES (
        p_user_id, 'My Calendar', 'custom', '#2563eb', 0,
        'synced', 'Just now', TRUE
    ) RETURNING id INTO calendar_id;
    
    RETURN calendar_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to handle user creation with profile
CREATE OR REPLACE FUNCTION create_user_with_profile(
    p_user_id UUID,
    p_email TEXT,
    p_username TEXT DEFAULT NULL,
    p_display_name TEXT DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Insert into users table
    INSERT INTO users (id, email, created_at)
    VALUES (p_user_id, p_email, NOW())
    ON CONFLICT (id) DO NOTHING;
    
    -- Insert into user_profiles table
    INSERT INTO user_profiles (user_id, username, display_name, created_at)
    VALUES (
        p_user_id, 
        COALESCE(p_username, SPLIT_PART(p_email, '@', 1)),
        COALESCE(p_display_name, SPLIT_PART(p_email, '@', 1)),
        NOW()
    )
    ON CONFLICT (user_id) DO NOTHING;
    
    -- Create default calendar
    PERFORM create_default_calendar_for_user(p_user_id::text);
END;
$$;

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
        id, user_id, name, color, platform, is_shared, event_count,
        sync_status, last_sync_display, is_enabled, shared_with_count, created_at
    ) VALUES (
        calendar_uuid, p_user_id, p_calendar_data->>'name',
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

-- ============================================
-- 📝 TABLE COMMENTS (Documentation)
-- ============================================

COMMENT ON TABLE users IS 'Central user management table';
COMMENT ON TABLE user_profiles IS 'User profiles for personalized dashboard URLs';
COMMENT ON TABLE calendars IS 'User calendars with media file support';
COMMENT ON TABLE api_keys IS 'Encrypted API keys for external platform integrations';
COMMENT ON TABLE payment_subscriptions IS 'User payment and subscription information';
COMMENT ON TABLE user_visits IS 'User visit tracking for analytics';
COMMENT ON TABLE smart_detection_cache IS 'Performance cache for smart detection features';
COMMENT ON TABLE enhanced_features IS 'Enhanced features usage tracking';

-- Grant necessary permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;

-- ============================================
-- 🎉 SCHEMA SETUP COMPLETE
-- ============================================