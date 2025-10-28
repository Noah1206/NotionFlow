-- 모든 캘린더 내보내기 관련 트리거 비활성화

-- 1. 메인 이벤트 변경 추적 트리거 제거
DROP TRIGGER IF EXISTS trigger_track_calendar_events_changes ON calendar_events;

-- 2. 관련 트리거 함수도 제거 (선택적)
-- DROP FUNCTION IF EXISTS track_calendar_event_changes();

-- 3. 다른 export 관련 트리거들도 비활성화
DROP TRIGGER IF EXISTS trigger_update_is_processed ON calendar_export_queue;
DROP TRIGGER IF EXISTS trigger_set_date_created ON calendar_export_logs;

-- 알림: 캘린더 내보내기 기능이 필요할 때는 수동으로 API를 호출하세요.
-- 트리거 없이도 내보내기 API는 정상 작동합니다.