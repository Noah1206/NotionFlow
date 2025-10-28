-- Notion 자동 동기화 완전 비활성화 (수동 동기화만 허용)
-- 모든 사용자의 Notion 자동 동기화 설정을 비활성화

-- 1. 현재 Notion 동기화 설정 확인
SELECT user_id, platform, is_enabled, sync_status, last_sync_at
FROM calendar_sync_configs
WHERE platform = 'notion';

-- 2. 모든 Notion 동기화 자동 실행 비활성화
UPDATE calendar_sync_configs
SET is_enabled = false,
    sync_status = 'manual_only',
    updated_at = NOW()
WHERE platform = 'notion';

-- 3. 특정 사용자의 Notion 동기화 비활성화 (필요시)
UPDATE calendar_sync_configs
SET is_enabled = false,
    sync_status = 'manual_only',
    updated_at = NOW()
WHERE platform = 'notion' AND user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';

-- 4. 확인
SELECT user_id, platform, is_enabled, sync_status, last_sync_at
FROM calendar_sync_configs
WHERE platform = 'notion';

-- 5. 선택사항: 기존 Notion 이벤트 정리 (원하는 경우)
-- DELETE FROM calendar_events
-- WHERE source_platform = 'notion' AND user_id = '87875eda-6797-f839-f8c7-0aa90efb1352';

COMMIT;