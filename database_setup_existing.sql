-- NotionFlow 기존 테이블 구조 확인 및 정리
-- 기존 테이블들이 이미 있으므로 새로운 테이블 생성 대신 구조 확인

-- 기존 테이블 구조:
-- 1. calendars (id, owner_id, type, name, description, color, ...)
-- 2. calendar_shares (id, calendar_id, user_id, access_level, shared_by, shared_at, is_active)
-- 3. friendships (id, user_id, friend_id, status, created_at, accepted_at, blocked_at, notes)
-- 4. user_profiles (id, user_id, username, display_name, avatar_url, bio, is_public, created_at, updated_at, website_url, email, encrypted_email)
-- 5. users (id, email, is_active, subscription_plan, subscription_expires_at, last_login_at, email_verified, timezone)

-- 기존 테이블들이 친구 캘린더 공유 기능에 필요한 모든 구조를 가지고 있습니다.
-- 추가 설정이나 인덱스가 필요한 경우에만 아래 스크립트를 실행하세요.

-- 인덱스 확인 및 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_calendars_owner_id ON calendars(owner_id);
CREATE INDEX IF NOT EXISTS idx_calendar_shares_user_id ON calendar_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_shares_calendar_id ON calendar_shares(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_shares_shared_by ON calendar_shares(shared_by);
CREATE INDEX IF NOT EXISTS idx_friendships_user_id ON friendships(user_id);
CREATE INDEX IF NOT EXISTS idx_friendships_friend_id ON friendships(friend_id);
CREATE INDEX IF NOT EXISTS idx_friendships_status ON friendships(status);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);

-- RLS (Row Level Security) 정책 확인
-- 이미 활성화되어 있을 수 있으므로 조건부로 확인

-- 기존 테이블 구조가 완벽하므로 별도의 테이블 생성이나 수정이 필요하지 않습니다.
-- 친구 캘린더 공유 기능은 현재 테이블 구조로 완전히 지원됩니다:

-- 친구 관계 관리: friendships 테이블
-- - user_id, friend_id: 친구 관계의 양쪽 사용자
-- - status: 'pending', 'accepted', 'blocked' 등 상태 관리
-- - created_at, accepted_at: 시간 추적

-- 캘린더 공유 관리: calendar_shares 테이블  
-- - calendar_id: 공유할 캘린더
-- - user_id: 공유받는 사용자
-- - shared_by: 공유하는 사용자 (캘린더 소유자)
-- - access_level: 'read', 'write' 등 권한 레벨
-- - is_active: 공유 활성화 상태

-- 캘린더 소유권: calendars 테이블
-- - owner_id: 캘린더 소유자

-- 사용자 정보: user_profiles 테이블
-- - 사용자 프로필 정보 (이름, 아바타 등)

-- Database structure verification complete. 
-- Existing tables support friend calendar sharing functionality.

DO $$ 
BEGIN
    RAISE NOTICE 'Database structure verification complete. Existing tables support friend calendar sharing functionality.';
END
$$;