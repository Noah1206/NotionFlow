#!/usr/bin/env python3
"""
수동으로 Notion 동기화 테스트
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 프로젝트 경로 추가
sys.path.append('.')
sys.path.append('backend')

def test_notion_sync():
    print("=== Notion 동기화 수동 테스트 ===\n")
    
    # 1. 환경변수 확인
    NOTION_API_KEY = os.getenv('NOTION_API_KEY')
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
    
    print(f"1. 환경변수 확인:")
    print(f"   NOTION_API_KEY: {'✅ 설정됨' if NOTION_API_KEY and NOTION_API_KEY != 'YOUR_API_KEY_HERE' else '❌ 설정 안됨'}")
    print(f"   SUPABASE_URL: {'✅ 설정됨' if SUPABASE_URL else '❌ 설정 안됨'}")
    print(f"   SUPABASE_KEY: {'✅ 설정됨' if SUPABASE_KEY else '❌ 설정 안됨'}")
    print()
    
    if not NOTION_API_KEY or NOTION_API_KEY == 'YOUR_API_KEY_HERE':
        print("❌ Notion API Key가 설정되지 않았습니다.")
        print("   .env 파일에 NOTION_API_KEY=your_notion_api_key를 추가해주세요.")
        return
    
    # 2. Notion API 테스트
    print("2. Notion API 연결 테스트:")
    try:
        from notion_client import Client as NotionClient
        notion = NotionClient(auth=NOTION_API_KEY)
        
        # 사용자 정보 조회
        users = notion.users.list()
        print(f"   ✅ Notion API 연결 성공")
        
        # 데이터베이스 조회
        databases = notion.search(filter={"property": "object", "value": "database"}).get('results', [])
        print(f"   📁 데이터베이스 {len(databases)}개 발견:")
        
        calendar_databases = []
        for db in databases:
            title = db.get('title', [])
            if title:
                name = title[0].get('plain_text', 'Untitled')
                print(f"       - {name}")
                
                # 날짜 필드가 있는 데이터베이스 찾기
                properties = db.get('properties', {})
                has_date = any(prop.get('type') == 'date' for prop in properties.values())
                if has_date:
                    calendar_databases.append({'id': db['id'], 'name': name})
        
        print(f"   📅 캘린더 데이터베이스 {len(calendar_databases)}개:")
        for cal_db in calendar_databases:
            print(f"       - {cal_db['name']} (ID: {cal_db['id'][:8]}...)")
        
    except Exception as e:
        print(f"   ❌ Notion API 연결 실패: {e}")
        return
    
    # 3. 수동으로 Supabase에 연동 정보 저장
    if SUPABASE_URL and SUPABASE_KEY and calendar_databases:
        print("\n3. Supabase에 연동 정보 수동 저장:")
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            user_id = "e390559f-c328-4786-ac5d-c74b5409451b"  # 임시 사용자 ID
            
            # calendar_sync_configs에 Notion 설정 저장
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
            
            # 기존 레코드 삭제 후 새로 생성
            supabase.table('calendar_sync_configs').delete().eq('user_id', user_id).eq('platform', 'notion').execute()
            result = supabase.table('calendar_sync_configs').insert(config_data).execute()
            
            if result.data:
                print("   ✅ calendar_sync_configs에 Notion 설정 저장 완료")
                
                # 첫 번째 캘린더 데이터베이스를 캘린더로 등록
                if calendar_databases:
                    cal_db = calendar_databases[0]
                    calendar_data = {
                        'id': cal_db['id'],  # Notion DB ID 사용
                        'owner_id': user_id,
                        'name': cal_db['name'],
                        'type': 'notion',
                        'color': '#9b59b6',
                        'description': f'Notion에서 동기화된 캘린더: {cal_db["name"]}',
                        'is_active': True,
                        'public_access': False,
                        'allow_editing': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # 기존 캘린더 삭제 후 새로 생성
                    supabase.table('calendars').delete().eq('id', cal_db['id']).execute()
                    cal_result = supabase.table('calendars').insert(calendar_data).execute()
                    
                    if cal_result.data:
                        print(f"   ✅ calendars에 '{cal_db['name']}' 캘린더 등록 완료")
                        
                        # calendar_sync에도 등록
                        sync_data = {
                            'user_id': user_id,
                            'platform': 'notion',
                            'calendar_id': cal_db['id'],
                            'sync_status': 'active',
                            'synced_at': datetime.now().isoformat(),
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        supabase.table('calendar_sync').delete().eq('user_id', user_id).eq('platform', 'notion').execute()
                        sync_result = supabase.table('calendar_sync').insert(sync_data).execute()
                        
                        if sync_result.data:
                            print("   ✅ calendar_sync에 동기화 정보 등록 완료")
                            print("\n🎉 Notion 연동 설정이 완료되었습니다!")
                            print("이제 NodeFlow를 새로고침하고 Sync 버튼을 눌러보세요.")
                        else:
                            print("   ❌ calendar_sync 등록 실패")
                    else:
                        print("   ❌ 캘린더 등록 실패")
            else:
                print("   ❌ Notion 설정 저장 실패")
                
        except Exception as e:
            print(f"   ❌ Supabase 저장 실패: {e}")
    
    print("\n완료!")

if __name__ == "__main__":
    test_notion_sync()