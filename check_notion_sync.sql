-- Check Notion sync configuration for user
SELECT * FROM calendar_sync 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352' 
  AND platform = 'notion';

-- Check calendar_sync_configs table structure and data
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'calendar_sync_configs';

-- Check if there's any Notion config data
SELECT * FROM calendar_sync_configs 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352' 
  AND platform = 'notion';

-- Check registered platforms
SELECT * FROM registered_platforms 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352' 
  AND platform = 'notion';