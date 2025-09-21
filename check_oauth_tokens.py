#!/usr/bin/env python3
"""
OAuth 토큰 저장 상태를 확인하는 스크립트
"""

import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from utils.config import config

def check_oauth_tokens(user_id: str):
    """특정 사용자의 OAuth 토큰 저장 상태 확인"""
    try:
        supabase = config.get_client_for_user(user_id)
        
        print(f"🔍 Checking OAuth tokens for user: {user_id}")
        
        # 1. oauth_tokens 테이블 확인
        print("\n📋 Checking oauth_tokens table...")
        oauth_result = supabase.table('oauth_tokens').select('*').eq('user_id', user_id).execute()
        
        if oauth_result.data:
            print(f"✅ Found {len(oauth_result.data)} oauth_tokens entries:")
            for token in oauth_result.data:
                platform = token.get('platform')
                has_access = bool(token.get('access_token'))
                has_refresh = bool(token.get('refresh_token'))
                expires_at = token.get('expires_at', 'N/A')
                print(f"  - {platform}: access_token={has_access}, refresh_token={has_refresh}, expires={expires_at}")
        else:
            print("❌ No oauth_tokens found")
        
        # 2. calendar_sync_configs 테이블 확인
        print("\n📋 Checking calendar_sync_configs table...")
        config_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).execute()
        
        if config_result.data:
            print(f"✅ Found {len(config_result.data)} calendar_sync_configs entries:")
            for config_entry in config_result.data:
                platform = config_entry.get('platform')
                credentials = config_entry.get('credentials', {})
                calendar_id = config_entry.get('calendar_id')
                is_enabled = config_entry.get('is_enabled')
                
                has_access = bool(credentials.get('access_token')) if isinstance(credentials, dict) else False
                has_api_key = bool(credentials.get('api_key')) if isinstance(credentials, dict) else False
                
                print(f"  - {platform}: enabled={is_enabled}, calendar_id={calendar_id[:8] + '...' if calendar_id else None}")
                print(f"    credentials: access_token={has_access}, api_key={has_api_key}")
                
                if platform == 'notion' and credentials:
                    print(f"    notion credentials keys: {list(credentials.keys()) if isinstance(credentials, dict) else 'not dict'}")
        else:
            print("❌ No calendar_sync_configs found")
        
        # 3. calendar_sync 테이블 확인
        print("\n📋 Checking calendar_sync table...")
        sync_result = supabase.table('calendar_sync').select('*').eq('user_id', user_id).execute()
        
        if sync_result.data:
            print(f"✅ Found {len(sync_result.data)} calendar_sync entries:")
            for sync_entry in sync_result.data:
                platform = sync_entry.get('platform')
                calendar_id = sync_entry.get('calendar_id')
                sync_status = sync_entry.get('sync_status')
                synced_at = sync_entry.get('synced_at')
                print(f"  - {platform}: calendar_id={calendar_id[:8] + '...' if calendar_id else None}, status={sync_status}, synced_at={synced_at}")
        else:
            print("❌ No calendar_sync found")
            
    except Exception as e:
        print(f"❌ Error checking OAuth tokens: {e}")

if __name__ == "__main__":
    user_id = "87875eda6797f839f8c70aa90efb1352"  # 실제 사용자 ID
    check_oauth_tokens(user_id)