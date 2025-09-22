-- Fix user ID format inconsistency and clean up invalid records

-- 1. Check current users table
SELECT id, email, created_at FROM users 
WHERE id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352',
    '8c7153b7-ee46-4d62-80ef-85b896e4962c',
    '550e8400-e29b-41d4-a716-446655440000'
);

-- 2. Clean up calendar_sync_configs with invalid user IDs
DELETE FROM calendar_sync_configs 
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '8c7153b7-ee46-4d62-80ef-85b896e4962c',
    '550e8400-e29b-41d4-a716-446655440000'
)
AND user_id NOT IN (SELECT id FROM users);

-- 3. Update user IDs to correct format (remove dashes if needed)
UPDATE calendar_sync_configs
SET user_id = REPLACE(user_id, '-', '')
WHERE user_id LIKE '%-%'
AND REPLACE(user_id, '-', '') IN (SELECT id FROM users);

-- 4. Clean up any orphaned oauth_tokens
DELETE FROM oauth_tokens
WHERE user_id NOT IN (SELECT id FROM users);

-- 5. Clean up any orphaned platform_coverage attempts
DELETE FROM platform_coverage
WHERE user_id NOT IN (SELECT id FROM users);

-- 6. Verify the cleanup
SELECT 'calendar_sync_configs' as table_name, COUNT(*) as orphaned_records
FROM calendar_sync_configs
WHERE user_id NOT IN (SELECT id FROM users)
UNION ALL
SELECT 'oauth_tokens', COUNT(*)
FROM oauth_tokens
WHERE user_id NOT IN (SELECT id FROM users)
UNION ALL
SELECT 'platform_coverage', COUNT(*)
FROM platform_coverage
WHERE user_id NOT IN (SELECT id FROM users);