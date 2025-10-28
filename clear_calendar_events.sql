-- 특정 사용자의 모든 캘린더 이벤트 삭제

-- 1. 현재 이벤트 확인
SELECT count(*) FROM calendar_events
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';

-- 2. 해당 사용자의 모든 이벤트 삭제
DELETE FROM calendar_events
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';

-- 3. 캐시도 정리
DELETE FROM calendar_export_queue
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';

-- 4. 삭제 확인
SELECT count(*) FROM calendar_events
WHERE user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';