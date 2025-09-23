#!/usr/bin/env python3
"""
🔍 Calendar Data Debug Script
Diagnose calendar_id mismatch issues between events and calendars
"""

import os
import sys

# Add utils to path first
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

try:
    from utils.config import config
    from utils.uuid_helper import normalize_uuid
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def debug_calendar_data():
    """Analyze calendar and event data to identify mismatches"""
    
    # Use existing config
    if not config.supabase_admin:
        print("❌ Supabase admin client not configured")
        return
    
    supabase = config.supabase_admin
    
    # Your user ID (replace with actual)
    user_id = "e390559f-c328-4786-ac5d-c74b5409451b"  # Update this
    normalized_user_id = normalize_uuid(user_id)
    
    print(f"🔍 Debugging data for user: {user_id}")
    print(f"🔍 Normalized user ID: {normalized_user_id}")
    print("=" * 60)
    
    # 1. Check calendars table
    print("\n📅 CALENDARS TABLE:")
    calendars_result = supabase.table('calendars').select('*').or_(
        f'owner_id.eq.{user_id},owner_id.eq.{normalized_user_id}'
    ).execute()
    
    calendars = calendars_result.data or []
    print(f"Found {len(calendars)} calendars")
    
    calendar_ids = []
    for cal in calendars:
        calendar_ids.append(cal['id'])
        print(f"  • {cal['name']} (ID: {cal['id']}) - Owner: {cal['owner_id']}")
    
    # 2. Check calendar_events table
    print("\n📋 CALENDAR_EVENTS TABLE:")
    events_result = supabase.table('calendar_events').select('*').eq(
        'user_id', normalized_user_id
    ).execute()
    
    events = events_result.data or []
    print(f"Found {len(events)} events")
    
    # Analyze calendar_id distribution
    calendar_id_counts = {}
    null_calendar_ids = 0
    
    for event in events:
        cal_id = event.get('calendar_id')
        if cal_id is None:
            null_calendar_ids += 1
        else:
            calendar_id_counts[cal_id] = calendar_id_counts.get(cal_id, 0) + 1
        
        print(f"  • {event['title'][:50]}... - Calendar ID: {cal_id} - Platform: {event.get('source_platform', 'unknown')}")
    
    # 3. Analyze mismatches
    print("\n🔍 ANALYSIS:")
    print(f"Calendar IDs in calendars table: {calendar_ids}")
    print(f"Calendar IDs in events: {list(calendar_id_counts.keys())}")
    print(f"Events with NULL calendar_id: {null_calendar_ids}")
    
    # Find orphaned events (events with calendar_id not in calendars table)
    orphaned_events = []
    for cal_id in calendar_id_counts.keys():
        if cal_id not in calendar_ids:
            orphaned_events.append(cal_id)
    
    if orphaned_events:
        print(f"⚠️  ORPHANED EVENTS found with calendar_ids: {orphaned_events}")
        print(f"   These events reference non-existent calendars!")
    
    if null_calendar_ids > 0:
        print(f"⚠️  {null_calendar_ids} events have NULL calendar_id")
    
    # 4. Check calendar_sync_configs
    print("\n⚙️  SYNC CONFIGS:")
    configs_result = supabase.table('calendar_sync_configs').select('*').eq(
        'user_id', normalized_user_id
    ).execute()
    
    configs = configs_result.data or []
    for config in configs:
        print(f"  • Platform: {config['platform']} - Enabled: {config['is_enabled']} - Calendar ID: {config.get('calendar_id', 'None')}")
    
    # 5. Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if orphaned_events:
        print("1. Fix orphaned events:")
        print("   - Update their calendar_id to match existing calendar")
        print("   - Or create missing calendars")
    
    if null_calendar_ids > 0:
        print("2. Fix NULL calendar_id events:")
        print("   - Assign them to a default calendar")
        print("   - Update Notion sync to always set calendar_id")
    
    if not calendars:
        print("3. Create a default calendar for the user")
    
    return {
        'calendars': calendars,
        'events': events,
        'calendar_id_counts': calendar_id_counts,
        'null_calendar_ids': null_calendar_ids,
        'orphaned_events': orphaned_events
    }

if __name__ == "__main__":
    debug_calendar_data()