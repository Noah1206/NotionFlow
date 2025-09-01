"""
테스트 사용자 데이터 추가 스크립트
"""

import sys
import os
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

try:
    from friends_db import friends_db
    print("✅ Friends DB imported successfully")
except ImportError as e:
    print(f"❌ Failed to import friends_db: {e}")
    sys.exit(1)

def add_test_users():
    """테스트 사용자들을 데이터베이스에 추가"""
    
    if not friends_db.is_available():
        print("❌ Friends database is not available")
        return False
    
    test_users = [
        {
            'id': 'user_001',
            'username': 'minsu_kim',
            'email': 'minsu@example.com',
            'avatar_url': None
        },
        {
            'id': 'user_002', 
            'username': 'younghee_lee',
            'email': 'younghee@gmail.com',
            'avatar_url': None
        },
        {
            'id': 'user_003',
            'username': 'chulsoo_park',
            'email': 'chulsoo@naver.com',
            'avatar_url': None
        },
        {
            'id': 'user_004',
            'username': 'jieun_choi',
            'email': 'jieun@daum.net',
            'avatar_url': None
        },
        {
            'id': 'user_005',
            'username': 'johnsmith',
            'email': 'john@company.com',
            'avatar_url': None
        },
        {
            'id': 'user_006',
            'username': 'alicejohnson',
            'email': 'alice@test.com',
            'avatar_url': None
        },
        {
            'id': 'user_007',
            'username': 'sumin_jung',
            'email': 'sumin@work.co.kr',
            'avatar_url': None
        },
        {
            'id': 'user_008',
            'username': 'davidwilson',
            'email': 'david@wilson.com',
            'avatar_url': None
        },
        {
            'id': 'user_009',
            'username': 'sarahchen',
            'email': 'sarah@chen.org',
            'avatar_url': None
        },
        {
            'id': 'user_010',
            'username': 'mikejohnson',
            'email': 'mike@example.org',
            'avatar_url': None
        }
    ]
    
    success_count = 0
    for user in test_users:
        try:
            result = friends_db.create_user_profile(
                user['id'],
                user['username'],
                user['email'],
                user['avatar_url']
            )
            
            if result:
                print(f"✅ Added user: {user['username']} ({user['email']})")
                success_count += 1
            else:
                print(f"❌ Failed to add user: {user['username']} ({user['email']})")
                
        except Exception as e:
            print(f"❌ Error adding user {user['username']}: {e}")
    
    print(f"\n📊 Summary: {success_count}/{len(test_users)} users added successfully")
    return success_count > 0

def check_existing_users():
    """기존 사용자 확인"""
    if not friends_db.is_available():
        print("❌ Friends database is not available")
        return
    
    try:
        # 모든 사용자 검색 (빈 쿼리로)
        users = friends_db.search_users("")
        print(f"📊 Found {len(users)} users in database:")
        
        for user in users:
            print(f"  - {user['username']} ({user['email']}) [ID: {user['user_id']}]")
            
    except Exception as e:
        print(f"❌ Error checking users: {e}")

if __name__ == "__main__":
    print("🚀 Starting test user creation...")
    
    # 기존 사용자 확인
    print("\n1. Checking existing users...")
    check_existing_users()
    
    # 테이블 생성 (필요한 경우)
    print("\n2. Ensuring tables exist...")
    friends_db.create_tables()
    
    # 테스트 사용자 추가
    print("\n3. Adding test users...")
    success = add_test_users()
    
    if success:
        print("\n4. Final check...")
        check_existing_users()
        print("\n✅ Test users added successfully! You can now test the search functionality.")
    else:
        print("\n❌ Failed to add test users. Please check your database connection.")