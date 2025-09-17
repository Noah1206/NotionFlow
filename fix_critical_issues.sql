-- NotionFlow 긴급 데이터베이스 수정 스크립트
-- 각 섹션을 개별적으로 실행 가능

-- 1. oauth_tokens 테이블 RLS 정책 수정
DROP POLICY IF EXISTS "Users can insert their own tokens" ON oauth_tokens;

CREATE POLICY "Users can insert their own tokens" ON oauth_tokens
    FOR INSERT WITH CHECK (true);

-- service_role을 위한 정책 추가
DROP POLICY IF EXISTS "Service role full access to oauth_tokens" ON oauth_tokens;

CREATE POLICY "Service role full access to oauth_tokens" ON oauth_tokens
    FOR ALL USING (true) WITH CHECK (true);

-- 2. users 테이블의 name 컬럼 nullable로 변경
ALTER TABLE users ALTER COLUMN name DROP NOT NULL;
ALTER TABLE users ALTER COLUMN name SET DEFAULT 'User';

-- 3. calendar_events 테이블에 calendar_id 컬럼 추가 (이미 source_calendar_id가 있다면 별칭 추가)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='calendar_events' AND column_name='calendar_id') THEN
        ALTER TABLE calendar_events ADD COLUMN calendar_id UUID;
    END IF;
END $$;

-- 4. platform_connections 테이블에 토큰 컬럼 추가
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='platform_connections' AND column_name='access_token') THEN
        ALTER TABLE platform_connections ADD COLUMN access_token TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='platform_connections' AND column_name='refresh_token') THEN
        ALTER TABLE platform_connections ADD COLUMN refresh_token TEXT;
    END IF;
END $$;

