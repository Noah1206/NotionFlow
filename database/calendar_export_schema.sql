-- =====================================
-- 캘린더 내보내기 및 변경사항 추적 시스템
-- =====================================

-- 1. 캘린더별 내보내기 설정 테이블
CREATE TABLE IF NOT EXISTS calendar_export_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- 내보내기 설정
    auto_export BOOLEAN DEFAULT false,
    enabled_platforms JSONB DEFAULT '[]'::jsonb, -- ["google", "notion", "outlook"]
    
    export_all_events BOOLEAN DEFAULT true,

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 고유 제약조건
    UNIQUE(calendar_id, user_id)
);

-- 2. 변경사항 추적 큐 테이블
CREATE TABLE IF NOT EXISTS calendar_export_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    event_id UUID REFERENCES calendar_events(id) ON DELETE CASCADE,

    -- 변경 정보
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('created', 'updated', 'deleted')),
    event_data JSONB, -- 이벤트 전체 데이터 (삭제의 경우 삭제 전 데이터)
    change_summary TEXT, -- 변경사항 요약

    -- 내보내기 상태
    export_status VARCHAR(20) DEFAULT 'pending' CHECK (export_status IN ('pending', 'processing', 'completed', 'failed')),
    target_platforms JSONB DEFAULT '[]'::jsonb, -- 내보낼 플랫폼 목록
    export_results JSONB DEFAULT '{}'::jsonb, -- 플랫폼별 내보내기 결과

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,

    -- 인덱스용 컬럼
    is_processed BOOLEAN DEFAULT false
);

-- 3. 내보내기 로그 테이블
CREATE TABLE IF NOT EXISTS calendar_export_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    queue_id UUID REFERENCES calendar_export_queue(id) ON DELETE SET NULL,

    -- 내보내기 정보
    platform VARCHAR(50) NOT NULL,
    operation_type VARCHAR(20) NOT NULL, -- 'export_batch', 'sync_single'
    events_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,

    -- 결과
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    execution_time_ms INTEGER,
    details JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,

    -- 메타데이터
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- 통계용 컬럼
    date_created DATE
);

-- 4. 플랫폼별 동기화 매핑 테이블
CREATE TABLE IF NOT EXISTS platform_event_mapping (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    local_event_id UUID NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,

    -- 플랫폼 정보
    platform VARCHAR(50) NOT NULL,
    platform_event_id TEXT NOT NULL, -- 플랫폼에서의 이벤트 ID
    platform_calendar_id TEXT, -- 플랫폼에서의 캘린더 ID

    -- 동기화 정보
    sync_status VARCHAR(20) DEFAULT 'synced' CHECK (sync_status IN ('synced', 'pending', 'failed', 'deleted')),
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    sync_hash TEXT, -- 변경 감지용 해시

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 고유 제약조건
    UNIQUE(local_event_id, platform),
    UNIQUE(platform, platform_event_id)
);

-- =====================================
-- 인덱스 생성
-- =====================================

-- calendar_export_settings 인덱스
CREATE INDEX IF NOT EXISTS idx_export_settings_calendar_id ON calendar_export_settings(calendar_id);
CREATE INDEX IF NOT EXISTS idx_export_settings_user_id ON calendar_export_settings(user_id);

-- calendar_export_queue 인덱스
CREATE INDEX IF NOT EXISTS idx_export_queue_calendar_id ON calendar_export_queue(calendar_id);
CREATE INDEX IF NOT EXISTS idx_export_queue_user_id ON calendar_export_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_export_queue_status ON calendar_export_queue(export_status);
CREATE INDEX IF NOT EXISTS idx_export_queue_created_at ON calendar_export_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_export_queue_pending ON calendar_export_queue(calendar_id, export_status) WHERE export_status = 'pending';
CREATE INDEX IF NOT EXISTS idx_export_queue_processing ON calendar_export_queue(user_id, is_processed) WHERE is_processed = false;

