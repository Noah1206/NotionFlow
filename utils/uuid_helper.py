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
    """auth.users 테이블에 사용자가 존재하는지 확인하고 없으면 생성"""
    try:
        from utils.config import config
        
        # 서비스 역할 클라이언트 사용
        supabase = config.supabase_admin
        if not supabase:
            print("❌ Admin client not available")
            return False
        
        normalized_id = normalize_uuid(user_id)
        if not normalized_id:
            print(f"❌ Invalid UUID format: {user_id}")
            return False
        
        # auth.users에서 사용자 확인
        existing = supabase.table('auth.users').select('id').eq('id', normalized_id).execute()
        
        if not existing.data:
            # auth.users에 사용자 생성
            user_data = {
                'id': normalized_id,
                'email': email,
                'created_at': 'NOW()',
                'updated_at': 'NOW()',
                'email_confirmed_at': 'NOW()'
            }
            
            if name:
                user_data['raw_user_meta_data'] = {'name': name}
            
            supabase.table('auth.users').insert(user_data).execute()
            print(f"✅ Created auth.users entry for {email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error ensuring auth user exists: {e}")
        return False