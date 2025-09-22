#!/usr/bin/env python3
"""
Check and clean up duplicate users (with and without dashes)
"""

import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    exit(1)

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def check_duplicates():
    """Check for duplicate users and consolidate them"""
    
    print("🔍 Checking for duplicate users...")
    
    # Get all users
    result = supabase.table('users').select('*').execute()
    
    if not result.data:
        print("No users found")
        return
    
    # Group users by normalized ID (without dashes)
    user_groups = {}
    
    for user in result.data:
        user_id = user['id']
        normalized_id = user_id.replace('-', '')
        
        if normalized_id not in user_groups:
            user_groups[normalized_id] = []
        user_groups[normalized_id].append(user)
    
    # Find duplicates
    duplicates = {k: v for k, v in user_groups.items() if len(v) > 1}
    
    if not duplicates:
        print("✅ No duplicate users found")
        return
    
    print(f"\n⚠️ Found {len(duplicates)} sets of duplicate users:")
    
    for normalized_id, users in duplicates.items():
        print(f"\n📊 Normalized ID: {normalized_id}")
        for user in users:
            created_at = user.get('created_at', 'Unknown')
            email = user.get('email', 'No email')
            print(f"  - ID: {user['id']}")
            print(f"    Email: {email}")
            print(f"    Created: {created_at}")
            
            # Check related records
            check_related_records(user['id'])
    
    # Offer to consolidate
    print("\n" + "="*60)
    response = input("\nConsolidate duplicates? Keep dash-free version and delete dash version? (yes/no): ")
    
    if response.lower() == 'yes':
        consolidate_duplicates(duplicates)
    else:
        print("❌ Operation cancelled")

def check_related_records(user_id):
    """Check related records for a user ID"""
    tables = [
        'calendars',
        'calendar_sync_configs',
        'oauth_tokens',
        'sync_events'
    ]
    
    for table in tables:
        try:
            if table == 'calendars':
                result = supabase.table(table).select('id').eq('owner_id', user_id).execute()
            else:
                result = supabase.table(table).select('id').eq('user_id', user_id).execute()
            
            count = len(result.data) if result.data else 0
            if count > 0:
                print(f"      {table}: {count} records")
        except Exception as e:
            print(f"      {table}: Error checking - {e}")

def consolidate_duplicates(duplicates):
    """Consolidate duplicate users - keep dash-free, remove dashed"""
    
    print("\n🔧 Consolidating duplicates...")
    
    for normalized_id, users in duplicates.items():
        # Find dash-free and dashed versions
        dash_free_user = None
        dashed_user = None
        
        for user in users:
            if '-' in user['id']:
                dashed_user = user
            else:
                dash_free_user = user
        
        if not dash_free_user or not dashed_user:
            print(f"⚠️ Skipping {normalized_id}: Could not identify dash patterns")
            continue
        
        print(f"\n📝 Processing {normalized_id}...")
        print(f"  Keeping: {dash_free_user['id']} (dash-free)")
        print(f"  Removing: {dashed_user['id']} (with dashes)")
        
        try:
            # Update all foreign key references from dashed to dash-free
            tables_to_update = [
                ('calendars', 'owner_id'),
                ('calendar_sync_configs', 'user_id'),
                ('oauth_tokens', 'user_id'),
                ('sync_events', 'user_id'),
                ('platform_coverage', 'user_id'),
                ('user_activities', 'user_id'),
                ('sync_jobs', 'user_id')
            ]
            
            for table, column in tables_to_update:
                result = supabase.table(table).update({
                    column: dash_free_user['id']
                }).eq(column, dashed_user['id']).execute()
                
                if result.data:
                    print(f"    Updated {len(result.data)} records in {table}")
            
            # Delete the dashed user
            result = supabase.table('users').delete().eq('id', dashed_user['id']).execute()
            
            if result.data:
                print(f"  ✅ Deleted user {dashed_user['id']}")
            else:
                print(f"  ⚠️ Could not delete user {dashed_user['id']}")
                
        except Exception as e:
            print(f"  ❌ Error consolidating: {e}")
    
    print("\n🎉 Consolidation complete!")

if __name__ == "__main__":
    check_duplicates()