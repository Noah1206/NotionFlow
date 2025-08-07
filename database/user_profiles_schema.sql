-- 🎯 NotionFlow User Profiles Table Schema
-- This table manages user-specific information for personalized dashboard URLs

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- RLS (Row Level Security) policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can only see their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only insert their own profile
CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only delete their own profile
CREATE POLICY "Users can delete own profile" ON user_profiles
    FOR DELETE USING (auth.uid() = user_id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profiles_updated_at();

-- Function to generate username suggestions
CREATE OR REPLACE FUNCTION generate_username_from_email(email_input TEXT)
RETURNS TEXT[] AS $$
DECLARE
    base_username TEXT;
    suggestions TEXT[] := '{}';
    counter INTEGER := 1;
    temp_username TEXT;
BEGIN
    -- Extract base username from email
    base_username := LOWER(SPLIT_PART(email_input, '@', 1));
    base_username := REGEXP_REPLACE(base_username, '[^a-zA-Z0-9]', '_', 'g');
    base_username := TRIM(TRAILING '_' FROM TRIM(LEADING '_' FROM base_username));
    
    -- Ensure minimum length
    IF LENGTH(base_username) < 3 THEN
        base_username := base_username || '_user';
    END IF;
    
    -- Truncate if too long
    IF LENGTH(base_username) > 15 THEN
        base_username := LEFT(base_username, 15);
    END IF;
    
    -- Generate suggestions
    WHILE counter <= 5 LOOP
        IF counter = 1 THEN
            temp_username := base_username;
        ELSE
            temp_username := base_username || '_' || counter::TEXT;
        END IF;
        
        -- Check if username is available and not reserved
        IF NOT EXISTS (SELECT 1 FROM user_profiles WHERE username = temp_username) AND
           temp_username !~ ANY(ARRAY[
               'admin', 'api', 'www', 'dashboard', 'login', 'signup', 'logout',
               'settings', 'profile', 'help', 'support', 'about', 'contact'
           ]) THEN
            suggestions := array_append(suggestions, temp_username);
        END IF;
        
        counter := counter + 1;
    END LOOP;
    
    RETURN suggestions;
END;
$$ LANGUAGE plpgsql;

-- Function to check username availability
CREATE OR REPLACE FUNCTION is_username_available(username_input TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check format
    IF username_input !~ '^[a-zA-Z0-9_]{3,20}$' THEN
        RETURN FALSE;
    END IF;
    
    -- Check if already exists
    IF EXISTS (SELECT 1 FROM user_profiles WHERE username = LOWER(username_input)) THEN
        RETURN FALSE;
    END IF;
    
    -- Check reserved usernames
    IF LOWER(username_input) = ANY(ARRAY[
        'admin', 'api', 'www', 'dashboard', 'login', 'signup', 'logout',
        'settings', 'profile', 'help', 'support', 'about', 'contact',
        'privacy', 'terms', 'legal', 'pricing', 'billing', 'payment',
        'app', 'mobile', 'desktop', 'web', 'ios', 'android',
        'notionflow', 'notion', 'flow', 'calendar', 'schedule',
        'root', 'system', 'config', 'static', 'assets', 'public'
    ]) THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;