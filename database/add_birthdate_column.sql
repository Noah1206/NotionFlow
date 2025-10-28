-- Add birthdate column to user_profiles table
-- This fixes the initial-setup redirect issue

-- Check if birthdate column exists, add it if not
DO $$
BEGIN
    -- Add birthdate column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'birthdate'
    ) THEN
        ALTER TABLE user_profiles 
        ADD COLUMN birthdate DATE DEFAULT '1990-01-01';
        
        RAISE NOTICE 'Added birthdate column to user_profiles table';
    ELSE
        RAISE NOTICE 'birthdate column already exists in user_profiles table';
    END IF;
END $$;

-- Update existing profiles that might not have birthdate
UPDATE user_profiles 
SET birthdate = '1990-01-01' 
WHERE birthdate IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.birthdate IS 'User birth date - defaults to 1990-01-01 to avoid initial-setup redirect';