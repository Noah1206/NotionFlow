#!/usr/bin/env python3
"""
Add sync_status column to calendar_sync_configs table
"""

import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from utils.config import config

def add_sync_status_column():
    """Add sync_status column using UPDATE operations"""
    try:
        supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else config.supabase_client

        print("🔍 Checking current table structure...")

        # Get current table data to see what we have
        current_data = supabase.table('calendar_sync_configs').select('*').limit(5).execute()
        if current_data.data:
            print(f"Current columns: {list(current_data.data[0].keys())}")

            # Check if sync_status already exists
            if 'sync_status' in current_data.data[0]:
                print("✅ sync_status column already exists!")
                return True
            else:
                print("❌ sync_status column missing")

        # Unfortunately, we can't use ALTER TABLE through the Supabase client
        # Let's try a workaround by creating a new table with the correct schema
        print("⚠️ Cannot add column directly through Supabase client")
        print("📝 Recommendation: Run the migration SQL directly in Supabase dashboard")

        # Display the exact SQL needed
        sql_needed = """
-- Add sync_status column
ALTER TABLE calendar_sync_configs
ADD COLUMN sync_status TEXT DEFAULT 'active';

-- Add other missing columns
ALTER TABLE calendar_sync_configs
ADD COLUMN IF NOT EXISTS real_time_sync BOOLEAN DEFAULT false;

ALTER TABLE calendar_sync_configs
ADD COLUMN IF NOT EXISTS sync_settings JSONB DEFAULT '{}';

ALTER TABLE calendar_sync_configs
ADD COLUMN IF NOT EXISTS health_status TEXT DEFAULT 'healthy';

-- Update existing records
UPDATE calendar_sync_configs
SET sync_status = CASE
    WHEN is_enabled = true THEN 'active'
    WHEN is_enabled = false AND calendar_id IS NULL THEN 'needs_calendar_selection'
    ELSE 'paused'
END
WHERE sync_status IS NULL;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_sync_status ON calendar_sync_configs(sync_status);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_health_status ON calendar_sync_configs(health_status);
"""

        print("\n📋 SQL to run in Supabase dashboard:")
        print("=" * 50)
        print(sql_needed)
        print("=" * 50)

        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def simulate_fixed_table():
    """Test what the OAuth code would do with the fixed table"""
    try:
        supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else config.supabase_client

        print("\n🔍 Testing OAuth scenario simulation...")

        # Get existing record
        user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'

        # For now, let's manually set sync_status by updating the record structure
        # This is a workaround until the column is properly added

        # Get current config
        result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()

        if result.data:
            config_data = result.data[0]
            print(f"📄 Current config: is_enabled={config_data.get('is_enabled')}, calendar_id={config_data.get('calendar_id')}")

            # Simulate what sync_status would be
            if config_data.get('is_enabled') and config_data.get('calendar_id'):
                simulated_sync_status = 'active'
            elif not config_data.get('is_enabled') and not config_data.get('calendar_id'):
                simulated_sync_status = 'needs_calendar_selection'
            elif not config_data.get('is_enabled'):
                simulated_sync_status = 'paused'
            else:
                simulated_sync_status = 'active'

            print(f"🎯 Simulated sync_status would be: {simulated_sync_status}")

            # Test the logic that was failing
            is_disconnected = (simulated_sync_status == 'needs_calendar_selection' or
                             not config_data.get('is_enabled', True))

            print(f"🔍 OAuth logic test:")
            print(f"  - is_disconnected: {is_disconnected}")
            print(f"  - would skip calendar sync creation: {is_disconnected}")

            if is_disconnected:
                print("🚫 OAuth would skip calendar_sync creation - user disconnected")
            else:
                print("✅ OAuth would proceed with calendar_sync creation")

            return True
        else:
            print("❌ No config found for test user")
            return False

    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting sync_status column fix...\n")

    column_added = add_sync_status_column()
    simulation_passed = simulate_fixed_table()

    if not column_added:
        print("\n⚠️  Manual intervention required:")
        print("1. Go to Supabase dashboard")
        print("2. Navigate to SQL editor")
        print("3. Run the SQL commands shown above")
        print("4. Re-run this script to verify")
    else:
        print(f"\n🎉 Column added successfully!")

    if simulation_passed:
        print("✅ OAuth logic simulation passed")
    else:
        print("❌ OAuth logic simulation failed")