-- calendar_export_logs 인덱스
CREATE INDEX IF NOT EXISTS idx_export_logs_calendar_id ON calendar_export_logs(calendar_id);
CREATE INDEX IF NOT EXISTS idx_export_logs_user_id ON calendar_export_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_export_logs_platform ON calendar_export_logs(platform);
CREATE INDEX IF NOT EXISTS idx_export_logs_date ON calendar_export_logs(date_created);
CREATE INDEX IF NOT EXISTS idx_export_logs_status ON calendar_export_logs(status);

-- platform_event_mapping 인덱스
CREATE INDEX IF NOT EXISTS idx_platform_mapping_calendar_id ON platform_event_mapping(calendar_id);
CREATE INDEX IF NOT EXISTS idx_platform_mapping_local_event ON platform_event_mapping(local_event_id);
CREATE INDEX IF NOT EXISTS idx_platform_mapping_platform ON platform_event_mapping(platform);
CREATE INDEX IF NOT EXISTS idx_platform_mapping_platform_event ON platform_event_mapping(platform, platform_event_id);
CREATE INDEX IF NOT EXISTS idx_platform_mapping_sync_status ON platform_event_mapping(sync_status);

-- =====================================
-- 트리거 및 함수 생성
-- =====================================

-- 업데이트 시간 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_calendar_export_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- calendar_export_settings 업데이트 트리거
CREATE TRIGGER trigger_update_export_settings_updated_at
    BEFORE UPDATE ON calendar_export_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_calendar_export_updated_at();

-- platform_event_mapping 업데이트 트리거
CREATE TRIGGER trigger_update_platform_mapping_updated_at
    BEFORE UPDATE ON platform_event_mapping
    FOR EACH ROW
    EXECUTE FUNCTION update_calendar_export_updated_at();

-- =====================================
-- 변경사항 추적 트리거
-- =====================================

-- 이벤트 변경 시 export_queue에 자동 추가 (사용자 존재 확인)
CREATE OR REPLACE FUNCTION track_calendar_event_changes()
RETURNS TRIGGER AS $$
DECLARE
    change_type_val VARCHAR(20);
    event_data_val JSONB;
    summary_val TEXT;
    target_user_id UUID;
    user_exists BOOLEAN := FALSE;
BEGIN
    -- 변경 타입 결정
    IF TG_OP = 'INSERT' THEN
        change_type_val := 'created';
        event_data_val := to_jsonb(NEW);
        summary_val := 'Event created: ' || NEW.title;
        target_user_id := NEW.user_id;
    ELSIF TG_OP = 'UPDATE' THEN
        change_type_val := 'updated';
        event_data_val := to_jsonb(NEW);
        summary_val := 'Event updated: ' || NEW.title;
        target_user_id := NEW.user_id;
    ELSIF TG_OP = 'DELETE' THEN
        change_type_val := 'deleted';
        event_data_val := to_jsonb(OLD);
        summary_val := 'Event deleted: ' || OLD.title;
        target_user_id := OLD.user_id;
    END IF;

    -- 사용자 존재 여부 확인 (users 테이블 또는 auth.users 테이블)
    SELECT EXISTS(
        SELECT 1 FROM auth.users WHERE id = target_user_id
        UNION ALL
        SELECT 1 FROM users WHERE id = target_user_id
    ) INTO user_exists;

    -- 사용자가 존재하는 경우에만 export_queue에 추가
    IF user_exists THEN
        INSERT INTO calendar_export_queue (
            calendar_id,
            user_id,
            event_id,
            change_type,
            event_data,
            change_summary
        ) VALUES (
            COALESCE(NEW.calendar_id, OLD.calendar_id),
            target_user_id,
            COALESCE(NEW.id, OLD.id),
            change_type_val,
            event_data_val,
            summary_val
        );
    ELSE
        -- 사용자가 존재하지 않으면 로그만 남기고 에러 발생시키지 않음
        RAISE NOTICE 'User % does not exist in users table, skipping export queue entry', target_user_id;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- calendar_events 테이블에 변경 추적 트리거 설정
CREATE TRIGGER trigger_track_calendar_events_changes
    AFTER INSERT OR UPDATE OR DELETE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION track_calendar_event_changes();

-- is_processed 상태 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_is_processed_status()
RETURNS TRIGGER AS $$
BEGIN
    NEW.is_processed = (NEW.export_status IN ('completed', 'failed'));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_is_processed
    BEFORE INSERT OR UPDATE ON calendar_export_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_is_processed_status();

