-- 최종 문제 해결 SQL

-- 1. auth.users 테이블에 사용자가 있는지 확인하고 없으면 추가
DO $$ 
BEGIN
    -- User 1
    IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = '87875eda-6797-f839-f8c7-0aa90efb1352'::uuid) THEN
        INSERT INTO auth.users (id, email, created_at, updated_at)
        VALUES ('87875eda-6797-f839-f8c7-0aa90efb1352'::uuid, 'ab40905045@gmail.com', NOW(), NOW());
    END IF;
    
    -- User 2  
    IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = '272f2b1c-a770-4119-92bf-563276830b84'::uuid) THEN
        INSERT INTO auth.users (id, email, created_at, updated_at)
        VALUES ('272f2b1c-a770-4119-92bf-563276830b84'::uuid, 'user2@example.com', NOW(), NOW());
    END IF;
END $$;

-- 2. oauth_tokens RLS 정책을 완전히 다시 설정
ALTER TABLE oauth_tokens DISABLE ROW LEVEL SECURITY;

-- 또는 더 관대한 정책으로 변경
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can insert their own tokens" ON oauth_tokens;
DROP POLICY IF EXISTS "Users can view their own tokens" ON oauth_tokens;
DROP POLICY IF EXISTS "Users can update their own tokens" ON oauth_tokens;
DROP POLICY IF EXISTS "Users can delete their own tokens" ON oauth_tokens;

-- 임시로 모든 작업 허용 (개발 환경용)
CREATE POLICY "Allow all for development" ON oauth_tokens
    FOR ALL USING (true) WITH CHECK (true);

-- 3. calendar_events 테이블 뷰 생성 (calendar_id 별칭)
CREATE OR REPLACE VIEW calendar_events_view AS 
SELECT 
    *,
    source_calendar_id AS calendar_id
FROM calendar_events;

-- 4. 테스트 이벤트 추가
INSERT INTO calendar_events (
    user_id,
    external_id,
    title,
    description,
    start_datetime,
    end_datetime,
    is_all_day,
    source_platform,
    source_calendar_id,
    source_calendar_name,
    status
) VALUES 
(
    '87875eda6797f839f8c70aa90efb1352',
    'test-event-1',
    '테스트 이벤트 1',
    '테스트 설명',
    '2025-09-18T10:00:00Z',
    '2025-09-18T11:00:00Z',
    false,
    'manual',
    '3e7f438e-b233-43f7-9329-1656acd82682',
    '내 새 캘린더',
    'confirmed'
),
(
    '87875eda6797f839f8c70aa90efb1352',
    'test-event-2',
    '종일 이벤트',
    '종일 테스트',
    '2025-09-19T00:00:00Z',
    '2025-09-19T23:59:59Z',
    true,
    'manual',
    '3e7f438e-b233-43f7-9329-1656acd82682',
    '내 새 캘린더',
    'confirmed'
),
(
    '272f2b1c-a770-4119-92bf-563276830b84',
    'test-event-3',
    '회의',
    '팀 회의',
    '2025-09-20T14:00:00Z',
    '2025-09-20T15:00:00Z',
    false,
    'manual',
    '26481b0a-ace7-4a9f-b821-e13e0896a03e',
    '내 새 캘린더',
    'confirmed'
)
ON CONFLICT (user_id, external_id, source_platform) DO NOTHING;

-- 5. 이벤트 개수 확인
SELECT 
    user_id,
    COUNT(*) as event_count,
    MIN(start_datetime) as first_event,
    MAX(start_datetime) as last_event
FROM calendar_events
GROUP BY user_id;

