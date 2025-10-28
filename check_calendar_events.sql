-- 캘린더별 이벤트 수 확인
SELECT 
    c.name as calendar_name,
    c.id as calendar_id,
    COUNT(ce.id) as event_count
FROM calendars c
LEFT JOIN calendar_events ce ON c.id = ce.calendar_id
WHERE c.owner_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
GROUP BY c.id, c.name
ORDER BY c.name;

-- 내 새 캘린더의 최근 이벤트 5개
SELECT 
    title,
    start_datetime,
    created_at
FROM calendar_events
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
    AND calendar_id = '6db7a044-c84b-4e4d-b23f-482cde1f80fc'
ORDER BY created_at DESC
LIMIT 5;
