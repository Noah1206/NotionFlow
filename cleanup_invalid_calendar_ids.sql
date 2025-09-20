-- Clean up invalid calendar IDs from calendar_sync table
-- These are Notion database IDs that were incorrectly stored as calendar IDs

-- Check current invalid entries
SELECT * FROM calendar_sync 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
  AND calendar_id IN (
    '3e7f438e-b233-43f7-9329-1656acd82682',
    '853988ac-b4f9-4e5a-a04f-cde85caadeaa', 
    'de110742-c2dc-4986-9267-7c12fe1303a1',
    '9faeb1b9-26e4-444d-b35b-32072d9025af',
    '5e20c37d-5723-4aeb-9429-c2b03cd59c9c'
  );

-- Delete invalid calendar_sync entries
DELETE FROM calendar_sync 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
  AND calendar_id IN (
    '3e7f438e-b233-43f7-9329-1656acd82682',
    '853988ac-b4f9-4e5a-a04f-cde85caadeaa', 
    'de110742-c2dc-4986-9267-7c12fe1303a1',
    '9faeb1b9-26e4-444d-b35b-32072d9025af',
    '5e20c37d-5723-4aeb-9429-c2b03cd59c9c'
  );

-- Check if there are any events linked to these invalid calendar IDs
SELECT calendar_id, COUNT(*) as event_count
FROM events 
WHERE calendar_id IN (
    '3e7f438e-b233-43f7-9329-1656acd82682',
    '853988ac-b4f9-4e5a-a04f-cde85caadeaa', 
    'de110742-c2dc-4986-9267-7c12fe1303a1',
    '9faeb1b9-26e4-444d-b35b-32072d9025af',
    '5e20c37d-5723-4aeb-9429-c2b03cd59c9c'
  )
GROUP BY calendar_id;

-- If there are events, move them to the correct calendar
UPDATE events 
SET calendar_id = '68154a23-5dc5-47f8-a84f-c740ccacfc49'
WHERE calendar_id IN (
    '3e7f438e-b233-43f7-9329-1656acd82682',
    '853988ac-b4f9-4e5a-a04f-cde85caadeaa', 
    'de110742-c2dc-4986-9267-7c12fe1303a1',
    '9faeb1b9-26e4-444d-b35b-32072d9025af',
    '5e20c37d-5723-4aeb-9429-c2b03cd59c9c'
  );

-- Verify cleanup
SELECT 'After cleanup - calendar_sync entries:' as check_type, COUNT(*) as count
FROM calendar_sync 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'

UNION ALL

SELECT 'After cleanup - valid calendar entries:' as check_type, COUNT(*) as count
FROM calendar_sync 
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
  AND calendar_id = '68154a23-5dc5-47f8-a84f-c740ccacfc49';