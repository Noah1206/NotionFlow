#!/usr/bin/env python3
"""
캘린더 테이블 상태 조사 스크립트
"""

import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from utils.config import config

def investigate_calendars(user_id: str):
    """사용자의 캘린더 관련 데이터 조사"""
    try:
        supabase = config.get_client_for_user(user_id)
        
        print(f"🔍 Investigating calendar data for user: {user_id}")
        
        # 1. calendars 테이블 전체 확인
        print("\n📋 Checking calendars table...")
        calendars_result = supabase.table('calendars').select('*').eq('owner_id', user_id).execute()
        
        if calendars_result.data:
            print(f"✅ Found {len(calendars_result.data)} calendars:")
            for cal in calendars_result.data:
                print(f"  - {cal['name']} (ID: {cal['id'][:8]}..., Platform: {cal.get('platform', 'unknown')})")
        else:
            print("❌ No calendars found in calendars table")
            
        # 2. calendar_sync에서 참조하는 calendar_id들 확인
        print("\n📋 Checking calendar_sync references...")
        sync_result = supabase.table('calendar_sync').select('*').eq('user_id', user_id).execute()
        
        referenced_ids = set()
        if sync_result.data:
            print(f"✅ Found {len(sync_result.data)} sync entries:")
            for sync in sync_result.data:
                calendar_id = sync['calendar_id']
                platform = sync['platform']
                status = sync['sync_status']
                referenced_ids.add(calendar_id)
                print(f"  - {platform}: {calendar_id[:8]}... (status: {status})")
                
                # 해당 calendar_id가 calendars 테이블에 존재하는지 확인
                cal_check = supabase.table('calendars').select('*').eq('id', calendar_id).execute()
                if cal_check.data:
                    print(f"    ✅ Calendar exists: {cal_check.data[0]['name']}")
                else:
                    print(f"    ❌ Calendar {calendar_id[:8]}... missing from calendars table")
        else:
            print("❌ No sync entries found")
            
        # 3. 누락된 calendar 엔트리들을 위한 정보 수집
        print("\n🔍 Checking for orphaned calendar_sync entries...")
        
        for sync_entry in sync_result.data:
            calendar_id = sync_entry['calendar_id']
            platform = sync_entry['platform']
            
            # calendars 테이블에 없는 경우
            cal_exists = supabase.table('calendars').select('*').eq('id', calendar_id).execute()
            if not cal_exists.data and platform == 'notion':
                print(f"\n🔧 Missing calendar entry for Notion: {calendar_id[:8]}...")
                print(f"   Sync status: {sync_entry['sync_status']}")
                print(f"   Last synced: {sync_entry.get('synced_at', 'Never')}")
                
                # 이 calendar_id로 Notion API를 통해 정보 수집 시도
                print(f"   💡 This calendar_id might be a Notion database ID")
                
        # 4. oauth_tokens와 calendar_sync_configs 재확인
        print("\n📋 Re-checking token storage...")
        
        oauth_result = supabase.table('oauth_tokens').select('*').eq('user_id', user_id).execute()
        config_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).execute()
        
        print(f"oauth_tokens entries: {len(oauth_result.data)}")
        print(f"calendar_sync_configs entries: {len(config_result.data)}")
        
        return {
            'calendars_count': len(calendars_result.data),
            'sync_entries_count': len(sync_result.data),
            'missing_calendars': len([s for s in sync_result.data if not supabase.table('calendars').select('*').eq('id', s['calendar_id']).execute().data]),
            'oauth_tokens_count': len(oauth_result.data),
            'config_entries_count': len(config_result.data)
        }
        
    except Exception as e:
        print(f"❌ Error investigating calendars: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    user_id = "87875eda6797f839f8c70aa90efb1352"
    result = investigate_calendars(user_id)
    
    if result:
        print(f"\n📊 Summary:")
        print(f"   Calendars in table: {result['calendars_count']}")
        print(f"   Sync entries: {result['sync_entries_count']}")
        print(f"   Missing calendar records: {result['missing_calendars']}")
        print(f"   OAuth tokens: {result['oauth_tokens_count']}")
        print(f"   Config entries: {result['config_entries_count']}")
        
        if result['missing_calendars'] > 0:
            print(f"\n⚠️ Data integrity issue: {result['missing_calendars']} sync entries reference non-existent calendars")
            print("💡 This suggests the OAuth flow is not properly creating calendar records")