-- OAuth 토큰 저장 테이블
-- 각 플랫폼별 사용자 OAuth 토큰 관리

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL, -- 'google', 'notion', 'slack', 'outlook', 'apple'
    
    -- OAuth 토큰 정보
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(20) DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ,
    scope TEXT,
    
    -- 추가 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 고유 제약조건 (사용자당 플랫폼당 하나의 토큰)
    UNIQUE(user_id, platform)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_id ON oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_platform ON oauth_tokens(platform);

-- 업데이트 시간 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_oauth_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_oauth_tokens_updated_at
    BEFORE UPDATE ON oauth_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_oauth_tokens_updated_at();

-- RLS (Row Level Security) 정책 설정
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own tokens" ON oauth_tokens
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tokens" ON oauth_tokens
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tokens" ON oauth_tokens
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tokens" ON oauth_tokens
    FOR DELETE USING (auth.uid() = user_id);

-- 주석 추가
COMMENT ON TABLE oauth_tokens IS 'OAuth 토큰 저장 테이블';
COMMENT ON COLUMN oauth_tokens.platform IS '플랫폼 종류: google, notion, slack, outlook, apple';
COMMENT ON COLUMN oauth_tokens.access_token IS 'OAuth 액세스 토큰';
COMMENT ON COLUMN oauth_tokens.refresh_token IS 'OAuth 리프레시 토큰';
COMMENT ON COLUMN oauth_tokens.scope IS '승인된 스코프 목록';