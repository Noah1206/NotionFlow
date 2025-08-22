-- NotionFlow 데이터베이스 설정
-- 필요한 테이블들을 생성합니다

-- 기존 테이블이 있다면 제약조건을 먼저 정리
DO $$
BEGIN
    -- 기존 외래키 제약조건들 삭제 (있다면)
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
              WHERE constraint_name = 'fk_friends_user_id') THEN
        ALTER TABLE friends DROP CONSTRAINT fk_friends_user_id;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
              WHERE constraint_name = 'fk_friends_friend_id') THEN
        ALTER TABLE friends DROP CONSTRAINT fk_friends_friend_id;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
              WHERE constraint_name = 'fk_friend_requests_from_user') THEN
        ALTER TABLE friend_requests DROP CONSTRAINT fk_friend_requests_from_user;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
              WHERE constraint_name = 'fk_friend_requests_to_user') THEN
        ALTER TABLE friend_requests DROP CONSTRAINT fk_friend_requests_to_user;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
              WHERE constraint_name = 'fk_calendar_shares_owner_id') THEN
        ALTER TABLE calendar_shares DROP CONSTRAINT fk_calendar_shares_owner_id;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
              WHERE constraint_name = 'fk_calendar_shares_shared_with_user_id') THEN
        ALTER TABLE calendar_shares DROP CONSTRAINT fk_calendar_shares_shared_with_user_id;
    END IF;
END
$$;

-- 1. user_profiles 테이블 (사용자 프로필 정보)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    display_name VARCHAR(100),
    email VARCHAR(255),
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- auth.users 테이블이 존재하는 경우에만 외래키 추가
-- 기존 데이터 정합성 문제가 있을 수 있으므로 조건부로 처리
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'users') THEN
        -- 먼저 orphaned 데이터가 있는지 확인
        IF NOT EXISTS (
            SELECT 1 FROM user_profiles up 
            LEFT JOIN auth.users au ON up.user_id = au.id 
            WHERE au.id IS NULL
        ) THEN
            -- orphaned 데이터가 없으면 외래키 제약조건 추가
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name = 'fk_user_profiles_auth_users') THEN
                ALTER TABLE user_profiles 
                ADD CONSTRAINT fk_user_profiles_auth_users 
                FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
            END IF;
        ELSE
            -- orphaned 데이터가 있으면 경고 메시지만 출력
            RAISE NOTICE 'Warning: user_profiles 테이블에 auth.users에 존재하지 않는 user_id가 있어 외래키 제약조건을 추가할 수 없습니다.';
        END IF;
    END IF;
END
$$;

-- 2. friends 테이블 (친구 관계)
CREATE TABLE IF NOT EXISTS friends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    friend_id UUID NOT NULL,
    status VARCHAR(20) DEFAULT 'accepted',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, friend_id)
);

-- 3. friend_requests 테이블 (친구 요청)
CREATE TABLE IF NOT EXISTS friend_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_user_id UUID NOT NULL,
    to_user_id UUID NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, declined
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(from_user_id, to_user_id)
);

-- 4. calendars 테이블 owner_id 컬럼 확인 및 추가
DO $$
BEGIN
    -- calendars 테이블에 owner_id 컬럼이 없으면 추가
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendars') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'calendars' AND column_name = 'owner_id') THEN
            ALTER TABLE calendars ADD COLUMN owner_id UUID;
            RAISE NOTICE 'Added owner_id column to calendars table';
        END IF;
    ELSE
        RAISE NOTICE 'calendars 테이블이 존재하지 않습니다. 먼저 calendars 테이블을 생성해주세요.';
    END IF;
END
$$;

-- 5. calendar_shares 테이블 (캘린더 공유)
CREATE TABLE IF NOT EXISTS calendar_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id UUID NOT NULL,
    owner_id UUID NOT NULL,
    shared_with_user_id UUID NOT NULL,
    shared_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    can_edit BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(calendar_id, shared_with_user_id)
);

