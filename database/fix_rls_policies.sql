-- Fix RLS policies for users and user_profiles tables
-- Run this in Supabase SQL Editor

-- 1. Disable RLS temporarily to fix the issue
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;

-- 2. Drop existing problematic policies
DROP POLICY IF EXISTS "Users can insert their own record" ON users;
DROP POLICY IF EXISTS "Users can view their own record" ON users;
DROP POLICY IF EXISTS "Users can update their own record" ON users;

DROP POLICY IF EXISTS "Users can insert their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can view their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON user_profiles;

-- 3. Create new, more permissive policies for users table
CREATE POLICY "Enable insert for authenticated users only" ON users
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = id);

CREATE POLICY "Enable select for users based on user_id" ON users
FOR SELECT TO authenticated
USING (auth.uid() = id);

CREATE POLICY "Enable update for users based on user_id" ON users
FOR UPDATE TO authenticated
USING (auth.uid() = id);

-- 4. Create policies for user_profiles table
CREATE POLICY "Enable insert for authenticated users only" ON user_profiles
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Enable select for users based on user_id" ON user_profiles
FOR SELECT TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Enable update for users based on user_id" ON user_profiles
FOR UPDATE TO authenticated
USING (auth.uid() = user_id);

-- 5. Allow service role to bypass RLS (for backend operations)
CREATE POLICY "Service role can do anything" ON users
FOR ALL TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role can do anything" ON user_profiles
FOR ALL TO service_role
USING (true)
WITH CHECK (true);

-- 6. Re-enable RLS with new policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 7. Create function to handle user creation with proper permissions
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
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION create_user_with_profile TO authenticated;
GRANT EXECUTE ON FUNCTION create_user_with_profile TO service_role;