-- date_created 자동 설정 트리거
CREATE OR REPLACE FUNCTION set_date_created()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_created = DATE(NEW.started_at);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_date_created
    BEFORE INSERT OR UPDATE ON calendar_export_logs
    FOR EACH ROW
    EXECUTE FUNCTION set_date_created();

-- =====================================
-- 유틸리티 함수들
-- =====================================

-- 대기 중인 변경사항 수 조회
CREATE OR REPLACE FUNCTION get_pending_changes_count(p_calendar_id UUID)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM calendar_export_queue
        WHERE calendar_id = p_calendar_id
          AND export_status = 'pending'
    );
END;
$$ LANGUAGE plpgsql;

-- 캘린더의 내보내기 설정 조회 또는 생성
CREATE OR REPLACE FUNCTION get_or_create_export_settings(p_calendar_id UUID, p_user_id UUID)
RETURNS TABLE(
    id UUID,
    auto_export BOOLEAN,
    enabled_platforms JSONB,
    export_all_events BOOLEAN
) AS $$
BEGIN
    -- 기존 설정 조회
    RETURN QUERY
    SELECT
        es.id,
        es.auto_export,
        es.enabled_platforms,
        es.export_all_events
    FROM calendar_export_settings es
    WHERE es.calendar_id = p_calendar_id
      AND es.user_id = p_user_id;

    -- 설정이 없으면 기본값으로 생성
    IF NOT FOUND THEN
        INSERT INTO calendar_export_settings (calendar_id, user_id)
        VALUES (p_calendar_id, p_user_id);

        RETURN QUERY
        SELECT
            es.id,
            es.auto_export,
            es.enabled_platforms,
            es.export_all_events
        FROM calendar_export_settings es
        WHERE es.calendar_id = p_calendar_id
          AND es.user_id = p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 내보내기 큐 항목들을 배치로 처리 완료 표시
CREATE OR REPLACE FUNCTION mark_export_queue_completed(
    p_queue_ids UUID[],
    p_target_platforms JSONB,
    p_results JSONB
)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE calendar_export_queue
    SET
        export_status = 'completed',
        target_platforms = p_target_platforms,
        export_results = p_results,
        processed_at = NOW()
    WHERE id = ANY(p_queue_ids)
      AND export_status = 'pending';

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================
-- RLS (Row Level Security) 정책
-- =====================================

-- calendar_export_settings RLS
ALTER TABLE calendar_export_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access their own export settings" ON calendar_export_settings
    FOR ALL USING (auth.uid() = user_id);

-- calendar_export_queue RLS
ALTER TABLE calendar_export_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access their own export queue" ON calendar_export_queue
    FOR ALL USING (auth.uid() = user_id);

-- calendar_export_logs RLS
ALTER TABLE calendar_export_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access their own export logs" ON calendar_export_logs
    FOR ALL USING (auth.uid() = user_id);

-- platform_event_mapping RLS
ALTER TABLE platform_event_mapping ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access their own platform mappings" ON platform_event_mapping
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM calendars c
            WHERE c.id = platform_event_mapping.calendar_id
            AND c.owner_id = auth.uid()::text
        )
    );

-- =====================================
-- 테이블 코멘트
-- =====================================

COMMENT ON TABLE calendar_export_settings IS '캘린더별 내보내기 설정';
COMMENT ON TABLE calendar_export_queue IS '변경사항 추적 및 내보내기 큐';
COMMENT ON TABLE calendar_export_logs IS '내보내기 작업 로그';
COMMENT ON TABLE platform_event_mapping IS '플랫폼별 이벤트 매핑 정보';

COMMENT ON COLUMN calendar_export_queue.change_type IS '변경 타입: created, updated, deleted';
COMMENT ON COLUMN calendar_export_queue.export_status IS '내보내기 상태: pending, processing, completed, failed';
COMMENT ON COLUMN calendar_export_logs.operation_type IS '작업 타입: export_batch, sync_single';
COMMENT ON COLUMN platform_event_mapping.sync_status IS '동기화 상태: synced, pending, failed, deleted';