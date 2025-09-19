-- NotionFlow Test Data Cleanup Script
-- 실제로 연동하지 않은 테스트 데이터들을 정리합니다

-- 1. 먼저 어떤 데이터가 있는지 확인
SELECT 'Before cleanup - Calendar Sync Configs' as info, platform, is_enabled, 
       created_at::date, 
       CASE 
           WHEN credentials IS NULL THEN 'NULL'
           WHEN credentials::text = '{}' THEN 'EMPTY'
           WHEN credentials::text LIKE '%access_token%' THEN 'HAS_TOKEN'
           ELSE 'OTHER'
       END as credential_status
FROM calendar_sync_configs 
WHERE user_id = '87875eda6797f839f8c70aa90efb1352';

-- 2. 테스트용 Calendar 3e7f438e 관련 데이터 삭제
DELETE FROM calendar_events 
WHERE calendar_id = '3e7f438e-b233-43f7-9329-1656acd82682'
AND user_id = '87875eda6797f839f8c70aa90efb1352';

-- 3. 테스트용 캘린더 삭제 (실제 생성하지 않은 캘린더)
DELETE FROM calendars 
WHERE id = '3e7f438e-b233-43f7-9329-1656acd82682'
AND owner_id = '87875eda6797f839f8c70aa90efb1352';

-- 4. 만약 Notion 설정이 테스트 데이터라면 삭제 (신중하게!)
-- 실제 OAuth 토큰이 있다면 이 부분은 주석처리하세요
-- DELETE FROM calendar_sync_configs 
-- WHERE platform = 'notion' 
-- AND user_id = '87875eda6797f839f8c70aa90efb1352'
-- AND (credentials IS NULL OR credentials::text = '{}' OR credentials::text NOT LIKE '%access_token%');

-- 4. 확인 쿼리들
SELECT 'Calendar Sync Configs' as table_name, platform, is_enabled, created_at 
FROM calendar_sync_configs 
WHERE user_id = '87875eda6797f839f8c70aa90efb1352';

SELECT 'Calendars' as table_name, id, name, type 
FROM calendars 
WHERE owner_id = '87875eda6797f839f8c70aa90efb1352';

SELECT 'Calendar Events' as table_name, count(*) as event_count 
FROM calendar_events 
WHERE user_id = '87875eda6797f839f8c70aa90efb1352';