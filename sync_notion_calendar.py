#!/usr/bin/env python3
"""
Manual Notion Calendar Sync Script
Run this to manually sync Notion events to NotionFlow
"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def sync_notion_for_user(user_id: str, calendar_id: str):
    """Manually trigger Notion sync for a specific user"""
    
    from backend.services.notion_sync_service import notion_sync_service
    
    print(f"🔄 Starting Notion sync for user: {user_id}")
    print(f"📅 Target calendar: {calendar_id}")
    print("-" * 50)
    
    # Perform sync
    result = notion_sync_service.sync_notion_to_calendar(user_id, calendar_id)
    
    if result['success']:
        print("✅ Sync completed successfully!")
        print(f"📊 Results:")
        if 'results' in result:
            print(f"  - Databases processed: {result['results'].get('databases_processed', 0)}")
            print(f"  - Events synced: {result['results'].get('synced_events', 0)}")
            print(f"  - Failed events: {result['results'].get('failed_events', 0)}")
    else:
        print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
    
    return result

def check_notion_connection(user_id: str):
    """Check if user has Notion connected"""
    
    try:
        from backend.services.notion_sync_service import notion_sync_service
        
        token = notion_sync_service.get_user_notion_token(user_id)
        
        if token:
            print(f"✅ Notion token found for user {user_id}")
            print(f"🔑 Token preview: {token[:20]}...")
            return True
        else:
            print(f"❌ No Notion token found for user {user_id}")
            print("Please connect Notion first through the dashboard")
            return False
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("\n⚠️  Please install required packages:")
        print("pip install httpx==0.24.1 notion-client==2.2.1")
        return False
    except Exception as e:
        print(f"❌ Error checking connection: {e}")
        return False

def main():
    """Main execution"""
    
    # Your user and calendar IDs
    USER_ID = "87875eda6797f839f8c70aa90efb1352"  # Your user ID from logs
    CALENDAR_ID = "de110742-c2dc-4986-9267-7c12fe1303a1"  # Your calendar ID from logs
    
    print("=" * 60)
    print("NOTION CALENDAR SYNC TOOL")
    print("=" * 60)
    print(f"User ID: {USER_ID}")
    print(f"Calendar ID: {CALENDAR_ID}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Step 1: Check connection
    print("\n📌 Step 1: Checking Notion connection...")
    if not check_notion_connection(USER_ID):
        print("\n⚠️  Please follow these steps:")
        print("1. Go to your NotionFlow dashboard")
        print("2. Navigate to API Keys page")
        print("3. Click 'Connect' for Notion")
        print("4. Complete the OAuth flow")
        print("5. Run this script again")
        return
    
    # Step 2: Sync events
    print("\n📌 Step 2: Syncing Notion events...")
    result = sync_notion_for_user(USER_ID, CALENDAR_ID)
    
    # Step 3: Verify sync
    if result['success']:
        print("\n📌 Step 3: Verifying sync...")
        
        # Check events in database
        from utils.config import get_supabase_admin
        supabase = get_supabase_admin()
        
        events = supabase.table('calendar_events').select('*').eq(
            'calendar_id', CALENDAR_ID
        ).eq('external_platform', 'notion').execute()
        
        if events.data:
            print(f"✅ Found {len(events.data)} Notion events in calendar")
            for event in events.data[:5]:  # Show first 5
                print(f"  📅 {event['title']} - {event['start_date']}")
        else:
            print("⚠️  No Notion events found in calendar")
            print("This might mean:")
            print("  - Your Notion databases don't have calendar/event pages")
            print("  - The databases don't have proper date fields")
            print("  - The integration doesn't have access to your databases")
    
    print("\n" + "=" * 60)
    print("Sync process completed!")
    print("=" * 60)

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run sync
    main()