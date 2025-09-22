#!/usr/bin/env python3
"""
Debug OAuth callback to see what's happening
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import Config

# Load environment variables
load_dotenv()

def debug_oauth_callback():
    """Debug what happens in OAuth callback"""
    print("\n" + "="*50)
    print("🔍 DEBUGGING OAUTH CALLBACK ISSUE")
    print("="*50)
    
    config = Config()
    
    print("\n1️⃣ Check current database state:")
    print("-"*50)
    
    # Check all calendar_sync_configs
    try:
        all_configs = config.supabase_client.table('calendar_sync_configs').select('*').execute()
        print(f"   Total configs: {len(all_configs.data) if all_configs.data else 0}")
        
        if all_configs.data:
            for cfg in all_configs.data:
                print(f"   - {cfg.get('platform', 'unknown')}: User {cfg.get('user_id', 'unknown')[:8]}...")
        
        # Check Notion configs specifically
        notion_configs = config.supabase_client.table('calendar_sync_configs').select('*').eq('platform', 'notion').execute()
        print(f"   Notion configs: {len(notion_configs.data) if notion_configs.data else 0}")
        
    except Exception as e:
        print(f"   ❌ Error checking configs: {e}")
    
    print("\n2️⃣ Check OAuth environment:")
    print("-"*50)
    
    notion_client_id = os.getenv('NOTION_CLIENT_ID')
    notion_client_secret = os.getenv('NOTION_CLIENT_SECRET')
    
    print(f"   NOTION_CLIENT_ID: {'✅ Set' if notion_client_id else '❌ Missing'}")
    print(f"   NOTION_CLIENT_SECRET: {'✅ Set' if notion_client_secret else '❌ Missing'}")
    
    if notion_client_id:
        print(f"   Client ID: {notion_client_id[:15]}...")
    
    print("\n3️⃣ Test database write directly:")
    print("-"*50)
    
    # Test direct write to calendar_sync_configs
    test_user_id = os.getenv('TEST_USER_UUID', 'da2784e1-24f5-4112-a1a7-7d3a7e44081b')
    from utils.uuid_helper import normalize_uuid
    normalized_user_id = normalize_uuid(test_user_id)
    
    print(f"   Test User ID: {normalized_user_id}")
    
    test_config = {
        'user_id': normalized_user_id,
        'platform': 'notion_test',
        'credentials': {
            'access_token': 'test_direct_write_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
            'test': True
        },
        'is_enabled': False,  # Mark as test
        'sync_frequency_minutes': 15,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    try:
        # Try direct insert
        result = config.supabase_client.table('calendar_sync_configs').insert(test_config).execute()
        
        if result.data:
            print("   ✅ Direct database write successful!")
            print(f"   Record ID: {result.data[0].get('id', 'Unknown')}")
            
            # Clean up test record
            config.supabase_client.table('calendar_sync_configs').delete().eq('platform', 'notion_test').execute()
            print("   🧹 Cleaned up test record")
        else:
            print("   ❌ Direct write returned no data")
            
    except Exception as e:
        print(f"   ❌ Direct write failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    print("\n4️⃣ Common OAuth callback issues:")
    print("-"*50)
    print("   ❌ OAuth callback URL not matching Notion app settings")
    print("   ❌ Session lost during OAuth redirect")
    print("   ❌ user_id not properly maintained in session")
    print("   ❌ OAuth callback throwing exception before token storage")
    print("   ❌ Network issues during token exchange")
    print("   ❌ Invalid OAuth response from Notion")
    
    print("\n5️⃣ Check OAuth callback URL:")
    print("-"*50)
    print("   Local: http://localhost:5000/oauth/notion/callback")
    print("   Railway: https://[your-app].railway.app/oauth/notion/callback")
    print("   Make sure this EXACTLY matches your Notion OAuth app settings")
    
    print("\n6️⃣ Debugging steps:")
    print("-"*50)
    print("   1. Check Railway logs during OAuth flow")
    print("   2. Add logging to OAuth callback route")
    print("   3. Test OAuth with manual token insertion")
    print("   4. Verify user session during OAuth")
    
    return True

def check_oauth_redirect_uri():
    """Check what OAuth redirect URI should be"""
    print("\n" + "="*50)
    print("🔗 OAUTH REDIRECT URI CHECK")
    print("="*50)
    
    # Check if running locally or deployed
    port = os.getenv('PORT', '5000')
    railway_url = os.getenv('RAILWAY_PUBLIC_URL')
    
    if railway_url:
        callback_url = f"{railway_url}/oauth/notion/callback"
        print(f"   🚀 Railway URL: {callback_url}")
    else:
        callback_url = f"http://localhost:{port}/oauth/notion/callback"
        print(f"   🏠 Local URL: {callback_url}")
    
    print(f"\n   ✅ Use this URL in your Notion OAuth app:")
    print(f"   {callback_url}")
    
    print(f"\n   📝 Notion OAuth app settings:")
    print(f"   1. Go to https://www.notion.so/my-integrations")
    print(f"   2. Edit your OAuth integration")
    print(f"   3. Set redirect URI to: {callback_url}")
    print(f"   4. Save settings")

if __name__ == "__main__":
    debug_oauth_callback()
    check_oauth_redirect_uri()
    
    print("\n✅ Debug completed!")
    print("\n📝 Next steps if tokens still not saving:")
    print("1. Check Railway logs during OAuth flow")
    print("2. Verify Notion OAuth app redirect URI settings")
    print("3. Test manual token insertion with insert_notion_token.py")
    print("4. Add more logging to OAuth callback route")