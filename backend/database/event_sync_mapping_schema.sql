-- 일정 동기화 매핑 테이블
-- Notion 일정과 외부 플랫폼 일정 간의 매핑 정보 저장

CREATE TABLE IF NOT EXISTS event_sync_mapping (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Notion 일정 정보
    notion_event_id VARCHAR(255) NOT NULL,
    notion_calendar_id VARCHAR(255),
    
    -- 외부 플랫폼 일정 정보
    platform VARCHAR(50) NOT NULL, -- 'google', 'outlook', 'apple', 'slack'
    external_event_id VARCHAR(255) NOT NULL,
    external_calendar_id VARCHAR(255),
    
    -- 동기화 상태
    sync_status VARCHAR(50) DEFAULT 'synced', -- 'synced', 'pending', 'failed', 'conflict'
    last_sync_direction VARCHAR(20), -- 'notion_to_external', 'external_to_notion', 'bidirectional'
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 메타데이터
    sync_metadata JSONB, -- 추가적인 동기화 정보
    error_message TEXT,  -- 동기화 실패 시 오류 메시지
    
    -- 인덱스와 제약조건
    UNIQUE(user_id, notion_event_id, platform),
    UNIQUE(user_id, external_event_id, platform)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_event_sync_mapping_user_id ON event_sync_mapping(user_id);
CREATE INDEX IF NOT EXISTS idx_event_sync_mapping_platform ON event_sync_mapping(platform);
CREATE INDEX IF NOT EXISTS idx_event_sync_mapping_sync_status ON event_sync_mapping(sync_status);
CREATE INDEX IF NOT EXISTS idx_event_sync_mapping_notion_event ON event_sync_mapping(notion_event_id);
CREATE INDEX IF NOT EXISTS idx_event_sync_mapping_external_event ON event_sync_mapping(external_event_id);

-- 업데이트 시간 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_event_sync_mapping_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_event_sync_mapping_updated_at
    BEFORE UPDATE ON event_sync_mapping
    FOR EACH ROW
    EXECUTE FUNCTION update_event_sync_mapping_updated_at();

-- RLS (Row Level Security) 정책 설정
ALTER TABLE event_sync_mapping ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own event sync mappings" ON event_sync_mapping
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own event sync mappings" ON event_sync_mapping
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own event sync mappings" ON event_sync_mapping
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own event sync mappings" ON event_sync_mapping
    FOR DELETE USING (auth.uid() = user_id);

-- 주석 추가
COMMENT ON TABLE event_sync_mapping IS 'Notion 일정과 외부 플랫폼 일정 간의 동기화 매핑 정보';
COMMENT ON COLUMN event_sync_mapping.notion_event_id IS 'Notion 페이지 ID 또는 데이터베이스 row ID';
COMMENT ON COLUMN event_sync_mapping.platform IS '동기화 대상 플랫폼: google, outlook, apple, slack';
COMMENT ON COLUMN event_sync_mapping.external_event_id IS '외부 플랫폼의 일정 ID';
COMMENT ON COLUMN event_sync_mapping.sync_status IS '동기화 상태: synced, pending, failed, conflict';
COMMENT ON COLUMN event_sync_mapping.last_sync_direction IS '마지막 동기화 방향';
COMMENT ON COLUMN event_sync_mapping.sync_metadata IS '추가적인 동기화 정보 (JSON 형태)';