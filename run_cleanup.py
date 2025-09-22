#!/usr/bin/env python3
"""
Clean up invalid user IDs and orphaned records in database
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    exit(1)

# Create Supabase client with service key for admin access
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def cleanup_database():
    """Clean up invalid user IDs and orphaned records"""
    
    print("🧹 Starting database cleanup...")
    
    # Test user IDs that should be removed
    test_user_ids = [
        '87875eda-6797-f839-f8c7-0aa90efb1352',  # With dashes
        '8c7153b7-ee46-4d62-80ef-85b896e4962c',
        '550e8400-e29b-41d4-a716-446655440000'
    ]
    
    # 1. Check which users actually exist
    print("\n📊 Checking users table...")
    for user_id in test_user_ids:
        normalized_id = user_id.replace('-', '')
        
        # Check with dashes
        result1 = supabase.table('users').select('id').eq('id', user_id).execute()
        # Check without dashes  
        result2 = supabase.table('users').select('id').eq('id', normalized_id).execute()
        
        if result1.data:
            print(f"  ✅ User {user_id} exists (with dashes)")
        elif result2.data:
            print(f"  ✅ User {normalized_id} exists (without dashes)")
        else:
            print(f"  ❌ User {user_id} does not exist")
    
    # 2. Clean up calendar_sync_configs
    print("\n🗑️ Cleaning calendar_sync_configs...")
    for user_id in test_user_ids:
        result = supabase.table('calendar_sync_configs').delete().eq('user_id', user_id).execute()
        if result.data:
            print(f"  Deleted {len(result.data)} records for {user_id}")
    
    # 3. Clean up oauth_tokens
    print("\n🗑️ Cleaning oauth_tokens...")
    for user_id in test_user_ids:
        result = supabase.table('oauth_tokens').delete().eq('user_id', user_id).execute()
        if result.data:
            print(f"  Deleted {len(result.data)} records for {user_id}")
    
    # 4. Clean up sync_events
    print("\n🗑️ Cleaning sync_events...")
    for user_id in test_user_ids:
        result = supabase.table('sync_events').delete().eq('user_id', user_id).execute()
        if result.data:
            print(f"  Deleted {len(result.data)} records for {user_id}")
    
    # 5. Clean up platform_coverage
    print("\n🗑️ Cleaning platform_coverage...")
    for user_id in test_user_ids:
        result = supabase.table('platform_coverage').delete().eq('user_id', user_id).execute()
        if result.data:
            print(f"  Deleted {len(result.data)} records for {user_id}")
    
    # 6. Verify cleanup
    print("\n✅ Verifying cleanup...")
    tables = ['calendar_sync_configs', 'oauth_tokens', 'sync_events', 'platform_coverage']
    
    for table in tables:
        orphaned_count = 0
        for user_id in test_user_ids:
            result = supabase.table(table).select('user_id').eq('user_id', user_id).execute()
            orphaned_count += len(result.data)
        
        if orphaned_count == 0:
            print(f"  ✅ {table}: No orphaned records")
        else:
            print(f"  ⚠️ {table}: {orphaned_count} orphaned records remain")
    
    print("\n🎉 Cleanup complete!")

if __name__ == "__main__":
    cleanup_database()