-- Fix Notion sync by setting the calendar_id
-- Update the calendar_sync_configs to link to the user's calendar

UPDATE calendar_sync_configs 
SET calendar_id = '68154a23-5dc5-47f8-a84f-c740ccacfc49'
WHERE id = '3b215a4c-3e20-4242-be1b-a60b00af7989'
  AND user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
  AND platform = 'notion';

-- Verify the update
SELECT * FROM calendar_sync_configs 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352' 
  AND platform = 'notion';

-- Also check if there's a calendar_sync entry
SELECT * FROM calendar_sync 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352' 
  AND platform = 'notion';

-- If no calendar_sync entry exists, create one
INSERT INTO calendar_sync (user_id, platform, calendar_id, is_active, created_at, updated_at)
VALUES (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    'notion',
    '68154a23-5dc5-47f8-a84f-c740ccacfc49',
    true,
    NOW(),
    NOW()
)
ON CONFLICT (user_id, platform, calendar_id) 
DO UPDATE SET 
    is_active = true,
    updated_at = NOW();