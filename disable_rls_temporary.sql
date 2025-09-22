-- Temporary solution: Disable RLS for calendar_sync_configs
-- This is less secure but will immediately fix the OAuth token storage issue
-- You can re-enable RLS later with proper policies

-- Disable RLS for calendar_sync_configs table
ALTER TABLE calendar_sync_configs DISABLE ROW LEVEL SECURITY;

-- Verify RLS is disabled
SELECT 
  schemaname, 
  tablename, 
  rowsecurity
FROM pg_tables 
WHERE tablename = 'calendar_sync_configs';

-- To re-enable later (after fixing policies):
-- ALTER TABLE calendar_sync_configs ENABLE ROW LEVEL SECURITY;