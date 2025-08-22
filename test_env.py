#!/usr/bin/env python3
"""
환경변수 테스트 스크립트
Railway 배포에서 환경변수가 제대로 로드되는지 확인
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

print("🔍 환경변수 확인:")
print("-" * 50)

# 필수 환경변수들 확인
required_vars = [
    'SUPABASE_URL',
    'SUPABASE_API_KEY',
    'SUPABASE_SERVICE_ROLE_KEY',
    'FLASK_SECRET_KEY',
    'API_KEY_ENCRYPTION_KEY'
]

for var in required_vars:
    value = os.getenv(var)
    if value:
        # 보안을 위해 첫 10자와 마지막 10자만 표시
        if len(value) > 20:
            masked = value[:10] + "..." + value[-10:]
        else:
            masked = value[:5] + "..."
        print(f"✅ {var}: {masked}")
    else:
        print(f"❌ {var}: 누락됨")

print("-" * 50)

# Supabase 연결 테스트
try:
    from supabase import create_client
    
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase 클라이언트 생성 성공")
        
        # 간단한 쿼리 테스트
        result = supabase.table('users').select('id').limit(1).execute()
        print("✅ Supabase 연결 테스트 성공")
        
    else:
        print("❌ Supabase 환경변수 누락")
        
except Exception as e:
    print(f"❌ Supabase 연결 오류: {e}")

print("-" * 50)
print("🎯 테스트 완료")