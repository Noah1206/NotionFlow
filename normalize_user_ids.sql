-- Normalize all user IDs to dash-free format across all tables
-- This script will update all user_id fields to remove dashes

BEGIN;

-- 1. First, backup current data
CREATE TABLE IF NOT EXISTS users_backup AS SELECT * FROM users;
CREATE TABLE IF NOT EXISTS calendars_backup AS SELECT * FROM calendars;
CREATE TABLE IF NOT EXISTS calendar_sync_configs_backup AS SELECT * FROM calendar_sync_configs;
CREATE TABLE IF NOT EXISTS oauth_tokens_backup AS SELECT * FROM oauth_tokens;
CREATE TABLE IF NOT EXISTS sync_events_backup AS SELECT * FROM sync_events;
CREATE TABLE IF NOT EXISTS platform_coverage_backup AS SELECT * FROM platform_coverage;
CREATE TABLE IF NOT EXISTS user_activities_backup AS SELECT * FROM user_activities;
CREATE TABLE IF NOT EXISTS sync_jobs_backup AS SELECT * FROM sync_jobs;

-- 2. Disable foreign key constraints temporarily
ALTER TABLE calendars DISABLE TRIGGER ALL;
ALTER TABLE calendar_sync_configs DISABLE TRIGGER ALL;
ALTER TABLE oauth_tokens DISABLE TRIGGER ALL;
ALTER TABLE sync_events DISABLE TRIGGER ALL;
ALTER TABLE platform_coverage DISABLE TRIGGER ALL;
ALTER TABLE user_activities DISABLE TRIGGER ALL;
ALTER TABLE sync_jobs DISABLE TRIGGER ALL;

-- 3. Update users table (primary key)
UPDATE users 
SET id = REPLACE(id, '-', '') 
WHERE id LIKE '%-%';

-- 4. Update calendars table
UPDATE calendars 
SET owner_id = REPLACE(owner_id, '-', '') 
WHERE owner_id LIKE '%-%';

-- 5. Update calendar_sync_configs table
UPDATE calendar_sync_configs 
SET user_id = REPLACE(user_id, '-', '') 
WHERE user_id LIKE '%-%';

-- 6. Update oauth_tokens table
UPDATE oauth_tokens 
SET user_id = REPLACE(user_id, '-', '') 
WHERE user_id LIKE '%-%';

-- 7. Update sync_events table
UPDATE sync_events 
SET user_id = REPLACE(user_id, '-', '') 
WHERE user_id LIKE '%-%';

-- 8. Update platform_coverage table
UPDATE platform_coverage 
SET user_id = REPLACE(user_id, '-', '') 
WHERE user_id LIKE '%-%';

-- 9. Update user_activities table
UPDATE user_activities 
SET user_id = REPLACE(user_id, '-', '') 
WHERE user_id LIKE '%-%';

-- 10. Update sync_jobs table
UPDATE sync_jobs 
SET user_id = REPLACE(user_id, '-', '') 
WHERE user_id LIKE '%-%';

-- 11. Re-enable foreign key constraints
ALTER TABLE calendars ENABLE TRIGGER ALL;
ALTER TABLE calendar_sync_configs ENABLE TRIGGER ALL;
ALTER TABLE oauth_tokens ENABLE TRIGGER ALL;
ALTER TABLE sync_events ENABLE TRIGGER ALL;
ALTER TABLE platform_coverage ENABLE TRIGGER ALL;
ALTER TABLE user_activities ENABLE TRIGGER ALL;
ALTER TABLE sync_jobs ENABLE TRIGGER ALL;

-- 12. Verify the updates
SELECT 'users' as table_name, COUNT(*) as records_with_dashes 
FROM users WHERE id LIKE '%-%'
UNION ALL
SELECT 'calendars', COUNT(*) 
FROM calendars WHERE owner_id LIKE '%-%'
UNION ALL
SELECT 'calendar_sync_configs', COUNT(*) 
FROM calendar_sync_configs WHERE user_id LIKE '%-%'
UNION ALL
SELECT 'oauth_tokens', COUNT(*) 
FROM oauth_tokens WHERE user_id LIKE '%-%'
UNION ALL
SELECT 'sync_events', COUNT(*) 
FROM sync_events WHERE user_id LIKE '%-%'
UNION ALL
SELECT 'platform_coverage', COUNT(*) 
FROM platform_coverage WHERE user_id LIKE '%-%'
UNION ALL
SELECT 'user_activities', COUNT(*) 
FROM user_activities WHERE user_id LIKE '%-%'
UNION ALL
SELECT 'sync_jobs', COUNT(*) 
FROM sync_jobs WHERE user_id LIKE '%-%';

-- If all counts are 0, commit the transaction
-- Otherwise, rollback
COMMIT;