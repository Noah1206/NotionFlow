-- 🧠 Smart Detection Cache Table
-- 플랫폼 연결 및 동기화 최적화를 위한 스마트 캐시 시스템

-- 스마트 감지 캐시 테이블 생성
CREATE TABLE IF NOT EXISTS smart_detection_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    
    -- 연결 정보
    connection_status VARCHAR(20) DEFAULT 'disconnected' CHECK (connection_status IN ('connected', 'disconnected', 'connecting', 'error')),
    last_connection_attempt TIMESTAMPTZ,
    connection_success_rate DECIMAL(5,2) DEFAULT 0.00,
    
    -- API 정보 캐시
    api_endpoint_url TEXT,
    api_response_time_ms INTEGER DEFAULT 0,
    api_rate_limit_remaining INTEGER DEFAULT 1000,
    api_rate_limit_reset TIMESTAMPTZ,
    
    -- 동기화 통계
    total_sync_count INTEGER DEFAULT 0,
    successful_sync_count INTEGER DEFAULT 0,
    failed_sync_count INTEGER DEFAULT 0,
    last_sync_timestamp TIMESTAMPTZ,
    last_sync_duration_ms INTEGER DEFAULT 0,
    last_sync_items_count INTEGER DEFAULT 0,
    
    -- 성능 최적화 데이터
    average_response_time_ms DECIMAL(8,2) DEFAULT 0.00,
    preferred_sync_time_slot VARCHAR(50), -- 'morning', 'afternoon', 'evening', 'night'
    optimal_batch_size INTEGER DEFAULT 10,
    
    -- 오류 추적
    last_error_message TEXT,
    last_error_timestamp TIMESTAMPTZ,
    consecutive_errors INTEGER DEFAULT 0,
    
    -- 사용자 행동 패턴
    user_interaction_frequency VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high'
    preferred_ui_theme VARCHAR(20) DEFAULT 'auto', -- 'light', 'dark', 'auto'
    
    -- 메타데이터
    platform_version VARCHAR(50),
    integration_type VARCHAR(30), -- 'oauth', 'api_token', 'webhook'
    cache_ttl_seconds INTEGER DEFAULT 3600,
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 인덱스를 위한 제약조건
    UNIQUE(user_id, platform)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_smart_cache_user_platform 
ON smart_detection_cache(user_id, platform);

CREATE INDEX IF NOT EXISTS idx_smart_cache_connection_status 
ON smart_detection_cache(connection_status);

