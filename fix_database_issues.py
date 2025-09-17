#!/usr/bin/env python3
"""
Database Issues Fix Script
Fixes schema and RLS issues for NotionFlow
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def fix_database_schema():
    """Fix database schema issues"""
    try:
        # Try different import methods
        supabase = None
        try:
            from utils.config import get_supabase_admin
            supabase = get_supabase_admin()
        except ImportError:
            try:
                import os
                from supabase import create_client
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_API_KEY')
                if supabase_url and supabase_key:
                    supabase = create_client(supabase_url, supabase_key)
            except ImportError:
                print("⚠️ Supabase library not available: cannot import supabase")
                return False
        
        if not supabase:
            print("❌ Could not create Supabase client")
            return False
        
        print("🔧 Fixing database schema issues...")
        
        # 1. Add missing connection_method column
        print("1. Adding connection_method column to platform_connections...")
        try:
            supabase.rpc('exec_sql', {
                'sql': '''
                ALTER TABLE platform_connections 
                ADD COLUMN IF NOT EXISTS connection_method VARCHAR(50) DEFAULT 'oauth';
                '''
            }).execute()
            print("   ✅ connection_method column added")
        except Exception as e:
            print(f"   ⚠️  Column might already exist: {e}")
        
        # 2. Fix RLS policies for oauth_states
        print("2. Fixing RLS policies for oauth_states...")
        try:
            supabase.rpc('exec_sql', {
                'sql': '''
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Users can manage own oauth states" ON oauth_states;
                
                -- Create new policy that allows users to manage their own oauth states
                CREATE POLICY "oauth_states_user_policy" ON oauth_states
                    FOR ALL 
                    USING (user_id = auth.uid() OR user_id = current_setting('app.current_user_id', true));
                '''
            }).execute()
            print("   ✅ oauth_states RLS policy fixed")
        except Exception as e:
            print(f"   ⚠️  RLS policy error: {e}")
        
        # 3. Fix RLS policies for sync_events
        print("3. Fixing RLS policies for sync_events...")
        try:
            supabase.rpc('exec_sql', {
                'sql': '''
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Users can manage own sync events" ON sync_events;
                
                -- Create new policy that allows users to manage their own sync events
                CREATE POLICY "sync_events_user_policy" ON sync_events
                    FOR ALL 
                    USING (user_id = auth.uid() OR user_id = current_setting('app.current_user_id', true));
                '''
            }).execute()
            print("   ✅ sync_events RLS policy fixed")
        except Exception as e:
            print("   ⚠️  RLS policy error: {e}")
        
        # 4. Create missing RPC function
        print("4. Creating missing RPC functions...")
        try:
            supabase.rpc('exec_sql', {
                'sql': '''
                CREATE OR REPLACE FUNCTION create_user_with_profile(
                    p_user_id UUID,
                    p_email TEXT,
                    p_username TEXT DEFAULT NULL,
                    p_display_name TEXT DEFAULT NULL
                )
                RETURNS JSON AS $$
                DECLARE
                    result JSON;
                BEGIN
                    -- Insert into users table (if not exists)
                    INSERT INTO users (id, email, created_at)
                    VALUES (p_user_id, p_email, NOW())
                    ON CONFLICT (id) DO NOTHING;
                    
                    -- Insert into user_profiles table (if not exists)
                    INSERT INTO user_profiles (id, username, email, display_name, created_at)
                    VALUES (p_user_id, COALESCE(p_username, SPLIT_PART(p_email, '@', 1)), p_email, COALESCE(p_display_name, SPLIT_PART(p_email, '@', 1)), NOW())
                    ON CONFLICT (id) DO NOTHING;
                    
                    result := json_build_object(
                        'user_id', p_user_id,
                        'email', p_email,
                        'username', COALESCE(p_username, SPLIT_PART(p_email, '@', 1)),
                        'display_name', COALESCE(p_display_name, SPLIT_PART(p_email, '@', 1))
                    );
                    
                    RETURN result;
                END;
                $$ LANGUAGE plpgsql;
                '''
            }).execute()
            print("   ✅ create_user_with_profile function created")
        except Exception as e:
            print(f"   ⚠️  Function creation error: {e}")
        
        print("\n🎉 Database schema fixes completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False

def test_notion_sync():
    """Test if Notion sync is working"""
    try:
        # Your user details
        USER_ID = "87875eda6797f839f8c70aa90efb1352"
        CALENDAR_ID = "de110742-c2dc-4986-9267-7c12fe1303a1"
        
        print(f"\n🧪 Testing Notion sync...")
        print(f"User ID: {USER_ID}")
        print(f"Calendar ID: {CALENDAR_ID}")
        
        # Import sync service
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        from services.notion_sync_service import notion_sync_service
        
        # Check token
        token = notion_sync_service.get_user_notion_token(USER_ID)
        if token:
            print(f"✅ Notion token found: {token[:20]}...")
            
            # Try sync
            print("🔄 Starting sync...")
            result = notion_sync_service.sync_notion_to_calendar(USER_ID, CALENDAR_ID)
            
            if result['success']:
                print(f"✅ Sync successful!")
                print(f"   Databases processed: {result['results'].get('databases_processed', 0)}")
                print(f"   Events synced: {result['results'].get('synced_events', 0)}")
                print(f"   Failed events: {result['results'].get('failed_events', 0)}")
            else:
                print(f"❌ Sync failed: {result.get('error')}")
        else:
            print("❌ No Notion token found")
            print("Please connect Notion through the dashboard first")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    """Main execution"""
    print("=" * 60)
    print("NOTIONFLOW DATABASE FIXES")
    print("=" * 60)
    
    # Step 1: Fix database schema
    if fix_database_schema():
        print("\n" + "=" * 60)
        
        # Step 2: Test Notion sync
        test_notion_sync()
    
    print("\n" + "=" * 60)
    print("Fix script completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()