#!/usr/bin/env python3
"""
Debug script to test Notion sync for specific user
"""

import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from services.notion_sync import NotionCalendarSync, sync_notion_calendar_for_user
from utils.config import config

def debug_notion_sync():
    """Debug the Notion sync process step by step"""

    # Test user from logs
    user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'

    print("🔍 Debugging Notion sync for user:", user_id)
    print("=" * 60)

    # Create sync instance
    notion_sync = NotionCalendarSync()

    # Step 1: Check if user has calendar
    print("\n1️⃣ Checking user calendar...")
    calendar_id = notion_sync.get_user_calendar_id(user_id)
    print(f"   Calendar ID: {calendar_id}")

    if not calendar_id:
        print("❌ No calendar found for user")
        return False

    # Step 2: Check Notion token
    print("\n2️⃣ Checking Notion token...")
    token = notion_sync.get_user_notion_token(user_id)
    if token:
        print(f"   ✅ Token found: {token[:20]}...")
    else:
        print("   ❌ No token found")
        return False

    # Step 3: Test Notion API access
    print("\n3️⃣ Testing Notion API access...")
    from services.notion_sync import NotionAPI

    notion_api = NotionAPI(token)
    databases = notion_api.search_databases()
    print(f"   📚 Found {len(databases)} total databases")

    if databases:
        print("   Database list:")
        for i, db in enumerate(databases[:5]):  # Show first 5
            title = db.get('title', [{}])
            if title and len(title) > 0:
                db_title = title[0].get('plain_text', 'Untitled')
            else:
                db_title = 'Untitled'
            print(f"     {i+1}. {db_title} (ID: {db['id']})")

    # Step 4: Find calendar databases
    print("\n4️⃣ Finding calendar databases...")
    calendar_dbs = notion_sync.find_calendar_databases(notion_api)
    print(f"   📅 Found {len(calendar_dbs)} calendar databases")

    if calendar_dbs:
        print("   Calendar databases:")
        for i, db in enumerate(calendar_dbs):
            title = db.get('title', [{}])
            if title and len(title) > 0:
                db_title = title[0].get('plain_text', 'Untitled')
            else:
                db_title = 'Untitled'
            print(f"     {i+1}. {db_title} (ID: {db['id']})")
    else:
        print("   ⚠️ No calendar databases found")
        print("   💡 Try creating a database in Notion with:")
        print("      - Title containing 'Calendar', 'Schedule', or 'Events'")
        print("      - OR a Date property for calendar events")
        return False

    # Step 5: Test querying first calendar database
    if calendar_dbs:
        print("\n5️⃣ Testing database query...")
        first_db = calendar_dbs[0]
        db_id = first_db['id']

        # Get database title
        title = first_db.get('title', [{}])
        if title and len(title) > 0:
            db_title = title[0].get('plain_text', 'Untitled')
        else:
            db_title = 'Untitled'

        print(f"   Querying database: {db_title}")

        try:
            query_result = notion_api.query_database(db_id, page_size=5)
            pages = query_result.get('results', [])
            print(f"   📄 Found {len(pages)} pages/events")

            if pages:
                print("   Sample events:")
                for i, page in enumerate(pages[:3]):  # Show first 3
                    page_title = "Untitled"
                    if 'properties' in page:
                        for prop_name, prop_data in page['properties'].items():
                            if prop_data.get('type') == 'title':
                                title_data = prop_data.get('title', [])
                                if title_data and len(title_data) > 0:
                                    page_title = title_data[0].get('plain_text', 'Untitled')
                                    break

                    print(f"     {i+1}. {page_title}")
            else:
                print("   ⚠️ No events found in this database")

        except Exception as e:
            print(f"   ❌ Error querying database: {e}")

    # Step 6: Test full sync
    print("\n6️⃣ Testing full sync...")
    try:
        result = sync_notion_calendar_for_user(user_id, calendar_id)
        print(f"   📊 Sync result: {result}")

        if result.get('success'):
            synced_count = result.get('synced_count', 0)
            print(f"   ✅ Sync completed: {synced_count} events synced")

            if synced_count == 0:
                print("   ⚠️ No events were synced. Possible reasons:")
                print("      - Calendar databases found but contain no events")
                print("      - Events found but failed to insert into calendar_events table")
                print("      - Date format issues preventing event creation")
        else:
            error = result.get('error', 'Unknown error')
            print(f"   ❌ Sync failed: {error}")

        return result.get('success', False)

    except Exception as e:
        print(f"   ❌ Sync error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_calendar_events_table():
    """Check if events are actually in the calendar_events table"""
    print("\n7️⃣ Checking calendar_events table...")

    user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'

    try:
        supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else config.supabase_client

        # Check total events for user
        result = supabase.table('calendar_events').select('*').eq('user_id', user_id).execute()

        if result.data:
            print(f"   📊 Found {len(result.data)} events in calendar_events table")

            # Show Notion events specifically
            notion_events = [e for e in result.data if e.get('source_platform') == 'notion']
            print(f"   📝 Notion events: {len(notion_events)}")

            if notion_events:
                print("   Recent Notion events:")
                for i, event in enumerate(notion_events[-3:]):  # Last 3
                    print(f"     {i+1}. {event.get('title', 'No title')} - {event.get('start_datetime', 'No date')}")
        else:
            print(f"   📊 No events found in calendar_events table for user")

    except Exception as e:
        print(f"   ❌ Error checking calendar_events: {e}")

if __name__ == "__main__":
    print("🚀 NotionFlow Notion Sync Debug Tool\n")

    success = debug_notion_sync()
    check_calendar_events_table()

    print("\n" + "=" * 60)
    if success:
        print("✅ Debug completed - Check the detailed output above for insights")
    else:
        print("❌ Debug found issues - Check the error messages above")

    print("\n💡 Next steps:")
    print("   1. Fix OAuth callback errors (completed)")
    print("   2. Ensure Notion workspace has calendar databases")
    print("   3. Check if calendar_events table receives data")
    print("   4. Verify date format parsing in Notion events")