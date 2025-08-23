#!/usr/bin/env python3
"""
Supabase 연결 테스트
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

print("🔍 Supabase 연결 진단:")
print("-" * 50)

# 환경변수 확인
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')

print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"API KEY 길이: {len(SUPABASE_API_KEY) if SUPABASE_API_KEY else 0}")
print(f"API KEY 시작: {SUPABASE_API_KEY[:50] if SUPABASE_API_KEY else 'None'}...")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    print("❌ 환경변수 누락!")
    exit(1)

# Supabase 연결 테스트
try:
    from supabase import create_client
    
    supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
    print("✅ Supabase 클라이언트 생성 성공")
    
    # 간단한 쿼리 테스트
    result = supabase.table('users').select('id').limit(1).execute()
    print("✅ users 테이블 쿼리 성공")
    
    # auth 테이블 확인
    try:
        auth_result = supabase.auth.get_user()
        print("✅ Auth 시스템 접근 가능")
    except Exception as e:
        print(f"⚠️ Auth 테스트: {e}")
    
except Exception as e:
    print(f"❌ Supabase 연결 실패: {e}")
    print("🔧 API 키를 확인해주세요!")

print("-" * 50)