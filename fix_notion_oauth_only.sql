-- Notion OAuth 토큰 저장 문제만 해결

-- 1. oauth_tokens RLS 정책 완전 비활성화 (개발용)
ALTER TABLE oauth_tokens DISABLE ROW LEVEL SECURITY;

-- 2. 또는 서비스 역할로 모든 권한 허용
-- ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;
-- DROP POLICY IF EXISTS "Allow all for development" ON oauth_tokens;
-- CREATE POLICY "Allow all for development" ON oauth_tokens
--     FOR ALL USING (true) WITH CHECK (true);

-- 3. auth.users에 사용자 추가 (외래키 제약 해결)
INSERT INTO auth.users (id, email, created_at, updated_at)
VALUES ('87875eda-6797-f839-f8c7-0aa90efb1352'::uuid, 'ab40905045@gmail.com', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO auth.users (id, email, created_at, updated_at)  
VALUES ('272f2b1c-a770-4119-92bf-563276830b84'::uuid, 'user2@example.com', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 4. users 테이블 name 컬럼 수정 (이미 했지만 재확인)
UPDATE users SET name = COALESCE(name, 'User') WHERE name IS NULL;

-- 5. 기존 테스트 이벤트 삭제 (실제 Notion 데이터만 보기 위해)
DELETE FROM calendar_events WHERE source_platform = 'manual';

