-- 실제 저장된 자격증명 확인
SELECT 
    platform,
    is_enabled,
    created_at,
    last_sync_at,
    consecutive_failures,
    CASE 
        WHEN credentials IS NULL THEN 'NULL'
        WHEN credentials::text = '{}' THEN 'EMPTY_OBJECT'
        WHEN credentials::text LIKE '%access_token%' THEN 'HAS_ACCESS_TOKEN'
        ELSE 'UNKNOWN_FORMAT'
    END as credential_status,
    LENGTH(credentials::text) as credential_length
FROM calendar_sync_configs 
WHERE user_id = '87875eda6797f839f8c70aa90efb1352'
ORDER BY platform;

-- Notion 자격증명 상세 확인 (토큰 마스킹)
SELECT 
    platform,
    is_enabled,
    CASE 
        WHEN credentials->>'access_token' IS NOT NULL THEN 
            CONCAT(LEFT(credentials->>'access_token', 10), '...', RIGHT(credentials->>'access_token', 4))
        ELSE 'NO_TOKEN'
    END as masked_token,
    created_at
FROM calendar_sync_configs 
WHERE user_id = '87875eda6797f839f8c70aa90efb1352' 
AND platform = 'notion';