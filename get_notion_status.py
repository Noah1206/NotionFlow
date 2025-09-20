#!/usr/bin/env python3
"""
실제 Notion 연동 상태를 확인하는 스크립트
"""

import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from utils.config import config

def check_notion_status(user_id: str):
    """특정 사용자의 Notion 연동 상태 확인"""
    try:
        supabase = config.get_client_for_user(user_id)
        
        # 1. calendar_sync_configs에서 Notion 설정 확인
        print(f"🔍 Checking Notion config for user: {user_id}")
        
        config_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
        
        if not config_result.data:
            print("❌ No Notion configuration found")
            return
            
        notion_config = config_result.data[0]
        print(f"✅ Found Notion config: {notion_config}")
        
        # 2. access_token 확인
        credentials = notion_config.get('credentials', {})
        if isinstance(credentials, dict):
            access_token = credentials.get('access_token')
            if access_token:
                print(f"✅ Access token found: {access_token[:20]}...")
                
                # 3. 실제 Notion API 호출로 데이터베이스 확인
                try:
                    import requests
                    
                    headers = {
                        'Authorization': f'Bearer {access_token}',
                        'Notion-Version': '2022-06-28',
                        'Content-Type': 'application/json'
                    }
                    
                    # 데이터베이스 검색
                    response = requests.post(
                        'https://api.notion.com/v1/search',
                        headers=headers,
                        json={
                            'filter': {'object': 'database'},
                            'page_size': 10
                        }
                    )
                    
                    if response.status_code == 200:
                        databases = response.json().get('results', [])
                        print(f"📚 Found {len(databases)} databases in Notion:")
                        
                        for db in databases:
                            title = db.get('title', [])
                            db_name = 'Untitled'
                            if title and len(title) > 0:
                                db_name = title[0].get('plain_text', 'Untitled')
                            print(f"  - {db_name} (ID: {db['id'][:8]}...)")
                            
                        if databases:
                            first_db = databases[0]
                            first_db_title = first_db.get('title', [])
                            first_db_name = 'Untitled'
                            if first_db_title and len(first_db_title) > 0:
                                first_db_name = first_db_title[0].get('plain_text', 'Untitled')
                            
                            print(f"\n💡 Suggestion: Instead of 'Calendar 3e7f438e', show '{first_db_name}'")
                            
                    else:
                        print(f"❌ Notion API error: {response.status_code} - {response.text}")
                        
                except Exception as api_error:
                    print(f"❌ Error calling Notion API: {api_error}")
                    
            else:
                print("❌ No access_token found in credentials")
        else:
            print("❌ Invalid credentials format")
            
        # 4. 연결된 캘린더 확인 (calendar_sync 테이블에서)
        print("\n🔍 Checking calendar associations...")
        
        calendar_sync_result = supabase.table('calendar_sync').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
        
        if calendar_sync_result.data:
            for sync_entry in calendar_sync_result.data:
                calendar_id = sync_entry['calendar_id']
                print(f"📅 Found calendar_sync entry: {calendar_id[:8]}... (status: {sync_entry.get('sync_status', 'unknown')})")
                
                # Check if calendar exists in calendars table
                calendar_result = supabase.table('calendars').select('*').eq('id', calendar_id).execute()
                if calendar_result.data:
                    calendar = calendar_result.data[0]
                    print(f"✅ Calendar exists: {calendar['name']} (ID: {calendar_id[:8]}...)")
                else:
                    print(f"⚠️ Calendar ID {calendar_id[:8]}... not found in calendars table")
        else:
            print("⚠️ No calendar_sync entries found for Notion")
            
        # 5. 캘린더 관련 legacy 확인 (calendar_sync_configs에서 calendar_id)
        calendar_id = notion_config.get('calendar_id')
        if calendar_id:
            print(f"📅 Legacy calendar_id in config: {calendar_id[:8]}...")
        else:
            print("ℹ️ No calendar_id in Notion config (this is normal for new structure)")
            
    except Exception as e:
        print(f"❌ Error checking Notion status: {e}")

if __name__ == "__main__":
    user_id = "87875eda6797f839f8c70aa90efb1352"  # 실제 사용자 ID
    check_notion_status(user_id)