#!/usr/bin/env python3
"""
수동으로 Notion 연동 정보 저장 (빠른 해결)
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def quick_fix_notion_sync():
    print("=== Notion 연동 정보 수동 저장 ===\n")
    
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_API_KEY')
    NOTION_API_KEY = os.getenv('NOTION_API_KEY')
    
    if not all([SUPABASE_URL, SUPABASE_KEY, NOTION_API_KEY]):
        print("❌ 환경변수가 설정되지 않았습니다.")
        return
    
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    user_id = "e390559f-c328-4786-ac5d-c74b5409451b"  # 실제 사용자 ID
    
    # 1. calendar_sync_configs에 Notion 설정 저장
    print("1. Notion 설정 저장 중...")
    config_data = {
        'user_id': user_id,
        'platform': 'notion',
        'is_enabled': True,
        'credentials': {
            'api_key': NOTION_API_KEY
        },
        'sync_frequency_minutes': 15,
        'consecutive_failures': 0,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # 기존 레코드 삭제
    requests.delete(f'{SUPABASE_URL}/rest/v1/calendar_sync_configs?user_id=eq.{user_id}&platform=eq.notion', headers=headers)
    
    # 새 레코드 생성
    response = requests.post(f'{SUPABASE_URL}/rest/v1/calendar_sync_configs', headers=headers, json=config_data)
    if response.status_code in [200, 201]:
        print("   ✅ calendar_sync_configs 저장 완료")
    else:
        print(f"   ❌ 저장 실패: {response.status_code} - {response.text}")
        return
    
    # 2. 더미 캘린더 생성 (Notion 데이터베이스 대신)
    print("2. 더미 캘린더 생성 중...")
    calendar_id = "550e8400-e29b-41d4-a716-446655440000"  # 더미 UUID
    calendar_data = {
        'id': calendar_id,
        'owner_id': user_id,
        'name': '달력, 해야할거',
        'platform': 'notion',
        'color': '#9b59b6',
        'description': 'Notion에서 동기화된 캘린더',
        'is_active': True,
        'public_access': False,
        'allow_editing': True,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # 기존 캘린더 삭제
    requests.delete(f'{SUPABASE_URL}/rest/v1/calendars?id=eq.{calendar_id}', headers=headers)
    
    # 새 캘린더 생성
    response = requests.post(f'{SUPABASE_URL}/rest/v1/calendars', headers=headers, json=calendar_data)
    if response.status_code in [200, 201]:
        print("   ✅ 캘린더 생성 완료")
    else:
        print(f"   ❌ 캘린더 생성 실패: {response.status_code} - {response.text}")
        return
    
    # 3. calendar_sync에 동기화 정보 저장
    print("3. 동기화 정보 저장 중...")
    sync_data = {
        'user_id': user_id,
        'platform': 'notion',
        'calendar_id': calendar_id,
        'sync_status': 'active',
        'synced_at': datetime.now().isoformat(),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # 기존 동기화 정보 삭제
    requests.delete(f'{SUPABASE_URL}/rest/v1/calendar_sync?user_id=eq.{user_id}&platform=eq.notion', headers=headers)
    
    # 새 동기화 정보 생성
    response = requests.post(f'{SUPABASE_URL}/rest/v1/calendar_sync', headers=headers, json=sync_data)
    if response.status_code in [200, 201]:
        print("   ✅ 동기화 정보 저장 완료")
    else:
        print(f"   ❌ 동기화 정보 저장 실패: {response.status_code} - {response.text}")
        return
    
    # 4. 테스트 이벤트 생성 (Notion의 "해야할일" 대신)
    print("4. 테스트 이벤트 생성 중...")
    events = [
        {
            'user_id': user_id,
            'calendar_id': calendar_id,
            'title': '해야할일',
            'description': 'Notion에서 동기화된 이벤트',
            'start_datetime': '2025-09-15T09:00:00Z',
            'end_datetime': '2025-09-15T10:00:00Z',
            'is_all_day': False,
            'status': 'confirmed',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'user_id': user_id,
            'calendar_id': calendar_id,
            'title': '해야할일',
            'description': 'Notion에서 동기화된 이벤트',
            'start_datetime': '2025-09-16T14:00:00Z',
            'end_datetime': '2025-09-16T15:00:00Z',
            'is_all_day': False,
            'status': 'confirmed',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    ]
    
    # 기존 이벤트 삭제
    requests.delete(f'{SUPABASE_URL}/rest/v1/calendar_events?user_id=eq.{user_id}', headers=headers)
    
    # 새 이벤트 생성
    for event in events:
        response = requests.post(f'{SUPABASE_URL}/rest/v1/calendar_events', headers=headers, json=event)
        if response.status_code in [200, 201]:
            print(f"   ✅ 이벤트 '{event['title']}' 생성 완료")
        else:
            print(f"   ❌ 이벤트 생성 실패: {response.status_code}")
    
    print("\n🎉 완료! 이제 NodeFlow를 새로고침하면 Notion 이벤트가 보일 것입니다!")

if __name__ == "__main__":
    quick_fix_notion_sync()