-- Simple fix for calendar_sync_configs RLS policies
-- This handles UUID/TEXT type casting properly

-- Drop existing policies
DROP POLICY IF EXISTS "Users can read own sync configs" ON calendar_sync_configs;
DROP POLICY IF EXISTS "Users can insert own sync configs" ON calendar_sync_configs;
DROP POLICY IF EXISTS "Users can update own sync configs" ON calendar_sync_configs;
DROP POLICY IF EXISTS "Users can delete own sync configs" ON calendar_sync_configs;

-- Simplified policies with proper type casting
CREATE POLICY "Users can read own sync configs" ON calendar_sync_configs
  FOR SELECT
  USING (
    user_id::uuid = auth.uid() 
    OR user_id = auth.uid()::text
    OR user_id = COALESCE((auth.jwt() ->> 'sub'), auth.uid()::text)
  );

CREATE POLICY "Users can insert own sync configs" ON calendar_sync_configs
  FOR INSERT
  WITH CHECK (
    user_id::uuid = auth.uid() 
    OR user_id = auth.uid()::text
    OR user_id = COALESCE((auth.jwt() ->> 'sub'), auth.uid()::text)
  );

CREATE POLICY "Users can update own sync configs" ON calendar_sync_configs
  FOR UPDATE
  USING (
    user_id::uuid = auth.uid() 
    OR user_id = auth.uid()::text
    OR user_id = COALESCE((auth.jwt() ->> 'sub'), auth.uid()::text)
  )
  WITH CHECK (
    user_id::uuid = auth.uid() 
    OR user_id = auth.uid()::text
    OR user_id = COALESCE((auth.jwt() ->> 'sub'), auth.uid()::text)
  );

CREATE POLICY "Users can delete own sync configs" ON calendar_sync_configs
  FOR DELETE
  USING (
    user_id::uuid = auth.uid() 
    OR user_id = auth.uid()::text
    OR user_id = COALESCE((auth.jwt() ->> 'sub'), auth.uid()::text)
  );

-- Check what we created
SELECT 
  schemaname, 
  tablename, 
  policyname, 
  permissive, 
  cmd, 
  qual 
FROM pg_policies 
WHERE tablename = 'calendar_sync_configs'
ORDER BY policyname;