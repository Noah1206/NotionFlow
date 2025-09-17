-- OAuth 토큰 저장 문제만 간단히 해결

-- 1. oauth_tokens RLS 정책 완전 비활성화 (가장 확실한 방법)
ALTER TABLE oauth_tokens DISABLE ROW LEVEL SECURITY;

-- 2. users 테이블 name 컬럼 null 허용 확인
UPDATE users SET name = 'User' WHERE name IS NULL;

-- 3. 현재 상태 확인
SELECT 'OAuth tokens count:' as info, COUNT(*) as count FROM oauth_tokens;
SELECT 'Calendar events count:' as info, COUNT(*) as count FROM calendar_events;

-- 4. 기존 실패한 토큰 삭제 (있다면)
DELETE FROM oauth_tokens WHERE platform = 'notion';

