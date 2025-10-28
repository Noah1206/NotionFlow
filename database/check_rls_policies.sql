-- RLS 정책 확인 및 수정

-- 1. 현재 RLS 정책 확인
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename IN ('users', 'calendar_export_queue', 'calendar_export_logs');

-- 2. users 테이블 RLS 정책이 너무 제한적일 수 있음
-- 필요시 다음과 같이 수정:

-- users 테이블에 대한 읽기 권한 추가 (트리거 함수용)
-- DROP POLICY IF EXISTS "Enable read access for authenticated users" ON users;
-- CREATE POLICY "Enable read access for authenticated users" ON users
--     FOR SELECT USING (true);

-- 또는 서비스 역할에 대한 전체 액세스 허용
-- DROP POLICY IF EXISTS "Service role full access" ON users;
-- CREATE POLICY "Service role full access" ON users
--     FOR ALL TO service_role USING (true) WITH CHECK (true);