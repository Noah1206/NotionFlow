-- 근본적인 외래키 제약조건 문제 해결
-- 모든 사용자가 OAuth 사용 시 외래키 오류를 겪지 않도록 수정

-- 1. 현재 외래키 제약조건들을 auth.users로 변경
-- (OAuth 사용자들은 auth.users에 저장되므로)

-- oauth_tokens 테이블 외래키 수정
ALTER TABLE oauth_tokens DROP CONSTRAINT IF EXISTS oauth_tokens_user_id_fkey;
ALTER TABLE oauth_tokens ADD CONSTRAINT oauth_tokens_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- platform_connections 테이블 외래키 수정  
ALTER TABLE platform_connections DROP CONSTRAINT IF EXISTS platform_connections_user_id_fkey;
ALTER TABLE platform_connections ADD CONSTRAINT platform_connections_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- calendar_sync_configs 테이블 외래키 수정
ALTER TABLE calendar_sync_configs DROP CONSTRAINT IF EXISTS calendar_sync_configs_user_id_fkey;
ALTER TABLE calendar_sync_configs ADD CONSTRAINT calendar_sync_configs_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- sync_events 테이블 외래키 수정
ALTER TABLE sync_events DROP CONSTRAINT IF EXISTS sync_events_user_id_fkey;
ALTER TABLE sync_events ADD CONSTRAINT sync_events_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- calendar_events 테이블 외래키 수정
ALTER TABLE calendar_events DROP CONSTRAINT IF EXISTS calendar_events_user_id_fkey;
ALTER TABLE calendar_events ADD CONSTRAINT calendar_events_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- 2. RLS 정책을 다시 활성화 (보안을 위해)
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_sync_configs ENABLE ROW LEVEL SECURITY;

-- 3. 새로운 RLS 정책 생성 (auth.users 기반)
CREATE POLICY "Users can manage their own oauth tokens" ON oauth_tokens
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own platform connections" ON platform_connections
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own sync configs" ON calendar_sync_configs
    FOR ALL USING (auth.uid() = user_id);

-- 4. 확인
SELECT 'Foreign key constraints updated to use auth.users' as status;