CREATE INDEX IF NOT EXISTS idx_smart_cache_last_sync 
ON smart_detection_cache(last_sync_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_smart_cache_updated_at 
ON smart_detection_cache(updated_at DESC);

-- 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_smart_cache_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER smart_cache_update_timestamp
    BEFORE UPDATE ON smart_detection_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_smart_cache_timestamp();

-- RLS (Row Level Security) 정책
ALTER TABLE smart_detection_cache ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 캐시 데이터만 볼 수 있음
CREATE POLICY "Users can view their own cache data"
ON smart_detection_cache
FOR SELECT
USING (auth.uid() = user_id);

-- 사용자는 자신의 캐시 데이터만 삽입할 수 있음
CREATE POLICY "Users can insert their own cache data"
ON smart_detection_cache
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- 사용자는 자신의 캐시 데이터만 업데이트할 수 있음
CREATE POLICY "Users can update their own cache data"
ON smart_detection_cache
FOR UPDATE
USING (auth.uid() = user_id);

-- 사용자는 자신의 캐시 데이터만 삭제할 수 있음
CREATE POLICY "Users can delete their own cache data"
ON smart_detection_cache
FOR DELETE
USING (auth.uid() = user_id);

-- 플랫폼별 연결 통계 뷰
CREATE OR REPLACE VIEW platform_connection_stats AS
SELECT 
    platform,
    COUNT(*) as total_users,
    COUNT(CASE WHEN connection_status = 'connected' THEN 1 END) as connected_users,
    ROUND(
        COUNT(CASE WHEN connection_status = 'connected' THEN 1 END)::DECIMAL / 
        COUNT(*)::DECIMAL * 100, 2
    ) as connection_rate_percent,
    AVG(total_sync_count) as avg_sync_count,
    AVG(average_response_time_ms) as avg_response_time_ms
FROM smart_detection_cache
GROUP BY platform
ORDER BY connected_users DESC;

-- 사용자별 플랫폼 대시보드 뷰
CREATE OR REPLACE VIEW user_platform_dashboard AS
SELECT 
    user_id,
    platform,
    connection_status,
    total_sync_count,
    last_sync_timestamp,
    connection_success_rate,
    average_response_time_ms,
    consecutive_errors,
    CASE 
        WHEN connection_status = 'connected' AND consecutive_errors = 0 THEN 'healthy'
        WHEN connection_status = 'connected' AND consecutive_errors > 0 AND consecutive_errors < 3 THEN 'warning'
        WHEN consecutive_errors >= 3 OR connection_status = 'error' THEN 'critical'
        ELSE 'inactive'
    END as health_status,
    updated_at
FROM smart_detection_cache
ORDER BY user_id, platform;

-- 스마트 캐시 데이터 초기화 함수
CREATE OR REPLACE FUNCTION initialize_smart_cache(
    p_user_id UUID,
    p_platform VARCHAR(50),
    p_integration_type VARCHAR(30) DEFAULT 'oauth'
)
RETURNS UUID AS $$
DECLARE
    cache_id UUID;
BEGIN
    INSERT INTO smart_detection_cache (
        user_id,
        platform,
        integration_type,
        connection_status,
        created_at,
        updated_at
    ) VALUES (
        p_user_id,
        p_platform,
        p_integration_type,
        'disconnected',
        NOW(),
        NOW()
    )
    ON CONFLICT (user_id, platform) 
    DO UPDATE SET
        updated_at = NOW(),
        integration_type = p_integration_type
    RETURNING id INTO cache_id;
    
    RETURN cache_id;
END;
$$ LANGUAGE plpgsql;

-- 연결 성공 시 캐시 업데이트 함수
CREATE OR REPLACE FUNCTION update_connection_success(
    p_user_id UUID,
    p_platform VARCHAR(50),
    p_response_time_ms INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE smart_detection_cache 
    SET 
        connection_status = 'connected',
        last_connection_attempt = NOW(),
        connection_success_rate = LEAST(connection_success_rate + 10.0, 100.0),
        api_response_time_ms = COALESCE(p_response_time_ms, api_response_time_ms),
        average_response_time_ms = CASE 
            WHEN total_sync_count = 0 THEN COALESCE(p_response_time_ms, 0)
            ELSE (average_response_time_ms * total_sync_count + COALESCE(p_response_time_ms, 0)) / (total_sync_count + 1)
        END,
        consecutive_errors = 0,
        updated_at = NOW()
    WHERE user_id = p_user_id AND platform = p_platform;
END;
$$ LANGUAGE plpgsql;

-- 동기화 성공 시 캐시 업데이트 함수
CREATE OR REPLACE FUNCTION update_sync_success(
    p_user_id UUID,
    p_platform VARCHAR(50),
    p_items_count INTEGER DEFAULT 0,
    p_duration_ms INTEGER DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    UPDATE smart_detection_cache 
    SET 
        total_sync_count = total_sync_count + 1,
        successful_sync_count = successful_sync_count + 1,
        last_sync_timestamp = NOW(),
        last_sync_duration_ms = p_duration_ms,
        last_sync_items_count = p_items_count,
        connection_success_rate = LEAST(connection_success_rate + 5.0, 100.0),
        updated_at = NOW()
    WHERE user_id = p_user_id AND platform = p_platform;
END;
$$ LANGUAGE plpgsql;

-- 오류 발생 시 캐시 업데이트 함수
CREATE OR REPLACE FUNCTION update_connection_error(
    p_user_id UUID,
    p_platform VARCHAR(50),
    p_error_message TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE smart_detection_cache 
    SET 
        connection_status = CASE 
            WHEN consecutive_errors >= 2 THEN 'error'
            ELSE connection_status
        END,
        last_error_message = p_error_message,
        last_error_timestamp = NOW(),
        consecutive_errors = consecutive_errors + 1,
        connection_success_rate = GREATEST(connection_success_rate - 15.0, 0.0),
        updated_at = NOW()
    WHERE user_id = p_user_id AND platform = p_platform;
END;
$$ LANGUAGE plpgsql;

-- 캐시 정리 함수 (오래된 데이터 삭제)
CREATE OR REPLACE FUNCTION cleanup_old_cache_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM smart_detection_cache 
    WHERE updated_at < NOW() - INTERVAL '90 days'
    AND connection_status = 'disconnected';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 정기적 캐시 정리를 위한 스케줄러 (pg_cron 필요)
-- SELECT cron.schedule('cleanup-cache', '0 2 * * 0', 'SELECT cleanup_old_cache_data();');

COMMENT ON TABLE smart_detection_cache IS 'NotionFlow 플랫폼 연결 및 동기화 최적화를 위한 스마트 캐시 시스템';
COMMENT ON COLUMN smart_detection_cache.connection_success_rate IS '연결 성공률 (0-100%)';
COMMENT ON COLUMN smart_detection_cache.preferred_sync_time_slot IS '사용자의 선호 동기화 시간대';
COMMENT ON COLUMN smart_detection_cache.optimal_batch_size IS '최적 배치 처리 크기';
COMMENT ON COLUMN smart_detection_cache.user_interaction_frequency IS '사용자 상호작용 빈도';