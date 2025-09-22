#!/usr/bin/env python3
"""
Clean up test tokens from database
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import Config

# Load environment variables
load_dotenv()

def cleanup_test_tokens():
    """Remove test tokens from database"""
    print("\n" + "="*50)
    print("🧹 CLEANING UP TEST TOKENS")
    print("="*50)
    
    config = Config()
    
    # Get test user ID
    test_user_id = os.getenv('TEST_USER_UUID', 'da2784e1-24f5-4112-a1a7-7d3a7e44081b')
    from utils.uuid_helper import normalize_uuid
    normalized_user_id = normalize_uuid(test_user_id)
    
    print(f"\n📌 User ID: {normalized_user_id}")
    
    # Find test tokens
    print("\n1️⃣ Finding test tokens...")
    try:
        # Look for test tokens (those containing "test" in access_token)
        all_configs = config.supabase_client.table('calendar_sync_configs').select('*').eq(
            'user_id', normalized_user_id
        ).execute()
        
        test_configs = []
        real_configs = []
        
        for cfg in all_configs.data:
            credentials = cfg.get('credentials', {})
            if isinstance(credentials, dict):
                access_token = credentials.get('access_token', '')
                if 'test' in access_token.lower():
                    test_configs.append(cfg)
                else:
                    real_configs.append(cfg)
        
        print(f"   Found {len(test_configs)} test token(s)")
        print(f"   Found {len(real_configs)} real token(s)")
        
        if test_configs:
            print("\n📋 Test tokens to delete:")
            for cfg in test_configs:
                creds = cfg.get('credentials', {})
                token = creds.get('access_token', '')[:30] if isinstance(creds, dict) else 'Unknown'
                print(f"   - ID: {cfg['id']} | Platform: {cfg['platform']} | Token: {token}...")
        
        if real_configs:
            print("\n📋 Real tokens to keep:")
            for cfg in real_configs:
                creds = cfg.get('credentials', {})
                token = creds.get('access_token', '')[:30] if isinstance(creds, dict) else 'Unknown'
                print(f"   - ID: {cfg['id']} | Platform: {cfg['platform']} | Token: {token}...")
        
    except Exception as e:
        print(f"   ❌ Error finding tokens: {e}")
        return False
    
    # Delete test tokens
    if test_configs:
        print(f"\n2️⃣ Deleting {len(test_configs)} test token(s)...")
        
        try:
            for cfg in test_configs:
                result = config.supabase_client.table('calendar_sync_configs').delete().eq(
                    'id', cfg['id']
                ).execute()
                
                if result.data:
                    print(f"   ✅ Deleted test token: {cfg['id']}")
                else:
                    print(f"   ⚠️ Delete returned no data for: {cfg['id']}")
            
            print("   ✅ All test tokens deleted!")
            
        except Exception as e:
            print(f"   ❌ Error deleting tokens: {e}")
            return False
    else:
        print("\n2️⃣ No test tokens to delete")
    
    # Verify cleanup
    print("\n3️⃣ Verifying cleanup...")
    try:
        remaining = config.supabase_client.table('calendar_sync_configs').select('*').eq(
            'user_id', normalized_user_id
        ).execute()
        
        print(f"   Remaining configs: {len(remaining.data) if remaining.data else 0}")
        
        if remaining.data:
            for cfg in remaining.data:
                creds = cfg.get('credentials', {})
                token = creds.get('access_token', '')[:30] if isinstance(creds, dict) else 'Unknown'
                print(f"   - {cfg['platform']}: {token}...")
        
    except Exception as e:
        print(f"   ❌ Error verifying: {e}")
    
    return True

if __name__ == "__main__":
    success = cleanup_test_tokens()
    
    if success:
        print("\n✅ Cleanup completed!")
        print("\n📝 Now you can:")
        print("1. Complete real Notion OAuth from dashboard")
        print("2. Or use insert_notion_token.py with real token")
    else:
        print("\n❌ Cleanup failed")
    
    sys.exit(0 if success else 1)