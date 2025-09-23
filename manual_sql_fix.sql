-- 🔧 Calendar Events 데이터 수정 SQL
-- 53개 이벤트를 분석한 결과를 바탕으로 한 수정 쿼리

-- 사용자 ID (하이픈 포함/제거 두 형식 모두 고려)
-- user_id: 87875eda-6797-f839-f8c7-0aa90efb1352 (하이픈 포함)
-- user_id: 87875eda6797f839f8c70aa90efb1352 (하이픈 제거)

-- 타겟 캘린더: 6db7a044-c84b-4e4d-b23f-482cde1f80fc (내 새 캘린더)

-- 1️⃣ 모든 이벤트를 '내 새 캘린더'로 통합
UPDATE calendar_events 
SET 
    calendar_id = '6db7a044-c84b-4e4d-b23f-482cde1f80fc',
    updated_at = NOW()
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
);

-- 2️⃣ Category 정규화 (null → 'notion')
UPDATE calendar_events 
SET 
    category = 'notion',
    updated_at = NOW()
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
) 
AND category IS NULL;

-- 3️⃣ Priority 정규화 (0 → 1)
UPDATE calendar_events 
SET 
    priority = 1,
    updated_at = NOW()
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
) 
AND priority = 0;

-- 4️⃣ External_ID 정규화 (null 값들을 일관된 형식으로)
UPDATE calendar_events 
SET 
    external_id = CONCAT('notion_', REPLACE(id::text, '-', '')),
    updated_at = NOW()
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
) 
AND external_id IS NULL;

-- 5️⃣ 검증 쿼리들
-- 결과 확인
SELECT 
    '최종 결과' as check_type,
    calendar_id,
    COUNT(*) as event_count
FROM calendar_events 
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
)
GROUP BY calendar_id
ORDER BY event_count DESC;

-- Category 분포 확인
SELECT 
    'Category 분포' as check_type,
    category,
    COUNT(*) as count
FROM calendar_events 
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
)
GROUP BY category;

-- Priority 분포 확인
SELECT 
    'Priority 분포' as check_type,
    priority,
    COUNT(*) as count
FROM calendar_events 
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
)
GROUP BY priority;

-- NULL 값 체크
SELECT 
    'NULL 체크' as check_type,
    SUM(CASE WHEN calendar_id IS NULL THEN 1 ELSE 0 END) as null_calendar_id,
    SUM(CASE WHEN category IS NULL THEN 1 ELSE 0 END) as null_category,
    SUM(CASE WHEN external_id IS NULL THEN 1 ELSE 0 END) as null_external_id
FROM calendar_events 
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
);

-- 최종 성공률 체크
SELECT 
    '성공률' as check_type,
    COUNT(*) as total_events,
    SUM(CASE WHEN calendar_id = '6db7a044-c84b-4e4d-b23f-482cde1f80fc' THEN 1 ELSE 0 END) as target_calendar_events,
    ROUND(
        (SUM(CASE WHEN calendar_id = '6db7a044-c84b-4e4d-b23f-482cde1f80fc' THEN 1 ELSE 0 END)::FLOAT / COUNT(*)) * 100, 
        1
    ) as success_rate_percent
FROM calendar_events 
WHERE user_id IN (
    '87875eda-6797-f839-f8c7-0aa90efb1352',
    '87875eda6797f839f8c70aa90efb1352'
);