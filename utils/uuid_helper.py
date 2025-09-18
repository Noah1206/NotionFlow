"""
UUID 정규화 유틸리티
하이픈 있는/없는 UUID 형식을 일관되게 처리
"""

import uuid
import re

def normalize_uuid(uuid_string):
    """UUID 문자열을 표준 형식(하이픈 포함)으로 정규화"""
    if not uuid_string:
        return None
    
    # 이미 올바른 UUID 형식인지 확인
    try:
        return str(uuid.UUID(uuid_string))
    except ValueError:
        pass
    
    # 하이픈 제거하고 다시 시도
    clean_uuid = re.sub(r'[^a-fA-F0-9]', '', uuid_string)
    
    if len(clean_uuid) == 32:
        # 32자리 hex 문자열을 UUID 형식으로 변환
        try:
            formatted = f"{clean_uuid[:8]}-{clean_uuid[8:12]}-{clean_uuid[12:16]}-{clean_uuid[16:20]}-{clean_uuid[20:]}"
            return str(uuid.UUID(formatted))
        except ValueError:
            pass
    
    return None

def ensure_auth_user_exists(user_id, email, name=None):
    """사용자 존재 확인 및 생성 (users와 user_profiles 테이블)"""
    try:
        from utils.config import config
        from datetime import datetime, timezone
        
        # 서비스 역할 클라이언트 사용
        supabase = config.supabase_admin
        if not supabase:
            print("❌ Admin client not available")
            return False
        
        normalized_id = normalize_uuid(user_id)
        if not normalized_id:
            print(f"❌ Invalid UUID format: {user_id}")
            return False
        
        # 1. users 테이블에서 사용자 확인 및 생성
        try:
            existing_user = supabase.table('users').select('id').eq('id', normalized_id).execute()
            
            if not existing_user.data:
                # users 테이블에 사용자 생성
                user_data = {
                    'id': normalized_id,
                    'email': email,
                    'name': name or 'User',
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                user_result = supabase.table('users').insert(user_data).execute()
                if user_result.data:
                    print(f"✅ Created users entry for {email}")
                else:
                    print(f"❌ Failed to create users entry")
                    return False
            else:
                print(f"✅ User already exists in users table: {normalized_id}")
        except Exception as user_e:
            print(f"❌ Error with users table: {user_e}")
            return False
        
        # 2. user_profiles 테이블에서 프로필 확인 및 생성
        try:
            existing_profile = supabase.table('user_profiles').select('user_id').eq('user_id', normalized_id).execute()
            
            if not existing_profile.data:
                # 고유한 username 생성 (timestamp + uuid prefix 조합)
                timestamp_suffix = str(int(datetime.now().timestamp()))[-6:]  # 마지막 6자리
                username = f"{normalized_id[:8]}{timestamp_suffix}"
                
                # username 중복 확인 및 재시도
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        profile_data = {
                            'user_id': normalized_id,
                            'username': username,
                            'email': email,
                            'created_at': datetime.now(timezone.utc).isoformat()
                        }
                        
                        if name:
                            profile_data['display_name'] = name
                        
                        profile_result = supabase.table('user_profiles').insert(profile_data).execute()
                        if profile_result.data:
                            print(f"✅ Created user_profiles entry: {username}")
                            break
                        else:
                            print(f"❌ Failed to create user_profiles entry")
                            return False
                            
                    except Exception as profile_insert_e:
                        if 'duplicate key' in str(profile_insert_e).lower() and attempt < max_attempts - 1:
                            # username 중복이면 새로운 username 생성
                            username = f"{normalized_id[:8]}{timestamp_suffix}{attempt + 1}"
                            print(f"⚠️ Username conflict, retrying with: {username}")
                            continue
                        else:
                            print(f"❌ Profile creation failed: {profile_insert_e}")
                            return False
            else:
                print(f"✅ User profile already exists: {normalized_id}")
                
        except Exception as profile_e:
            print(f"⚠️ Error with user_profiles table (continuing): {profile_e}")
            # 프로필 생성 실패는 치명적이지 않음
        
        return True
        
    except Exception as e:
        print(f"❌ Error ensuring user exists: {e}")
        return False