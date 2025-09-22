-- Comprehensive RLS disable script for NotionFlow
-- This disables RLS on all tables that are causing issues

-- Main tables
ALTER TABLE calendar_sync_configs DISABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE platform_coverage DISABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_tokens DISABLE ROW LEVEL SECURITY;
ALTER TABLE calendars DISABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_sync DISABLE ROW LEVEL SECURITY;

-- Additional tables that might have RLS issues
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE platform_connections DISABLE ROW LEVEL SECURITY;
ALTER TABLE sync_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions DISABLE ROW LEVEL SECURITY;

-- Check which tables still have RLS enabled
SELECT 
  schemaname, 
  tablename, 
  rowsecurity
FROM pg_tables 
WHERE schemaname = 'public' 
  AND rowsecurity = true
ORDER BY tablename;

-- If you want to see all tables and their RLS status:
-- SELECT 
--   schemaname, 
--   tablename, 
--   rowsecurity
-- FROM pg_tables 
-- WHERE schemaname = 'public'
-- ORDER BY tablename;