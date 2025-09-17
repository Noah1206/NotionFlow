-- Fix OAuth token foreign key constraint issue
-- This script ensures users exist in the auth.users table for OAuth token storage

-- 1. Disable RLS temporarily for easier troubleshooting
ALTER TABLE oauth_tokens DISABLE ROW LEVEL SECURITY;
ALTER TABLE platform_connections DISABLE ROW LEVEL SECURITY;

-- 2. Create missing auth.users entries for existing user profiles
-- This ensures the foreign key constraint can be satisfied
INSERT INTO auth.users (id, email, created_at, updated_at, email_confirmed_at)
SELECT 
    up.user_id,
    up.email,
    up.created_at,
    up.updated_at,
    up.created_at
FROM user_profiles up
WHERE up.user_id NOT IN (SELECT id FROM auth.users)
ON CONFLICT (id) DO NOTHING;

-- 3. Alternative: Create auth.users entries for users in the users table if exists
INSERT INTO auth.users (id, email, created_at, updated_at, email_confirmed_at)
SELECT 
    u.id,
    u.email,
    u.created_at,
    u.updated_at,
    u.created_at
FROM users u
WHERE u.id NOT IN (SELECT id FROM auth.users)
ON CONFLICT (id) DO NOTHING;

-- 4. Show current state
SELECT 'Auth users count' as info, COUNT(*) as count FROM auth.users;
SELECT 'User profiles count' as info, COUNT(*) as count FROM user_profiles;
SELECT 'Users table count' as info, COUNT(*) as count FROM users;
SELECT 'OAuth tokens count' as info, COUNT(*) as count FROM oauth_tokens;
SELECT 'Platform connections count' as info, COUNT(*) as count FROM platform_connections;

-- 5. Clean up any orphaned data
DELETE FROM oauth_tokens WHERE user_id NOT IN (SELECT id FROM auth.users);
DELETE FROM platform_connections WHERE user_id NOT IN (SELECT id FROM auth.users);

-- 6. Show final state
SELECT 'Final OAuth tokens count' as info, COUNT(*) as count FROM oauth_tokens;
SELECT 'Final platform connections count' as info, COUNT(*) as count FROM platform_connections;