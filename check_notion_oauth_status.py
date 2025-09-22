#!/usr/bin/env python3
"""
Check Notion OAuth status in the database
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import Config

# Load environment variables
load_dotenv()

def check_notion_oauth():
    """Check Notion OAuth status"""
    print("\n" + "="*50)
    print("🔍 CHECKING NOTION OAUTH STATUS")
    print("="*50)
    
    # Initialize config
    config = Config()
    
    # Get test user ID
    test_user_id = os.getenv('TEST_USER_UUID', 'da2784e1-24f5-4112-a1a7-7d3a7e44081b')
    print(f"\n📌 User ID: {test_user_id}")
    
    # Normalize UUID
    from utils.uuid_helper import normalize_uuid
    normalized_id = normalize_uuid(test_user_id)
    print(f"📌 Normalized ID: {normalized_id}")
    
    print("\n" + "-"*50)
    print("1️⃣ Checking oauth_tokens table...")
    print("-"*50)
    
    try:
        oauth_result = config.supabase_client.table('oauth_tokens').select('*').eq(
            'platform', 'notion'
        ).execute()
        
        if oauth_result.data:
            print(f"✅ Found {len(oauth_result.data)} Notion OAuth token(s):")
            for token in oauth_result.data:
                user_id = token.get('user_id', 'Unknown')
                print(f"\n   User ID: {user_id}")
                print(f"   Access Token: {token.get('access_token', '')[:30]}...")
                print(f"   Created: {token.get('created_at', 'Unknown')}")
                print(f"   Updated: {token.get('updated_at', 'Unknown')}")
        else:
            print("❌ No Notion OAuth tokens found in database")
    except Exception as e:
        print(f"❌ Error checking oauth_tokens: {e}")
    
    print("\n" + "-"*50)
    print("2️⃣ Checking calendar_sync_configs table...")
    print("-"*50)
    
    try:
        sync_result = config.supabase_client.table('calendar_sync_configs').select('*').eq(
            'platform', 'notion'
        ).execute()
        
        if sync_result.data:
            print(f"✅ Found {len(sync_result.data)} Notion sync config(s):")
            for config_item in sync_result.data:
                user_id = config_item.get('user_id', 'Unknown')
                print(f"\n   User ID: {user_id}")
                print(f"   Calendar ID: {config_item.get('calendar_id', 'None')}")
                print(f"   Enabled: {config_item.get('is_enabled', False)}")
                print(f"   Last Sync: {config_item.get('last_sync_at', 'Never')}")
                
                credentials = config_item.get('credentials', {})
                if isinstance(credentials, dict):
                    if 'access_token' in credentials:
                        print(f"   Access Token: {credentials['access_token'][:30]}...")
                    else:
                        print(f"   Access Token: Not found in credentials")
                    print(f"   Credential Keys: {list(credentials.keys())}")
                else:
                    print(f"   Credentials Type: {type(credentials)}")
        else:
            print("❌ No Notion sync configs found in database")
    except Exception as e:
        print(f"❌ Error checking calendar_sync_configs: {e}")
    
    print("\n" + "-"*50)
    print("3️⃣ Checking calendars table for Notion calendars...")
    print("-"*50)
    
    try:
        cal_result = config.supabase_client.table('calendars').select('*').ilike(
            'name', '%notion%'
        ).execute()
        
        if cal_result.data:
            print(f"✅ Found {len(cal_result.data)} Notion-related calendar(s):")
            for cal in cal_result.data:
                print(f"\n   ID: {cal.get('id', 'Unknown')}")
                print(f"   Name: {cal.get('name', 'Unknown')}")
                print(f"   Owner: {cal.get('owner_id', 'Unknown')}")
                print(f"   Created: {cal.get('created_at', 'Unknown')}")
        else:
            print("❌ No Notion-related calendars found")
    except Exception as e:
        print(f"❌ Error checking calendars: {e}")
    
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    print("\nTo complete Notion sync setup:")
    print("1. User must complete OAuth authentication at /dashboard/connect")
    print("2. Select Notion workspace and grant permissions")
    print("3. System will store access token in calendar_sync_configs")
    print("4. Then sync can import events from Notion databases")
    
    print("\n✅ Check completed!")

if __name__ == "__main__":
    check_notion_oauth()