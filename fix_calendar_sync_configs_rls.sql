-- Fix RLS policies for calendar_sync_configs table
-- This allows users to read/write their own sync configurations

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can read own sync configs" ON calendar_sync_configs;
DROP POLICY IF EXISTS "Users can insert own sync configs" ON calendar_sync_configs;
DROP POLICY IF EXISTS "Users can update own sync configs" ON calendar_sync_configs;
DROP POLICY IF EXISTS "Users can delete own sync configs" ON calendar_sync_configs;

-- Create new policies that work with OAuth flows
-- Allow users to read their own sync configs
CREATE POLICY "Users can read own sync configs" ON calendar_sync_configs
  FOR SELECT
  USING (
    user_id = auth.uid()::text 
    OR user_id = (auth.jwt() ->> 'sub')::text
    OR user_id = auth.uid()::text
  );

-- Allow users to insert their own sync configs  
CREATE POLICY "Users can insert own sync configs" ON calendar_sync_configs
  FOR INSERT
  WITH CHECK (
    user_id = auth.uid()::text 
    OR user_id = (auth.jwt() ->> 'sub')::text
    OR user_id = auth.uid()::text
  );

-- Allow users to update their own sync configs
CREATE POLICY "Users can update own sync configs" ON calendar_sync_configs
  FOR UPDATE
  USING (
    user_id = auth.uid()::text 
    OR user_id = (auth.jwt() ->> 'sub')::text
    OR user_id = auth.uid()::text
  )
  WITH CHECK (
    user_id = auth.uid()::text 
    OR user_id = (auth.jwt() ->> 'sub')::text
    OR user_id = auth.uid()::text
  );

-- Allow users to delete their own sync configs
CREATE POLICY "Users can delete own sync configs" ON calendar_sync_configs
  FOR DELETE
  USING (
    user_id = auth.uid()::text 
    OR user_id = (auth.jwt() ->> 'sub')::text
    OR user_id = auth.uid()::text
  );

-- Alternative: Temporarily disable RLS for OAuth flows (less secure but simpler)
-- Uncomment the line below if the above policies don't work
-- ALTER TABLE calendar_sync_configs DISABLE ROW LEVEL SECURITY;

-- Check current policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies 
WHERE tablename = 'calendar_sync_configs';

-- Check RLS status
SELECT schemaname, tablename, rowsecurity, forcerowsecurity
FROM pg_tables 
WHERE tablename = 'calendar_sync_configs';