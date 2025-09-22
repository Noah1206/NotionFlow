#!/usr/bin/env python3
"""
Analyze current user ID formats in the database
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

def analyze_user_ids():
    """Analyze current state of user IDs"""
    
    print("📊 Analyzing User ID formats in database...\n")
    
    # Get all users
    result = supabase.table('users').select('id, email, created_at').execute()
    
    if not result.data:
        print("No users found")
        return
    
    users_with_dashes = []
    users_without_dashes = []
    
    for user in result.data:
        user_id = user['id']
        if '-' in user_id:
            users_with_dashes.append(user)
        else:
            users_without_dashes.append(user)
    
    print(f"📈 User ID Format Summary:")
    print(f"  Total users: {len(result.data)}")
    print(f"  With dashes (UUID format): {len(users_with_dashes)}")
    print(f"  Without dashes: {len(users_without_dashes)}")
    
    if users_with_dashes:
        print(f"\n👤 Users WITH dashes ({len(users_with_dashes)}):")
        for user in users_with_dashes[:10]:  # Show first 10
            email = user.get('email', 'No email')
            print(f"  - {user['id']}")
            print(f"    Email: {email}")
    
    if users_without_dashes:
        print(f"\n👤 Users WITHOUT dashes ({len(users_without_dashes)}):")
        for user in users_without_dashes[:10]:  # Show first 10
            email = user.get('email', 'No email')
            print(f"  - {user['id']}")
            print(f"    Email: {email}")
    
    # Check for potential matches between dashed and non-dashed
    print("\n🔍 Checking for potential duplicates (same ID, different format)...")
    
    # Create normalized mapping
    dashed_normalized = {u['id'].replace('-', ''): u for u in users_with_dashes}
    dashfree_ids = {u['id']: u for u in users_without_dashes}
    
    potential_duplicates = []
    for normalized_id, dashed_user in dashed_normalized.items():
        if normalized_id in dashfree_ids:
            potential_duplicates.append({
                'dashed': dashed_user,
                'dashfree': dashfree_ids[normalized_id]
            })
    
    if potential_duplicates:
        print(f"\n⚠️ Found {len(potential_duplicates)} potential duplicates:")
        for dup in potential_duplicates:
            print(f"\n  Dashed version: {dup['dashed']['id']}")
            print(f"    Email: {dup['dashed'].get('email', 'No email')}")
            print(f"  Dash-free version: {dup['dashfree']['id']}")
            print(f"    Email: {dup['dashfree'].get('email', 'No email')}")
    else:
        print("  ✅ No potential duplicates found")
    
    # Check related tables
    print("\n📋 Checking related tables for user ID formats...")
    
    tables_to_check = [
        ('calendars', 'owner_id'),
        ('calendar_sync_configs', 'user_id'),
        ('oauth_tokens', 'user_id'),
        ('sync_events', 'user_id')
    ]
    
    for table, column in tables_to_check:
        result = supabase.table(table).select(column).execute()
        if result.data:
            with_dashes = sum(1 for r in result.data if r.get(column) and '-' in str(r[column]))
            without_dashes = sum(1 for r in result.data if r.get(column) and '-' not in str(r[column]))
            print(f"\n  {table}:")
            print(f"    With dashes: {with_dashes}")
            print(f"    Without dashes: {without_dashes}")

if __name__ == "__main__":
    analyze_user_ids()