-- 임시로 export queue 트리거 비활성화
DROP TRIGGER IF EXISTS trigger_track_calendar_events_changes ON calendar_events;

-- 필요시 다시 활성화할 때 사용
-- CREATE TRIGGER trigger_track_calendar_events_changes
--     AFTER INSERT OR UPDATE OR DELETE ON calendar_events
--     FOR EACH ROW
--     EXECUTE FUNCTION track_calendar_event_changes();