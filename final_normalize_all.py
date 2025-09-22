#!/usr/bin/env python3
"""
Final normalization - Convert ALL user IDs to dash-free format
This will update ALL tables, no duplicates expected
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

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def final_normalize():
    """Convert ALL user IDs to dash-free format"""
    
    print("🚀 Starting FINAL normalization of user IDs...")
    print("This will convert ALL user IDs from UUID format to dash-free format")
    
    # Get all users with dashes
    result = supabase.table('users').select('*').execute()
    users_to_update = []
    
    if result.data:
        for user in result.data:
            if '-' in user['id']:
                users_to_update.append(user)
    
    if not users_to_update:
        print("✅ No users with dashes found. Database is already normalized.")
        return
    
    print(f"\n📊 Found {len(users_to_update)} users to update:")
    for user in users_to_update:
        new_id = user['id'].replace('-', '')
        print(f"  {user['id']} → {new_id}")
    
    response = input(f"\n⚠️ This will update {len(users_to_update)} users. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    # Update process
    print("\n🔧 Starting updates...")
    
    # For each user, create new record with dash-free ID and delete old one
    for user in users_to_update:
        old_id = user['id']
        new_id = old_id.replace('-', '')
        
        print(f"\n📝 Processing {old_id} → {new_id}")
        
        try:
            # 1. First update all foreign key references
            tables_to_update = [
                ('calendars', 'owner_id'),
                ('calendar_sync_configs', 'user_id'),
                ('oauth_tokens', 'user_id'),
                ('sync_events', 'user_id'),
                ('platform_coverage', 'user_id'),
                ('user_activities', 'user_id'),
                ('sync_jobs', 'user_id'),
                ('platform_connections', 'user_id')
            ]
            
            for table, column in tables_to_update:
                try:
                    result = supabase.table(table).update({
                        column: new_id
                    }).eq(column, old_id).execute()
                    
                    if result.data:
                        print(f"  ✅ Updated {len(result.data)} records in {table}")
                except Exception as e:
                    print(f"  ⚠️ {table}: {e}")
            
            # 2. Create new user record with dash-free ID
            user_data = user.copy()
            user_data['id'] = new_id
            
            # Insert new user record
            result = supabase.table('users').insert(user_data).execute()
            if result.data:
                print(f"  ✅ Created new user record with ID {new_id}")
                
                # 3. Delete old user record
                result = supabase.table('users').delete().eq('id', old_id).execute()
                if result.data:
                    print(f"  ✅ Deleted old user record with ID {old_id}")
                else:
                    print(f"  ⚠️ Could not delete old user record")
            else:
                print(f"  ❌ Failed to create new user record")
                
        except Exception as e:
            print(f"  ❌ Error processing user: {e}")
    
    # Verify the results
    print("\n🔍 Verifying normalization...")
    
    # Check for any remaining dashes
    result = supabase.table('users').select('id').execute()
    remaining_dashes = 0
    if result.data:
        for user in result.data:
            if '-' in user['id']:
                remaining_dashes += 1
    
    if remaining_dashes == 0:
        print("✅ SUCCESS! All user IDs have been normalized to dash-free format.")
    else:
        print(f"⚠️ {remaining_dashes} users still have dashes in their IDs.")
    
    # Show final state
    print("\n📊 Final database state:")
    result = supabase.table('users').select('id, email').limit(10).execute()
    if result.data:
        for user in result.data:
            print(f"  {user['id']}: {user.get('email', 'No email')}")

if __name__ == "__main__":
    final_normalize()