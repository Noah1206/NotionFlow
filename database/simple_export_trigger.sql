-- 권한 문제 없는 단순한 트리거 함수
CREATE OR REPLACE FUNCTION track_calendar_event_changes()
RETURNS TRIGGER AS $$
DECLARE
    change_type_val VARCHAR(20);
    event_data_val JSONB;
    summary_val TEXT;
    target_user_id UUID;
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

    -- 사용자 존재 확인 없이 바로 삽입 시도 (실패해도 무시)
    BEGIN
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
    EXCEPTION
        WHEN foreign_key_violation THEN
            -- 외래키 위반 시 무시하고 계속 진행
            NULL;
        WHEN insufficient_privilege THEN
            -- 권한 부족 시 무시하고 계속 진행
            NULL;
    END;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;