-- 외래키 제약조건들을 추가 (테이블 생성 후)
-- 제약조건 추가 시 오류가 발생해도 계속 진행하도록 처리
DO $$
BEGIN
    -- friends 테이블 외래키 (안전하게 추가)
    BEGIN
        ALTER TABLE friends 
        ADD CONSTRAINT fk_friends_user_id 
        FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN
        -- 이미 존재하는 경우 무시
        NULL;
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Warning: friends.user_id에 대한 외래키 제약조건을 추가할 수 없습니다 (데이터 무결성 문제)';
    WHEN OTHERS THEN
        RAISE NOTICE 'Warning: friends.user_id 외래키 추가 중 오류: %', SQLERRM;
    END;
    
    BEGIN
        ALTER TABLE friends 
        ADD CONSTRAINT fk_friends_friend_id 
        FOREIGN KEY (friend_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Warning: friends.friend_id에 대한 외래키 제약조건을 추가할 수 없습니다 (데이터 무결성 문제)';
    WHEN OTHERS THEN
        RAISE NOTICE 'Warning: friends.friend_id 외래키 추가 중 오류: %', SQLERRM;
    END;
    
    -- friend_requests 테이블 외래키
    BEGIN
        ALTER TABLE friend_requests 
        ADD CONSTRAINT fk_friend_requests_from_user 
        FOREIGN KEY (from_user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Warning: friend_requests.from_user_id에 대한 외래키 제약조건을 추가할 수 없습니다';
    WHEN OTHERS THEN
        RAISE NOTICE 'Warning: friend_requests.from_user_id 외래키 추가 중 오류: %', SQLERRM;
    END;
    
    BEGIN
        ALTER TABLE friend_requests 
        ADD CONSTRAINT fk_friend_requests_to_user 
        FOREIGN KEY (to_user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Warning: friend_requests.to_user_id에 대한 외래키 제약조건을 추가할 수 없습니다';
    WHEN OTHERS THEN
        RAISE NOTICE 'Warning: friend_requests.to_user_id 외래키 추가 중 오류: %', SQLERRM;
    END;
    
    -- calendar_shares 테이블 외래키
    BEGIN
        IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendars') THEN
            -- Check if calendars table has 'id' column
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'calendars' AND column_name = 'id') THEN
                ALTER TABLE calendar_shares 
                ADD CONSTRAINT fk_calendar_shares_calendar_id 
                FOREIGN KEY (calendar_id) REFERENCES calendars(id) ON DELETE CASCADE;
            ELSE
                RAISE NOTICE 'Warning: calendars 테이블에 id 컬럼이 없어 외래키를 추가할 수 없습니다';
            END IF;
        ELSE
            RAISE NOTICE 'Warning: calendars 테이블이 존재하지 않아 외래키를 추가할 수 없습니다';
        END IF;
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    WHEN OTHERS THEN
        RAISE NOTICE 'Warning: calendar_shares.calendar_id 외래키 추가 중 오류: %', SQLERRM;
    END;
    
    BEGIN
        ALTER TABLE calendar_shares 
        ADD CONSTRAINT fk_calendar_shares_owner_id 
        FOREIGN KEY (owner_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Warning: calendar_shares.owner_id에 대한 외래키 제약조건을 추가할 수 없습니다';
    WHEN OTHERS THEN
        RAISE NOTICE 'Warning: calendar_shares.owner_id 외래키 추가 중 오류: %', SQLERRM;
    END;
    
    BEGIN
        ALTER TABLE calendar_shares 
        ADD CONSTRAINT fk_calendar_shares_shared_with_user_id 
        FOREIGN KEY (shared_with_user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Warning: calendar_shares.shared_with_user_id에 대한 외래키 제약조건을 추가할 수 없습니다';
    WHEN OTHERS THEN
        RAISE NOTICE 'Warning: calendar_shares.shared_with_user_id 외래키 추가 중 오류: %', SQLERRM;
    END;
    
    RAISE NOTICE 'Database setup completed. Check any warning messages above.';
END
$$;

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_display_name ON user_profiles(display_name);

CREATE INDEX IF NOT EXISTS idx_friends_user_id ON friends(user_id);
CREATE INDEX IF NOT EXISTS idx_friends_friend_id ON friends(friend_id);
CREATE INDEX IF NOT EXISTS idx_friends_status ON friends(status);

CREATE INDEX IF NOT EXISTS idx_friend_requests_to_user ON friend_requests(to_user_id);
CREATE INDEX IF NOT EXISTS idx_friend_requests_from_user ON friend_requests(from_user_id);
CREATE INDEX IF NOT EXISTS idx_friend_requests_status ON friend_requests(status);

CREATE INDEX IF NOT EXISTS idx_calendar_shares_owner ON calendar_shares(owner_id);
CREATE INDEX IF NOT EXISTS idx_calendar_shares_shared_with ON calendar_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_shares_calendar ON calendar_shares(calendar_id);

-- RLS (Row Level Security) 정책 설정
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE friends ENABLE ROW LEVEL SECURITY;
ALTER TABLE friend_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_shares ENABLE ROW LEVEL SECURITY;

-- user_profiles 정책 (기존 정책이 있으면 삭제 후 재생성)
DROP POLICY IF EXISTS "Users can view all profiles" ON user_profiles;
CREATE POLICY "Users can view all profiles" ON user_profiles
    FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own profile" ON user_profiles;
CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- friends 정책
DROP POLICY IF EXISTS "Users can view own friendships" ON friends;
CREATE POLICY "Users can view own friendships" ON friends
    FOR SELECT USING (auth.uid() = user_id OR auth.uid() = friend_id);

DROP POLICY IF EXISTS "Users can manage own friendships" ON friends;
CREATE POLICY "Users can manage own friendships" ON friends
    FOR ALL USING (auth.uid() = user_id);

-- friend_requests 정책
DROP POLICY IF EXISTS "Users can view requests to/from them" ON friend_requests;
CREATE POLICY "Users can view requests to/from them" ON friend_requests
    FOR SELECT USING (auth.uid() = from_user_id OR auth.uid() = to_user_id);

DROP POLICY IF EXISTS "Users can send friend requests" ON friend_requests;
CREATE POLICY "Users can send friend requests" ON friend_requests
    FOR INSERT WITH CHECK (auth.uid() = from_user_id);

DROP POLICY IF EXISTS "Users can respond to requests to them" ON friend_requests;
CREATE POLICY "Users can respond to requests to them" ON friend_requests
    FOR UPDATE USING (auth.uid() = to_user_id);

-- calendar_shares 정책
DROP POLICY IF EXISTS "Users can view shares involving them" ON calendar_shares;
CREATE POLICY "Users can view shares involving them" ON calendar_shares
    FOR SELECT USING (auth.uid() = owner_id OR auth.uid() = shared_with_user_id);

DROP POLICY IF EXISTS "Owners can manage calendar shares" ON calendar_shares;
CREATE POLICY "Owners can manage calendar shares" ON calendar_shares
    FOR ALL USING (auth.uid() = owner_id);

-- 업데이트 시간 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 업데이트 트리거 생성
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 테스트 데이터 삽입 (옵셔널)
-- INSERT INTO user_profiles (user_id, username, display_name, email) VALUES
-- ('user_001', 'kim123', '김철수', 'kim@example.com'),
-- ('user_002', 'lee456', '이영희', 'lee@example.com'),
-- ('user_003', 'park789', '박민수', 'park@example.com')
-- ON CONFLICT (user_id) DO NOTHING;