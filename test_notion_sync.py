#!/usr/bin/env python3
"""
Test script to verify Notion sync functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add necessary paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

# Load environment
load_dotenv()

def test_notion_sync():
    print("🧪 Testing Notion sync functionality...")
    
    try:
        from services.notion_sync import notion_sync
        print("✅ Successfully imported notion_sync")
        
        # Test with a sample user ID (use the one from the error)
        user_id = "87875eda-6797-f839-f8c7-0aa90efb1352"
        calendar_id = "test_calendar"
        
        print(f"🔍 Testing token retrieval for user {user_id}")
        token = notion_sync.get_user_notion_token(user_id)
        
        if token:
            print(f"✅ Token found: {token[:20]}...")
            
            # Test Notion API connection
            from services.notion_sync import NotionAPI
            api = NotionAPI(token)
            
            print("🔍 Testing Notion API connection...")
            databases = api.search_databases()
            
            if databases:
                print(f"✅ Found {len(databases)} databases in Notion")
                for db in databases[:3]:  # Show first 3
                    title = db.get('title', [{}])
                    if title:
                        db_title = title[0].get('plain_text', 'Untitled')
                        print(f"   📋 {db_title}")
                
                print("🔄 Testing calendar sync...")
                result = notion_sync.sync_to_calendar(user_id, calendar_id)
                
                if result['success']:
                    print(f"✅ Sync successful! Synced {result['synced_events']} events")
                else:
                    print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
            else:
                print("⚠️ No databases found in Notion (might be permission issue)")
        else:
            print("❌ No Notion token found")
            print("💡 Make sure to connect your Notion account first via the web interface")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_notion_sync()
