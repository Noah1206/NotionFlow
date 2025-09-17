#!/usr/bin/env python3
"""
Fix RLS Policies for NotionFlow
"""

import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

def execute_sql_via_api(sql_query):
    """Execute SQL using Supabase REST API"""
    try:
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Missing Supabase credentials")
            return False
        
        # Use RPC to execute SQL
        url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'sql': sql_query
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ SQL executed successfully")
            return True
        else:
            print(f"❌ SQL execution failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error executing SQL: {e}")
        return False

def fix_rls_policies():
    """Fix RLS policies for calendar_sync and other tables"""
    
    print("🔧 Fixing RLS policies...")
    
    # 1. Fix calendar_sync table RLS
    print("1. Fixing calendar_sync RLS...")
    calendar_sync_sql = '''
    -- Drop existing policies if they exist
    DROP POLICY IF EXISTS "calendar_sync_user_policy" ON calendar_sync;
    DROP POLICY IF EXISTS "Users can manage own sync" ON calendar_sync;
    
    -- Create new policy for calendar_sync
    CREATE POLICY "calendar_sync_user_policy" ON calendar_sync
        FOR ALL 
        USING (user_id = auth.uid() OR user_id::text = current_setting('app.current_user_id', true));
    '''
    
    if execute_sql_via_api(calendar_sync_sql):
        print("   ✅ calendar_sync RLS fixed")
    else:
        print("   ❌ calendar_sync RLS failed")
    
    # 2. Fix oauth_states table RLS
    print("2. Fixing oauth_states RLS...")
    oauth_states_sql = '''
    -- Drop existing policies if they exist
    DROP POLICY IF EXISTS "oauth_states_user_policy" ON oauth_states;
    DROP POLICY IF EXISTS "Users can manage own oauth states" ON oauth_states;
    
    -- Create new policy for oauth_states
    CREATE POLICY "oauth_states_user_policy" ON oauth_states
        FOR ALL 
        USING (user_id = auth.uid() OR user_id::text = current_setting('app.current_user_id', true));
    '''
    
    if execute_sql_via_api(oauth_states_sql):
        print("   ✅ oauth_states RLS fixed")
    else:
        print("   ❌ oauth_states RLS failed")
    
    # 3. Fix sync_events table RLS
    print("3. Fixing sync_events RLS...")
    sync_events_sql = '''
    -- Drop existing policies if they exist
    DROP POLICY IF EXISTS "sync_events_user_policy" ON sync_events;
    DROP POLICY IF EXISTS "Users can manage own sync events" ON sync_events;
    
    -- Create new policy for sync_events
    CREATE POLICY "sync_events_user_policy" ON sync_events
        FOR ALL 
        USING (user_id = auth.uid() OR user_id::text = current_setting('app.current_user_id', true));
    '''
    
    if execute_sql_via_api(sync_events_sql):
        print("   ✅ sync_events RLS fixed")
    else:
        print("   ❌ sync_events RLS failed")
    
    # 4. Add missing columns if needed
    print("4. Adding missing columns...")
    missing_columns_sql = '''
    -- Add connection_method column to platform_connections if not exists
    ALTER TABLE platform_connections 
    ADD COLUMN IF NOT EXISTS connection_method VARCHAR(50) DEFAULT 'oauth';
    
    -- Fix user_id column in calendars table if needed
    DO $$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'calendars' AND column_name = 'user_id') THEN
            ALTER TABLE calendars ADD COLUMN user_id UUID REFERENCES users(id);
            UPDATE calendars SET user_id = owner_id WHERE user_id IS NULL;
        END IF;
    END $$;
    '''
    
    if execute_sql_via_api(missing_columns_sql):
        print("   ✅ Missing columns added")
    else:
        print("   ❌ Missing columns failed")
    
    print("\n🎉 RLS policies fix completed!")

def main():
    print("=" * 60)
    print("NOTIONFLOW RLS POLICIES FIX")
    print("=" * 60)
    
    fix_rls_policies()
    
    print("\n" + "=" * 60)
    print("Fix completed! Now try selecting a calendar to test Notion sync.")
    print("=" * 60)

if __name__ == "__main__":
    main()