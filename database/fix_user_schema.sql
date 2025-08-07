-- Fix User Schema Issues
-- 사용자 관련 테이블 스키마 수정

-- 1. users 테이블 RLS 정책 수정
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- 2. user_profiles 외래키 제약조건 임시 비활성화 (선택사항)
-- ALTER TABLE user_profiles DROP CONSTRAINT IF EXISTS user_profiles_user_id_fkey;

-- 3. user_subscriptions 테이블에 is_active 컬럼 추가 (없는 경우)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_subscriptions' AND column_name = 'is_active') THEN
        ALTER TABLE user_subscriptions ADD COLUMN is_active BOOLEAN DEFAULT true;
    END IF;
END $$;

-- 4. 누락된 users 레코드 생성을 위한 트리거 함수 (선택사항)
CREATE OR REPLACE FUNCTION create_user_if_not_exists()
RETURNS TRIGGER AS $$
BEGIN
    -- user_profiles에 삽입될 때 users 테이블에 레코드가 없으면 생성
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = NEW.user_id) THEN
        INSERT INTO users (id, email, created_at)
        VALUES (NEW.user_id, 'temp@example.com', NOW())
        ON CONFLICT (id) DO NOTHING;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. 트리거 생성 (선택사항)
DROP TRIGGER IF EXISTS ensure_user_exists ON user_profiles;
CREATE TRIGGER ensure_user_exists
    BEFORE INSERT ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION create_user_if_not_exists();

-- 6. 임시로 모든 테이블의 RLS 비활성화 (개발용)
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions DISABLE ROW LEVEL SECURITY;

COMMIT;