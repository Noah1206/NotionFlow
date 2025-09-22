#!/usr/bin/env python3
"""
Find all Notion tokens in the database with different UUID formats
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import Config

# Load environment variables
load_dotenv()

def find_all_notion_data():
    """Find all Notion-related data in database"""
    print("\n" + "="*50)
    print("🔍 SEARCHING FOR ALL NOTION DATA")
    print("="*50)
    
    # Initialize config
    config = Config()
    
    print("\n1️⃣ ALL oauth_tokens for Notion:")
    print("-"*50)
    
    try:
        # Get ALL Notion tokens regardless of user
        oauth_result = config.supabase_client.table('oauth_tokens').select('*').eq(
            'platform', 'notion'
        ).execute()
        
        if oauth_result.data:
            print(f"✅ Found {len(oauth_result.data)} Notion OAuth token(s):")
            for i, token in enumerate(oauth_result.data, 1):
                print(f"\n[{i}] Token Entry:")
                print(f"   User ID: {token.get('user_id', 'Unknown')}")
                print(f"   Access Token: {token.get('access_token', '')[:40]}...")
                print(f"   Refresh Token: {token.get('refresh_token', '')[:40] if token.get('refresh_token') else 'None'}...")
                print(f"   Created: {token.get('created_at', 'Unknown')}")
                print(f"   Updated: {token.get('updated_at', 'Unknown')}")
        else:
            print("❌ No Notion OAuth tokens found at all")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n2️⃣ ALL calendar_sync_configs for Notion:")
    print("-"*50)
    
    try:
        # Get ALL Notion sync configs
        sync_result = config.supabase_client.table('calendar_sync_configs').select('*').eq(
            'platform', 'notion'
        ).execute()
        
        if sync_result.data:
            print(f"✅ Found {len(sync_result.data)} Notion sync config(s):")
            for i, cfg in enumerate(sync_result.data, 1):
                print(f"\n[{i}] Sync Config:")
                print(f"   User ID: {cfg.get('user_id', 'Unknown')}")
                print(f"   Calendar ID: {cfg.get('calendar_id', 'None')}")
                print(f"   Enabled: {cfg.get('is_enabled', False)}")
                print(f"   Last Sync: {cfg.get('last_sync_at', 'Never')}")
                
                credentials = cfg.get('credentials', {})
                if isinstance(credentials, dict):
                    if 'access_token' in credentials:
                        print(f"   Has Access Token: Yes ({credentials['access_token'][:30]}...)")
                    else:
                        print(f"   Has Access Token: No")
                    print(f"   Credential Fields: {list(credentials.keys())}")
        else:
            print("❌ No Notion sync configs found at all")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n3️⃣ Checking different user ID formats:")
    print("-"*50)
    
    # Test user variations
    test_email = "johyeonwooung@gmail.com"
    test_variations = [
        "da2784e1-24f5-4112-a1a7-7d3a7e44081b",  # Original with hyphens
        "da2784e124f54112a1a77d3a7e44081b",      # Without hyphens
        "DA2784E1-24F5-4112-A1A7-7D3A7E44081B",  # Uppercase with hyphens
        "DA2784E124F54112A1A77D3A7E44081B",      # Uppercase without hyphens
        test_email                                # Email format
    ]
    
    for user_id in test_variations:
        print(f"\n🔍 Checking: {user_id}")
        
        try:
            # Check oauth_tokens
            oauth = config.supabase_client.table('oauth_tokens').select('platform').eq(
                'user_id', user_id
            ).eq('platform', 'notion').execute()
            
            if oauth.data:
                print(f"   ✅ Found in oauth_tokens!")
            
            # Check calendar_sync_configs
            sync = config.supabase_client.table('calendar_sync_configs').select('platform').eq(
                'user_id', user_id
            ).eq('platform', 'notion').execute()
            
            if sync.data:
                print(f"   ✅ Found in calendar_sync_configs!")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n4️⃣ Recent OAuth activities (last 10):")
    print("-"*50)
    
    try:
        # Get recent oauth tokens
        recent = config.supabase_client.table('oauth_tokens').select(
            'user_id, platform, created_at'
        ).order('created_at', desc=True).limit(10).execute()
        
        if recent.data:
            print("Recent OAuth tokens:")
            for entry in recent.data:
                print(f"   {entry['created_at']}: {entry['platform']} - {entry['user_id']}")
        else:
            print("❌ No recent OAuth tokens")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n5️⃣ Searching by email in user_profiles:")
    print("-"*50)
    
    try:
        # Find user by email
        user_result = config.supabase_client.table('user_profiles').select('*').eq(
            'email', test_email
        ).execute()
        
        if user_result.data:
            print(f"✅ Found user profile:")
            for profile in user_result.data:
                print(f"   ID: {profile.get('id')}")
                print(f"   Email: {profile.get('email')}")
                print(f"   Username: {profile.get('username')}")
                print(f"   Created: {profile.get('created_at')}")
                
                # Now check if this ID has Notion tokens
                user_id = profile.get('id')
                if user_id:
                    print(f"\n   Checking Notion data for this user ID ({user_id}):")
                    
                    oauth = config.supabase_client.table('oauth_tokens').select('*').eq(
                        'user_id', user_id
                    ).eq('platform', 'notion').execute()
                    
                    if oauth.data:
                        print(f"   ✅ HAS Notion OAuth token!")
                    else:
                        print(f"   ❌ NO Notion OAuth token")
                    
                    sync = config.supabase_client.table('calendar_sync_configs').select('*').eq(
                        'user_id', user_id
                    ).eq('platform', 'notion').execute()
                    
                    if sync.data:
                        print(f"   ✅ HAS Notion sync config!")
                    else:
                        print(f"   ❌ NO Notion sync config")
        else:
            print(f"❌ No user profile found for {test_email}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*50)
    print("✅ Search completed!")
    print("="*50)

if __name__ == "__main__":
    find_all_notion_data()