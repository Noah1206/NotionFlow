-- 수정된 트리거 함수 (사용자 존재 확인 포함)
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