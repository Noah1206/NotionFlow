-- Remove foreign key constraint from user_profiles table
-- This allows profiles to exist without corresponding users table entries

-- Drop the foreign key constraint
ALTER TABLE user_profiles DROP CONSTRAINT IF EXISTS user_profiles_user_id_fkey;

-- Add comment for documentation  
COMMENT ON TABLE user_profiles IS 'User profiles - foreign key constraint removed for Supabase Auth compatibility';

-- Optional: Add index for performance since we removed the FK
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id_performance ON user_profiles(user_id);