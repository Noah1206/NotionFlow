#!/usr/bin/env python3
"""
Normalize all user IDs in the database to dash-free format
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    exit(1)

# Create Supabase client with service key for admin access
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def normalize_user_ids():
    """Normalize all user IDs to remove dashes"""
    
    print("🔄 Starting user ID normalization...")
    print("Converting all user IDs from dash format to dash-free format")
    print("Example: 87875eda-6797-f839-f8c7-0aa90efb1352 → 87875eda6797f839f8c70aa90efb1352")
    
    # Tables that need updating
    tables_to_update = [
        ('users', 'id'),
        ('calendars', 'owner_id'),
        ('calendar_sync_configs', 'user_id'),
        ('oauth_tokens', 'user_id'),
        ('sync_events', 'user_id'),
        ('platform_coverage', 'user_id'),
        ('user_activities', 'user_id'),
        ('sync_jobs', 'user_id')
    ]
    
    # Track all user IDs that need updating
    users_with_dashes = set()
    
    # 1. First, find all users and check which have dashes
    print("\n📊 Finding users with dashes in IDs...")
    result = supabase.table('users').select('id').execute()
    
    if result.data:
        for user in result.data:
            if '-' in user['id']:
                users_with_dashes.add(user['id'])
        
        if users_with_dashes:
            print(f"Found {len(users_with_dashes)} users with dashes:")
            for user_id in users_with_dashes:
                print(f"  - {user_id}")
        else:
            print("No users found with dashes in their IDs")
            return
    else:
        print("No users found in database")
        return
    
    # 2. Create mapping of old IDs to new IDs
    id_mapping = {}
    for old_id in users_with_dashes:
        new_id = old_id.replace('-', '')
        id_mapping[old_id] = new_id
        print(f"\n📝 Will update: {old_id} → {new_id}")
    
    # 3. Check for conflicts (new IDs that already exist)
    print("\n🔍 Checking for conflicts...")
    conflicts = []
    for new_id in id_mapping.values():
        result = supabase.table('users').select('id').eq('id', new_id).execute()
        if result.data:
            conflicts.append(new_id)
    
    if conflicts:
        print("❌ Conflicts found! These dash-free IDs already exist:")
        for conflict_id in conflicts:
            print(f"  - {conflict_id}")
        print("Cannot proceed with normalization due to conflicts.")
        return
    
    print("✅ No conflicts found, proceeding with updates...")
    
    # 4. Update each table
    total_updates = 0
    
    for table_name, column_name in tables_to_update:
        print(f"\n📝 Updating {table_name}.{column_name}...")
        table_updates = 0
        
        for old_id, new_id in id_mapping.items():
            try:
                # Special handling for primary key (users table)
                if table_name == 'users' and column_name == 'id':
                    # First, we need to update all foreign keys, then update the primary key
                    # This is complex, so we'll use a different approach
                    print(f"  Updating primary key {old_id} → {new_id}")
                    
                    # Get the full user record
                    user_data = supabase.table('users').select('*').eq('id', old_id).execute()
                    if user_data.data:
                        user_record = user_data.data[0]
                        # Remove the id field as it will be set to new_id
                        del user_record['id']
                        
                        # Insert with new ID
                        result = supabase.table('users').upsert({
                            'id': new_id,
                            **user_record
                        }).execute()
                        
                        if result.data:
                            # Delete old record only after successful insert
                            supabase.table('users').delete().eq('id', old_id).execute()
                            table_updates += 1
                else:
                    # Update foreign key references
                    result = supabase.table(table_name).update({
                        column_name: new_id
                    }).eq(column_name, old_id).execute()
                    
                    if result.data:
                        table_updates += len(result.data)
                        
            except Exception as e:
                print(f"  ⚠️ Error updating {old_id}: {e}")
        
        print(f"  ✅ Updated {table_updates} records")
        total_updates += table_updates
    
    # 5. Verify the updates
    print("\n🔍 Verifying updates...")
    remaining_dashes = 0
    
    for table_name, column_name in tables_to_update:
        result = supabase.table(table_name).select(column_name).execute()
        count = 0
        if result.data:
            for record in result.data:
                if record.get(column_name) and '-' in str(record[column_name]):
                    count += 1
        
        if count > 0:
            print(f"  ⚠️ {table_name}: {count} records still have dashes")
            remaining_dashes += count
        else:
            print(f"  ✅ {table_name}: No dashes remaining")
    
    if remaining_dashes == 0:
        print(f"\n🎉 Success! Normalized {total_updates} records across all tables.")
    else:
        print(f"\n⚠️ Partial success: {total_updates} records updated, but {remaining_dashes} records still have dashes.")
    
    # 6. Show sample of normalized users
    print("\n📊 Sample of normalized users:")
    result = supabase.table('users').select('id, email').limit(5).execute()
    if result.data:
        for user in result.data:
            print(f"  - {user['id']}: {user.get('email', 'N/A')}")

if __name__ == "__main__":
    response = input("\n⚠️ This will modify all user IDs in the database. Continue? (yes/no): ")
    if response.lower() == 'yes':
        normalize_user_ids()
    else:
        print("❌ Operation cancelled")