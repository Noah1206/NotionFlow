-- 간단한 Notion 자동 동기화 비활성화

-- 1. 모든 Notion 자동 동기화 비활성화
UPDATE calendar_sync_configs
SET is_enabled = false
WHERE platform = 'notion';

-- 2. 특정 사용자 확인 및 비활성화
UPDATE calendar_sync_configs
SET is_enabled = false
WHERE platform = 'notion' AND user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';

-- 3. 결과 확인
SELECT user_id, platform, is_enabled
FROM calendar_sync_configs
WHERE platform = 'notion';