#!/usr/bin/env python3
"""
Manually insert Notion token for testing
You need to get a Notion integration token first:
1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the token
4. Share your Notion database with the integration
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import Config
from utils.uuid_helper import normalize_uuid

# Load environment variables
load_dotenv()

def insert_notion_token():
    """Manually insert a Notion token for testing"""
    print("\n" + "="*50)
    print("🔧 MANUAL NOTION TOKEN INSERTION")
    print("="*50)
    
    # Get your Notion token
    print("\n📝 Please enter your Notion access token:")
    print("   (Get it from https://www.notion.so/my-integrations)")
    print("   Or use OAuth token from Notion OAuth flow")
    print("   Press Enter to skip if you don't have one")
    
    token = input("\nNotion token: ").strip()
    
    if not token:
        print("\n❌ No token provided. Exiting...")
        return False
    
    # Initialize config
    config = Config()
    
    # Get test user ID
    test_user_id = os.getenv('TEST_USER_UUID', 'da2784e1-24f5-4112-a1a7-7d3a7e44081b')
    normalized_user_id = normalize_uuid(test_user_id)
    
    print(f"\n📌 Using user ID: {test_user_id}")
    print(f"📌 Normalized: {normalized_user_id}")
    
    # Step 1: Create or get a calendar for Notion
    print("\n1️⃣ Creating/Getting calendar for Notion sync...")
    
    try:
        # Check existing calendars
        cal_result = config.supabase_client.table('calendars').select('*').eq(
            'owner_id', normalized_user_id
        ).execute()
        
        if cal_result.data:
            # Use existing calendar
            calendar_id = cal_result.data[0]['id']
            print(f"✅ Using existing calendar: {calendar_id}")
        else:
            # Create new calendar
            calendar_id = str(uuid.uuid4()).replace('-', '')
            new_calendar = {
                'id': calendar_id,
                'owner_id': normalized_user_id,
                'name': 'Notion Calendar',
                'description': 'Events synced from Notion',
                'color': '#FF6B35',
                'is_default': True,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = config.supabase_client.table('calendars').insert(new_calendar).execute()
            if result.data:
                print(f"✅ Created new calendar: {calendar_id}")
            else:
                print("❌ Failed to create calendar")
                return False
                
    except Exception as e:
        print(f"❌ Error with calendar: {e}")
        return False
    
    # Step 2: Insert into calendar_sync_configs
    print("\n2️⃣ Inserting token into calendar_sync_configs...")
    
    try:
        # Check if config exists
        existing = config.supabase_client.table('calendar_sync_configs').select('*').eq(
            'user_id', normalized_user_id
        ).eq('platform', 'notion').execute()
        
        sync_config_data = {
            'user_id': normalized_user_id,
            'platform': 'notion',
            'calendar_id': calendar_id,
            'credentials': {
                'access_token': token,
                'token_type': 'Bearer',
                'stored_at': datetime.now(timezone.utc).isoformat()
            },
            'is_enabled': True,
            'sync_frequency_minutes': 15,
            'last_sync_at': None,
            'consecutive_failures': 0,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if existing.data:
            # Update existing
            print("📝 Updating existing config...")
            update_data = {
                'credentials': sync_config_data['credentials'],
                'is_enabled': True,
                'calendar_id': calendar_id,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            result = config.supabase_client.table('calendar_sync_configs').update(
                update_data
            ).eq('user_id', normalized_user_id).eq('platform', 'notion').execute()
        else:
            # Insert new
            print("📝 Inserting new config...")
            sync_config_data['created_at'] = datetime.now(timezone.utc).isoformat()
            result = config.supabase_client.table('calendar_sync_configs').insert(
                sync_config_data
            ).execute()
        
        if result.data:
            print("✅ Token stored in calendar_sync_configs!")
        else:
            print("❌ Failed to store in calendar_sync_configs")
            
    except Exception as e:
        print(f"❌ Error storing sync config: {e}")
        return False
    
    # Step 3: Also try oauth_tokens table (might have foreign key issues)
    print("\n3️⃣ Attempting to insert into oauth_tokens table...")
    
    try:
        oauth_data = {
            'user_id': normalized_user_id,
            'platform': 'notion',
            'access_token': token,
            'token_type': 'Bearer',
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),  # Assume 1 year
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Check if exists
        existing_oauth = config.supabase_client.table('oauth_tokens').select('*').eq(
            'user_id', normalized_user_id
        ).eq('platform', 'notion').execute()
        
        if existing_oauth.data:
            # Update
            result = config.supabase_client.table('oauth_tokens').update({
                'access_token': token,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', normalized_user_id).eq('platform', 'notion').execute()
            print("✅ Updated oauth_tokens table")
        else:
            # Insert
            result = config.supabase_client.table('oauth_tokens').insert(oauth_data).execute()
            if result.data:
                print("✅ Inserted into oauth_tokens table")
            else:
                print("⚠️ Could not insert into oauth_tokens (expected if user doesn't exist)")
                
    except Exception as e:
        print(f"⚠️ OAuth tokens table error (expected): {e}")
    
    # Step 4: Verify insertion
    print("\n4️⃣ Verifying token storage...")
    
    try:
        # Check calendar_sync_configs
        verify = config.supabase_client.table('calendar_sync_configs').select('*').eq(
            'user_id', normalized_user_id
        ).eq('platform', 'notion').execute()
        
        if verify.data and verify.data[0].get('credentials', {}).get('access_token'):
            print("✅ Token successfully stored and verified!")
            print(f"   Token prefix: {token[:20]}...")
            print(f"   Calendar ID: {verify.data[0].get('calendar_id')}")
            print(f"   Enabled: {verify.data[0].get('is_enabled')}")
            
            print("\n✅ SUCCESS! You can now test Notion sync.")
            print("\n📝 Next steps:")
            print("1. Run: python test_notion_sync_debug.py")
            print("2. Or use the dashboard to trigger manual sync")
            return True
        else:
            print("❌ Token verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    success = insert_notion_token()
    sys.exit(0 if success else 1)