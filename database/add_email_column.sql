-- 🔧 Add missing email column to user_profiles table
-- This will fix the "Could not find the 'email' column" error

-- Add email and encrypted_email columns to user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS email VARCHAR(255),
ADD COLUMN IF NOT EXISTS encrypted_email TEXT;

-- Add index for email queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- Add email uniqueness constraint (optional)
-- ALTER TABLE user_profiles ADD CONSTRAINT unique_email UNIQUE (email);

-- Update RLS policy to allow email column access
-- (The existing policies should already cover this, but just to be safe)

COMMENT ON COLUMN user_profiles.email IS 'User email address for notifications and authentication';
COMMENT ON COLUMN user_profiles.encrypted_email IS 'Encrypted email for URL generation';