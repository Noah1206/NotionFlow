#!/usr/bin/env python3
"""
🔄 Force Notion Resync
Delete existing Notion events and force fresh sync
"""

import os
import sys

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

def force_resync():
    """Force fresh Notion sync by clearing existing events"""
    try:
        from utils.config import config
        from utils.uuid_helper import normalize_uuid
        
        if not config.supabase_admin:
            print("❌ Supabase admin client not available")
            return
        
        supabase = config.supabase_admin
        
        # User ID
        user_id = "e390559f-c328-4786-ac5d-c74b5409451b"
        normalized_user_id = normalize_uuid(user_id)
        
        print(f"🔄 Force resyncing Notion events for user: {normalized_user_id}")
        
        # 1. Count existing Notion events
        existing = supabase.table('calendar_events').select('id', count='exact').eq('user_id', normalized_user_id).eq('source_platform', 'notion').execute()
        existing_count = existing.count if existing.count is not None else 0
        
        print(f"📊 Found {existing_count} existing Notion events")
        
        if existing_count == 0:
            print("✅ No existing Notion events to delete")
        else:
            # 2. Delete existing Notion events
            print(f"🗑️ Deleting {existing_count} existing Notion events...")
            
            delete_result = supabase.table('calendar_events').delete().eq('user_id', normalized_user_id).eq('source_platform', 'notion').execute()
            
            print(f"✅ Deleted {existing_count} Notion events")
        
        # 3. Trigger fresh sync
        print(f"🔄 Now trigger Notion sync from the web interface!")
        print(f"🌐 Go to API Keys page and click 'Sync Notion'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    force_resync()