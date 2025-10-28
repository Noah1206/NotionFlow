-- ============================================
-- 📋 Event Validation System Schema
-- 3-tier validation system for duplicate prevention
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Event validation tracking table
CREATE TABLE IF NOT EXISTS event_validation_history (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,

    -- Event identification
    source_event_id UUID NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,
    target_platform VARCHAR(50) NOT NULL, -- google, notion, apple
    target_event_id VARCHAR(255), -- External platform event ID after sync

    -- Validation results
    tier1_db_check BOOLEAN NOT NULL, -- Event exists in DB
    tier2_trash_check BOOLEAN NOT NULL, -- Event not in trash
    tier3_duplicate_check BOOLEAN NOT NULL, -- No duplicate content

    -- Content fingerprinting for duplicate detection
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 hash of title+date+time
    normalized_title VARCHAR(255) NOT NULL, -- Lowercased, trimmed title
    event_date DATE NOT NULL, -- Date for comparison
    event_start_time TIME, -- Time for comparison

    -- Validation metadata
    validation_status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, approved, rejected, synced
    rejection_reason TEXT, -- Why validation failed
    case_classification VARCHAR(50), -- new_event, content_change, date_change, deletion

    -- Sync tracking
    sync_attempted_at TIMESTAMP WITH TIME ZONE,
    sync_completed_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'pending', -- pending, success, failed
    sync_error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_validation_attempt UNIQUE (user_id, source_event_id, target_platform, content_hash),
    CONSTRAINT valid_validation_status CHECK (validation_status IN ('pending', 'approved', 'rejected', 'synced')),
    CONSTRAINT valid_sync_status CHECK (sync_status IN ('pending', 'success', 'failed'))
);

-- Event content fingerprints table for efficient duplicate detection
CREATE TABLE IF NOT EXISTS event_content_fingerprints (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,

    -- Content fingerprint
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 hash
    normalized_title VARCHAR(255) NOT NULL,
    event_date DATE NOT NULL,
    event_start_time TIME,

    -- Source tracking
    source_event_id UUID, -- Can be NULL for external events
    external_event_id VARCHAR(255), -- External platform event ID

    -- Status
    is_active BOOLEAN DEFAULT true, -- false if event was deleted
    last_verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_fingerprint UNIQUE (user_id, platform, content_hash),
    CONSTRAINT fingerprint_source_check CHECK (
        (source_event_id IS NOT NULL) OR (external_event_id IS NOT NULL)
    )
);

