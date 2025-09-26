#!/usr/bin/env python3
"""
Force Delete Calendar - Complete calendar deletion tool
Removes calendar and all associated data from all possible locations
"""

import sys
import os

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

def force_delete_calendar(calendar_id, user_id="e390559f-c328-4786-ac5d-c74b5409451b"):
    """Force delete a calendar from all possible locations and formats"""
    
    try:
        # Import required modules
        from utils.config import config
        from utils.uuid_helper import normalize_uuid
        
        # Get both user_id formats
        normalized_user_id = normalize_uuid(user_id)
        original_user_id = user_id
        user_id_formats = [original_user_id, normalized_user_id]
        
        print(f"[FORCE-DELETE] Calendar ID: {calendar_id}")
        print(f"[FORCE-DELETE] User ID formats: {user_id_formats}")
        
        # Get admin client
        admin_client = config.supabase_admin
        if not admin_client:
            print("❌ Supabase admin client not available")
            return False
        
        total_deleted = 0
        deletion_log = []
        
        # Show what exists first
        print("\n🔍 CURRENT STATE:")
        try:
            calendars_result = admin_client.table('calendars').select('id, name, owner_id').eq('id', calendar_id).execute()
            if calendars_result.data:
                for cal in calendars_result.data:
                    print(f"📅 Calendar: {cal['name']} (owner: {cal['owner_id']})")
            else:
                print("📅 No calendars found with this ID")
                
            events_result = admin_client.table('calendar_events').select('id, user_id, calendar_id, source_calendar_id').eq('calendar_id', calendar_id).execute()
            if events_result.data:
                print(f"📊 Found {len(events_result.data)} events by calendar_id")
                
            for uid in user_id_formats:
                events_by_user = admin_client.table('calendar_events').select('id').eq('user_id', uid).eq('source_calendar_id', calendar_id).execute()
                if events_by_user.data:
                    print(f"📊 Found {len(events_by_user.data)} events by user_id {uid}")
                    
        except Exception as e:
            print(f"⚠️ Error checking current state: {e}")
        
        print("\n🗑️ STARTING DELETION:")
        
        # Delete from ALL possible locations and formats
        for uid in user_id_formats:
            try:
                print(f"\n📋 Processing user_id format: {uid}")
                
                # 1. Delete calendar_events by calendar_id
                print("  🔸 Deleting events by calendar_id...")
                events_result1 = admin_client.table('calendar_events').delete().eq('calendar_id', calendar_id).execute()
                if events_result1.data:
                    deleted_count = len(events_result1.data)
                    total_deleted += deleted_count
                    deletion_log.append(f"Deleted {deleted_count} events by calendar_id")
                    print(f"    ✅ Deleted {deleted_count} events")
                
                # 2. Delete calendar_events by user_id + source_calendar_id
                print("  🔸 Deleting events by user_id+source_calendar_id...")
                events_result2 = admin_client.table('calendar_events').delete().eq('user_id', uid).eq('source_calendar_id', calendar_id).execute()
                if events_result2.data:
                    deleted_count = len(events_result2.data)
                    total_deleted += deleted_count
                    deletion_log.append(f"Deleted {deleted_count} events by user_id+source_calendar_id for {uid}")
                    print(f"    ✅ Deleted {deleted_count} events")
                
                # 3. Delete calendar_shares
                print("  🔸 Deleting calendar shares...")
                shares_result = admin_client.table('calendar_shares').delete().eq('calendar_id', calendar_id).execute()
                if shares_result.data:
                    deleted_count = len(shares_result.data)
                    total_deleted += deleted_count
                    deletion_log.append(f"Deleted {deleted_count} shares")
                    print(f"    ✅ Deleted {deleted_count} shares")
                
                # 4. Delete calendar itself
                print("  🔸 Deleting calendar...")
                calendar_result = admin_client.table('calendars').delete().eq('id', calendar_id).eq('owner_id', uid).execute()
                if calendar_result.data:
                    deleted_count = len(calendar_result.data)
                    total_deleted += deleted_count
                    deletion_log.append(f"Deleted calendar with owner_id {uid}")
                    print(f"    ✅ Deleted calendar with owner_id {uid}")
                
            except Exception as e:
                error_msg = f"Error with user_id {uid}: {str(e)}"
                deletion_log.append(error_msg)
                print(f"    ❌ {error_msg}")
                continue
        
        # Final cleanup - try deletion without user_id constraints
        print(f"\n🔄 FINAL CLEANUP:")
        
        try:
            print("  🔸 Final events cleanup (no user constraint)...")
            all_events_result = admin_client.table('calendar_events').delete().eq('calendar_id', calendar_id).execute()
            if all_events_result.data:
                deleted_count = len(all_events_result.data)
                total_deleted += deleted_count
                deletion_log.append(f"Final cleanup: deleted {deleted_count} events")
                print(f"    ✅ Deleted {deleted_count} remaining events")
        except Exception as e:
            print(f"    ❌ Final events cleanup error: {e}")
        
        try:
            print("  🔸 Final calendar cleanup (no owner constraint)...")
            any_calendar_result = admin_client.table('calendars').delete().eq('id', calendar_id).execute()
            if any_calendar_result.data:
                deleted_count = len(any_calendar_result.data)
                total_deleted += deleted_count
                deletion_log.append(f"Final cleanup: deleted calendar")
                print(f"    ✅ Deleted remaining calendar")
        except Exception as e:
            print(f"    ❌ Final calendar cleanup error: {e}")
        
        print(f"\n✅ FORCE DELETION COMPLETED")
        print(f"📊 Total items deleted: {total_deleted}")
        print(f"📋 Deletion log:")
        for log_entry in deletion_log:
            print(f"   • {log_entry}")
        
        return total_deleted > 0
        
    except Exception as e:
        print(f"❌ Force delete error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python force_delete_calendar.py <calendar_id> [user_id]")
        sys.exit(1)
    
    calendar_id = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 else "e390559f-c328-4786-ac5d-c74b5409451b"
    
    print(f"🚀 Starting force delete for calendar: {calendar_id}")
    success = force_delete_calendar(calendar_id, user_id)
    
    if success:
        print("\n🎉 Calendar force deletion successful!")
    else:
        print("\n💥 Calendar force deletion failed!")