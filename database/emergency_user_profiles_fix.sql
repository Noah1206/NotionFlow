-- 🚨 긴급 수정: user_profiles RLS 정책 문제 해결
-- 사용자 프로필 생성 허용

-- 현재 user_profiles 테이블 상태 확인
SELECT 
    tablename,
    rowsecurity as "RLS 활성화됨"
FROM pg_tables 
WHERE tablename = 'user_profiles';

-- 현재 적용된 정책들 확인
SELECT 
    policyname as "정책명",
    cmd as "명령",
    qual as "조건"
FROM pg_policies 
WHERE tablename = 'user_profiles';

-- ⚠️ 기존 잘못된 정책 삭제 (있다면)
DROP POLICY IF EXISTS "user_profiles_policy" ON user_profiles;
DROP POLICY IF EXISTS "Users can manage their own profiles" ON user_profiles;

-- ✅ 올바른 정책 생성
-- 1. 사용자는 자신의 프로필만 볼 수 있음
CREATE POLICY "Users can view own profile" 
ON user_profiles FOR SELECT 
USING (user_id = auth.uid());

-- 2. 🔥 중요: 새 사용자가 프로필을 생성할 수 있음
CREATE POLICY "Users can create own profile" 
ON user_profiles FOR INSERT 
WITH CHECK (user_id = auth.uid());

-- 3. 사용자는 자신의 프로필만 수정할 수 있음
CREATE POLICY "Users can update own profile" 
ON user_profiles FOR UPDATE 
USING (user_id = auth.uid());

-- 4. 사용자는 자신의 프로필만 삭제할 수 있음
CREATE POLICY "Users can delete own profile" 
ON user_profiles FOR DELETE 
USING (user_id = auth.uid());

-- ✅ 결과 확인
SELECT 
    policyname as "새 정책명",
    cmd as "명령",
    permissive as "허용여부"
FROM pg_policies 
WHERE tablename = 'user_profiles'
ORDER BY cmd;