-- Event sync queue for batch processing
CREATE TABLE IF NOT EXISTS event_sync_queue (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,

    -- Batch information
    batch_id UUID NOT NULL DEFAULT uuid_generate_v4(),
    priority INTEGER DEFAULT 5, -- 1-10, lower is higher priority

    -- Event data
    source_event_id UUID NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,
    target_platform VARCHAR(50) NOT NULL,
    sync_action VARCHAR(20) NOT NULL, -- create, update, delete

    -- Queue status
    status VARCHAR(20) DEFAULT 'queued', -- queued, processing, completed, failed
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Processing metadata
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,

    -- Validation reference
    validation_id UUID REFERENCES event_validation_history(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_queue_status CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    CONSTRAINT valid_sync_action CHECK (sync_action IN ('create', 'update', 'delete'))
);

-- ============================================
-- 📊 INDEXES (Performance Optimization)
-- ============================================

-- Validation history indexes
CREATE INDEX IF NOT EXISTS idx_validation_history_user_id ON event_validation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_validation_history_calendar_id ON event_validation_history(calendar_id);
CREATE INDEX IF NOT EXISTS idx_validation_history_source_event ON event_validation_history(source_event_id);
CREATE INDEX IF NOT EXISTS idx_validation_history_target_platform ON event_validation_history(target_platform);
CREATE INDEX IF NOT EXISTS idx_validation_history_content_hash ON event_validation_history(content_hash);
CREATE INDEX IF NOT EXISTS idx_validation_history_status ON event_validation_history(validation_status);
CREATE INDEX IF NOT EXISTS idx_validation_history_date ON event_validation_history(event_date);

-- Fingerprints indexes
CREATE INDEX IF NOT EXISTS idx_fingerprints_user_platform ON event_content_fingerprints(user_id, platform);
CREATE INDEX IF NOT EXISTS idx_fingerprints_hash ON event_content_fingerprints(content_hash);
CREATE INDEX IF NOT EXISTS idx_fingerprints_date ON event_content_fingerprints(event_date);
CREATE INDEX IF NOT EXISTS idx_fingerprints_title ON event_content_fingerprints(normalized_title);
CREATE INDEX IF NOT EXISTS idx_fingerprints_active ON event_content_fingerprints(is_active);

-- Sync queue indexes
CREATE INDEX IF NOT EXISTS idx_sync_queue_user_id ON event_sync_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_batch_id ON event_sync_queue(batch_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON event_sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_priority ON event_sync_queue(priority, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_sync_queue_platform ON event_sync_queue(target_platform);

-- ============================================
-- 🔄 TRIGGERS (Auto-update timestamps)
-- ============================================

-- Updated at triggers
CREATE TRIGGER update_validation_history_updated_at
    BEFORE UPDATE ON event_validation_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fingerprints_updated_at
    BEFORE UPDATE ON event_content_fingerprints
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sync_queue_updated_at
    BEFORE UPDATE ON event_sync_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 🔐 ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS
ALTER TABLE event_validation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_content_fingerprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_sync_queue ENABLE ROW LEVEL SECURITY;

-- User access policies
CREATE POLICY "Users can view their own validation history" ON event_validation_history
    FOR SELECT USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert their own validation history" ON event_validation_history
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update their own validation history" ON event_validation_history
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "Users can view their own fingerprints" ON event_content_fingerprints
    FOR SELECT USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert their own fingerprints" ON event_content_fingerprints
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update their own fingerprints" ON event_content_fingerprints
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "Users can view their own sync queue" ON event_sync_queue
    FOR SELECT USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert their own sync queue" ON event_sync_queue
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update their own sync queue" ON event_sync_queue
    FOR UPDATE USING (user_id = auth.uid()::text);

-- Service role policies
CREATE POLICY "Service role full access validation" ON event_validation_history
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access fingerprints" ON event_content_fingerprints
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access queue" ON event_sync_queue
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- 🔧 UTILITY FUNCTIONS
-- ============================================

-- Function to generate content hash
CREATE OR REPLACE FUNCTION generate_content_hash(
    p_title TEXT,
    p_event_date DATE,
    p_event_time TIME DEFAULT NULL
)
RETURNS VARCHAR(64) AS $$
BEGIN
    -- Normalize and hash content for duplicate detection
    RETURN encode(
        digest(
            LOWER(TRIM(COALESCE(p_title, ''))) || '|' ||
            COALESCE(p_event_date::text, '') || '|' ||
            COALESCE(p_event_time::text, ''),
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to check if event is in localStorage trash
CREATE OR REPLACE FUNCTION is_event_in_trash(
    p_event_id UUID,
    p_calendar_id UUID
)
RETURNS BOOLEAN AS $$
BEGIN
    -- This is a placeholder function since localStorage check must be done client-side
    -- In actual implementation, this check will be performed in the application layer
    -- Return false by default (assume not in trash)
    RETURN false;
END;
$$ LANGUAGE plpgsql;

-- Function to perform 3-tier validation
CREATE OR REPLACE FUNCTION validate_event_for_sync(
    p_user_id TEXT,
    p_event_id UUID,
    p_target_platform VARCHAR(50),
    p_is_in_trash BOOLEAN DEFAULT false -- Passed from client-side trash check
)
RETURNS TABLE (
    tier1_pass BOOLEAN,
    tier2_pass BOOLEAN,
    tier3_pass BOOLEAN,
    validation_result VARCHAR(20),
    rejection_reason TEXT,
    case_classification VARCHAR(50),
    content_hash VARCHAR(64)
) AS $$
DECLARE
    v_event_record RECORD;
    v_content_hash VARCHAR(64);
    v_existing_fingerprint RECORD;
    v_tier1_pass BOOLEAN := false;
    v_tier2_pass BOOLEAN := false;
    v_tier3_pass BOOLEAN := false;
    v_validation_result VARCHAR(20) := 'rejected';
    v_rejection_reason TEXT := '';
    v_case_classification VARCHAR(50) := 'unknown';
BEGIN
    -- Tier 1: Check if event exists in DB
    SELECT ce.*, c.name as calendar_name INTO v_event_record
    FROM calendar_events ce
    JOIN calendars c ON ce.calendar_id = c.id
    WHERE ce.id = p_event_id
      AND ce.user_id = p_user_id
      AND ce.status != 'cancelled';

    IF FOUND THEN
        v_tier1_pass := true;

        -- Tier 2: Check if event is in trash (passed from client)
        IF NOT p_is_in_trash THEN
            v_tier2_pass := true;

            -- Generate content hash for Tier 3 check
            v_content_hash := generate_content_hash(
                v_event_record.title,
                COALESCE(v_event_record.start_date, v_event_record.start_datetime::date),
                CASE
                    WHEN v_event_record.is_all_day THEN NULL
                    ELSE v_event_record.start_datetime::time
                END
            );

            -- Tier 3: Check for duplicate content on target platform
            SELECT * INTO v_existing_fingerprint
            FROM event_content_fingerprints
            WHERE user_id = p_user_id
              AND platform = p_target_platform
              AND content_hash = v_content_hash
              AND is_active = true;

            IF NOT FOUND THEN
                v_tier3_pass := true;
                v_validation_result := 'approved';
                v_case_classification := 'new_event';
            ELSE
                v_rejection_reason := 'Duplicate content detected on target platform';
                v_case_classification := 'duplicate_content';
            END IF;
        ELSE
            v_rejection_reason := 'Event is in trash';
            v_case_classification := 'trashed_event';
        END IF;
    ELSE
        v_rejection_reason := 'Event not found in database or cancelled';
        v_case_classification := 'missing_event';
    END IF;

    -- Return validation results
    RETURN QUERY SELECT
        v_tier1_pass,
        v_tier2_pass,
        v_tier3_pass,
        v_validation_result,
        v_rejection_reason,
        v_case_classification,
        COALESCE(v_content_hash, '');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to record validation attempt
CREATE OR REPLACE FUNCTION record_validation_attempt(
    p_user_id TEXT,
    p_calendar_id UUID,
    p_source_event_id UUID,
    p_target_platform VARCHAR(50),
    p_tier1_result BOOLEAN,
    p_tier2_result BOOLEAN,
    p_tier3_result BOOLEAN,
    p_validation_status VARCHAR(20),
    p_rejection_reason TEXT,
    p_case_classification VARCHAR(50),
    p_content_hash VARCHAR(64)
)
RETURNS UUID AS $$
DECLARE
    v_validation_id UUID;
    v_event_record RECORD;
BEGIN
    -- Get event details for fingerprinting
    SELECT * INTO v_event_record
    FROM calendar_events
    WHERE id = p_source_event_id AND user_id = p_user_id;

    -- Insert validation record
    INSERT INTO event_validation_history (
        user_id,
        calendar_id,
        source_event_id,
        target_platform,
        tier1_db_check,
        tier2_trash_check,
        tier3_duplicate_check,
        content_hash,
        normalized_title,
        event_date,
        event_start_time,
        validation_status,
        rejection_reason,
        case_classification
    ) VALUES (
        p_user_id,
        p_calendar_id,
        p_source_event_id,
        p_target_platform,
        p_tier1_result,
        p_tier2_result,
        p_tier3_result,
        p_content_hash,
        LOWER(TRIM(COALESCE(v_event_record.title, ''))),
        COALESCE(v_event_record.start_date, v_event_record.start_datetime::date),
        CASE
            WHEN v_event_record.is_all_day THEN NULL
            ELSE v_event_record.start_datetime::time
        END,
        p_validation_status,
        p_rejection_reason,
        p_case_classification
    ) RETURNING id INTO v_validation_id;

    -- If validation passed, create fingerprint for future duplicate detection
    IF p_validation_status = 'approved' AND p_tier3_result THEN
        INSERT INTO event_content_fingerprints (
            user_id,
            platform,
            content_hash,
            normalized_title,
            event_date,
            event_start_time,
            source_event_id
        ) VALUES (
            p_user_id,
            p_target_platform,
            p_content_hash,
            LOWER(TRIM(COALESCE(v_event_record.title, ''))),
            COALESCE(v_event_record.start_date, v_event_record.start_datetime::date),
            CASE
                WHEN v_event_record.is_all_day THEN NULL
                ELSE v_event_record.start_datetime::time
            END,
            p_source_event_id
        ) ON CONFLICT (user_id, platform, content_hash) DO NOTHING;
    END IF;

    RETURN v_validation_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 📝 TABLE COMMENTS (Documentation)
-- ============================================

COMMENT ON TABLE event_validation_history IS '3-tier event validation tracking for sync operations';
COMMENT ON TABLE event_content_fingerprints IS 'Content fingerprints for duplicate detection across platforms';
COMMENT ON TABLE event_sync_queue IS 'Queue for batch processing of validated events';

COMMENT ON COLUMN event_validation_history.tier1_db_check IS 'Tier 1: Event exists in database';
COMMENT ON COLUMN event_validation_history.tier2_trash_check IS 'Tier 2: Event not in localStorage trash';
COMMENT ON COLUMN event_validation_history.tier3_duplicate_check IS 'Tier 3: No duplicate content on target platform';
COMMENT ON COLUMN event_content_fingerprints.content_hash IS 'SHA-256 hash of normalized title + date + time';

-- Grant necessary permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON event_validation_history TO service_role;
GRANT ALL ON event_content_fingerprints TO service_role;
GRANT ALL ON event_sync_queue TO service_role;

-- ============================================
-- 🎉 EVENT VALIDATION SCHEMA COMPLETE
-- ============================================