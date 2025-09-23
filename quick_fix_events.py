#!/usr/bin/env python3
"""
🔧 Quick Fix for Orphaned Events
Uses existing utils to fix calendar_id issues
"""

import os
import sys

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

def quick_fix():
    """Quick fix for orphaned events using existing utils"""
    try:
        # Import existing utilities
        from utils.dashboard_data import dashboard_data
        from utils.uuid_helper import normalize_uuid
        
        if not dashboard_data or not dashboard_data.admin_client:
            print("❌ Dashboard data manager not available")
            return
        
        supabase = dashboard_data.admin_client
        
        # Use your actual user ID
        user_id = "e390559f-c328-4786-ac5d-c74b5409451b"
        normalized_user_id = normalize_uuid(user_id)
        
        print(f"🔧 Quick fixing events for user: {normalized_user_id}")
        
        # 1. Get user's calendars
        calendars = supabase.table('calendars').select('id, name').eq('owner_id', normalized_user_id).execute()
        
        if not calendars.data:
            print("❌ No calendars found")
            return
        
        primary_calendar_id = calendars.data[0]['id']
        calendar_name = calendars.data[0]['name']
        
        print(f"📅 Primary calendar: {calendar_name} ({primary_calendar_id})")
        
        # 2. Count orphaned events (null calendar_id)
        orphaned = supabase.table('calendar_events').select('id', count='exact').eq('user_id', normalized_user_id).is_('calendar_id', 'null').execute()
        
        orphan_count = orphaned.count if orphaned.count is not None else 0
        print(f"⚠️  Found {orphan_count} orphaned events")
        
        if orphan_count == 0:
            print("✅ No orphaned events found!")
            
            # Check total events
            total = supabase.table('calendar_events').select('id', count='exact').eq('user_id', normalized_user_id).execute()
            total_count = total.count if total.count is not None else 0
            
            # Check events in primary calendar
            in_calendar = supabase.table('calendar_events').select('id', count='exact').eq('user_id', normalized_user_id).eq('calendar_id', primary_calendar_id).execute()
            in_calendar_count = in_calendar.count if in_calendar.count is not None else 0
            
            print(f"📊 Total events: {total_count}")
            print(f"📊 Events in primary calendar: {in_calendar_count}")
            
            return
        
        # 3. Update orphaned events
        print(f"🔧 Updating {orphan_count} orphaned events...")
        
        update_result = supabase.table('calendar_events').update({
            'calendar_id': primary_calendar_id
        }).eq('user_id', normalized_user_id).is_('calendar_id', 'null').execute()
        
        print("✅ Update completed!")
        
        # 4. Verify
        remaining = supabase.table('calendar_events').select('id', count='exact').eq('user_id', normalized_user_id).is_('calendar_id', 'null').execute()
        remaining_count = remaining.count if remaining.count is not None else 0
        
        if remaining_count == 0:
            print("🎉 All orphaned events fixed!")
        else:
            print(f"⚠️  {remaining_count} events still orphaned")
        
        # Final stats
        total = supabase.table('calendar_events').select('id', count='exact').eq('user_id', normalized_user_id).execute()
        in_calendar = supabase.table('calendar_events').select('id', count='exact').eq('user_id', normalized_user_id).eq('calendar_id', primary_calendar_id).execute()
        
        total_count = total.count if total.count is not None else 0
        in_calendar_count = in_calendar.count if in_calendar.count is not None else 0
        
        print(f"\n📊 FINAL STATS:")
        print(f"   Total events: {total_count}")
        print(f"   Events in primary calendar: {in_calendar_count}")
        print(f"   Coverage: {in_calendar_count/total_count*100:.1f}%" if total_count > 0 else "   Coverage: 0%")
        
        if in_calendar_count > 0:
            print(f"\n🎉 SUCCESS! Your {in_calendar_count} events should now appear in calendar views!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_fix()