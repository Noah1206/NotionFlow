#!/usr/bin/env python3
"""Debug event count discrepancy between API key page and calendar list page"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, '/Users/johyeon-ung/Desktop/NotionFlow')

try:
    # Try different import methods
    try:
        from supabase import create_client, Client
        print("✅ Using supabase library directly")
    except ImportError:
        try:
            from postgrest import APIClient
            print("✅ Using postgrest fallback")
        except ImportError:
            print("❌ No database libraries available")
            sys.exit(1)
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    print(f"✅ Connected to Supabase: {supabase_url[:30]}...")
    
    # Get user data
    print("\n🔍 Finding user...")
    user_result = supabase.table('profiles').select('*').limit(1).execute()
    
    if not user_result.data:
        print("❌ No users found")
        sys.exit(1)
    
    user_id = user_result.data[0]['id']
    print(f"👤 User ID: {user_id}")
    
    print("\n📊 Checking event counts...")
    
    # Method 1: API Key Page Logic (Total Events)
    print("\n1️⃣ API Key Page Method:")
    total_events = supabase.table('calendar_events').select('id', count='exact').eq('user_id', user_id).execute()
    api_key_count = total_events.count or 0
    print(f"   Total Events: {api_key_count}")
    
    # Method 2: Calendar List Page Logic (Per Calendar Sum)
    print("\n2️⃣ Calendar List Page Method:")
    calendars = supabase.table('calendars').select('id, name').eq('owner_id', user_id).execute()
    calendar_total = 0
    
    for cal in calendars.data:
        cal_events = supabase.table('calendar_events').select('id', count='exact').eq('user_id', user_id).eq('calendar_id', cal['id']).execute()
        cal_count = cal_events.count or 0
        calendar_total += cal_count
        print(f"   📅 {cal['name']} ({cal['id'][:8]}...): {cal_count} events")
    
    print(f"   Sum of Calendar Events: {calendar_total}")
    
    # Check for orphaned events
    print("\n3️⃣ Orphaned Events Check:")
    orphaned = supabase.table('calendar_events').select('id', count='exact').eq('user_id', user_id).is_('calendar_id', 'null').execute()
    orphaned_count = orphaned.count or 0
    print(f"   Events with no calendar_id: {orphaned_count}")
    
    # Summary
    print("\n" + "="*50)
    print("📈 SUMMARY:")
    print(f"   API Key Page Shows: {api_key_count} events")
    print(f"   Calendar List Shows: {calendar_total} events")
    print(f"   Orphaned Events: {orphaned_count} events")
    print(f"   Expected Total: {calendar_total + orphaned_count} events")
    
    if api_key_count != calendar_total:
        print("\n⚠️ DISCREPANCY FOUND!")
        difference = calendar_total - api_key_count
        print(f"   Difference: {difference} events")
        
        if orphaned_count > 0:
            print(f"   This might be due to {orphaned_count} orphaned events")
        
        # Show sample events to debug
        print("\n🔍 Sample Events:")
        sample_events = supabase.table('calendar_events').select('id, title, calendar_id, source_platform, created_at').eq('user_id', user_id).limit(10).execute()
        for event in sample_events.data:
            cal_id = event.get('calendar_id', 'None')[:8] if event.get('calendar_id') else 'None'
            print(f"   - {event['title'][:30]:<30} | Calendar: {cal_id:<8} | Platform: {event.get('source_platform', 'N/A')}")
    else:
        print("\n✅ Counts match!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()