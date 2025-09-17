"""
Database Cleanup Script for NotionFlow
Removes unused tables and fixes schema issues
"""

import os
from supabase import create_client

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')

def cleanup_unused_tables():
    """Remove tables that are no longer needed based on screenshot"""
    
    # Tables to KEEP (from screenshot)
    keep_tables = {
        'calendar_events',
        'calendar_members',
        'calendar_share_tokens',
        'calendar_shares',
        'calendar_sync',
        'calendar_sync_configs',
        'calendar_tags',
        'calendars',
        'event_attendees',
        'event_sync_mapping',
        'event_tags',
        'friendships',
        'notification_preferences',
        'oauth_states',
        'oauth_tokens',
        'platform_connections',
        'platform_coverage',
        'platform_sync_summary',  # This is a view, not a table
        'sync_analytics',
        'sync_events',
        'sync_logs',
        'sync_status',
        'user_activity',
        'user_profiles',
        'user_subscriptions',
        'users'  # Auth table
    }
    
    # Tables that might exist but are NOT in screenshot (candidates for removal)
    potential_remove = [
        'sync_tracking',  # Old tracking table
        'api_keys',  # Old API key storage
        'calendar_connections',  # Redundant with calendar_sync_configs
        'notion_connections',  # Redundant with platform_connections
        'google_connections',  # Redundant with platform_connections
    ]
    
    print("=" * 60)
    print("DATABASE CLEANUP PLAN")
    print("=" * 60)
    print("\n✅ Tables to KEEP:")
    for table in sorted(keep_tables):
        print(f"  - {table}")
    
    print("\n❌ Tables to potentially REMOVE (if they exist):")
    for table in potential_remove:
        print(f"  - {table}")
    
    print("\n" + "=" * 60)
    print("⚠️  This is a dry run. Review the list above.")
    print("To actually delete tables, uncomment the SQL execution below.")
    print("=" * 60)
    
    # SQL to remove unused tables (COMMENTED OUT FOR SAFETY)
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    for table in potential_remove:
        try:
            # Check if table exists first
            result = supabase.rpc('exec_sql', {
                'sql': f'''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                );
                '''
            }).execute()
            
            if result.data and result.data[0]['exists']:
                print(f"🗑️  Dropping table: {table}")
                # DROP TABLE command
                # supabase.rpc('exec_sql', {
                #     'sql': f'DROP TABLE IF EXISTS {table} CASCADE;'
                # }).execute()
            else:
                print(f"ℹ️  Table {table} doesn't exist, skipping...")
                
        except Exception as e:
            print(f"❌ Error checking/dropping {table}: {e}")
    """

if __name__ == "__main__":
    print("Starting database cleanup analysis...")
    cleanup_unused_tables()
    print("\n✅ Analysis complete!")