-- Notion 동기화 일시 중지
-- calendar_sync_configs 테이블에서 Notion 토큰 비활성화

-- 1. 현재 Notion 동기화 설정 확인
SELECT * FROM calendar_sync_configs WHERE platform = 'notion';

-- 2. Notion 동기화 비활성화 (임시)
UPDATE calendar_sync_configs
SET is_active = false
WHERE platform = 'notion' AND user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';

-- 3. 기존 이벤트 삭제 (필요시)
-- DELETE FROM calendar_events WHERE source_platform = 'notion' AND user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';

-- 나중에 다시 활성화하려면:
-- UPDATE calendar_sync_configs SET is_active = true WHERE platform = 'notion' AND user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';