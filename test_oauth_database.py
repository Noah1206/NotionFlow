#!/usr/bin/env python3
"""
Test script to verify OAuth database integration is working correctly.
Run this script to test the OAuth state management with Supabase.
"""

import os
import sys
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Supabase setup
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_API_KEY must be set in environment variables")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_oauth_states_table():
    """Test OAuth states table operations"""
    print("\n🔍 Testing OAuth States Table...")
    
    try:
        # 1. Test insertion
        test_state = secrets.token_urlsafe(32)
        test_data = {
            'user_id': 'test_user_123',
            'provider': 'test_provider',
            'state': test_state,
            'code_verifier': 'test_verifier_' + secrets.token_urlsafe(16),
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
        print("  📝 Inserting test OAuth state...")
        insert_result = supabase.table('oauth_states').insert(test_data).execute()
        
        if insert_result.data:
            print("  ✅ Successfully inserted OAuth state")
            inserted_id = insert_result.data[0]['id']
        else:
            print("  ❌ Failed to insert OAuth state")
            return False
        
        # 2. Test retrieval
        print("  🔍 Retrieving OAuth state...")
        select_result = supabase.table('oauth_states').select('*').eq('state', test_state).single().execute()
        
        if select_result.data:
            print("  ✅ Successfully retrieved OAuth state")
            print(f"     State: {select_result.data['state'][:8]}...")
            print(f"     Provider: {select_result.data['provider']}")
            print(f"     Expires at: {select_result.data['expires_at']}")
        else:
            print("  ❌ Failed to retrieve OAuth state")
            return False
        
        # 3. Test deletion
        print("  🗑️  Deleting test OAuth state...")
        delete_result = supabase.table('oauth_states').delete().eq('id', inserted_id).execute()
        
        if delete_result.data:
            print("  ✅ Successfully deleted OAuth state")
        else:
            print("  ⚠️  Warning: Could not confirm deletion")
        
        # 4. Test expired state cleanup
        print("  🧹 Testing expired state cleanup...")
        
        # Insert an expired state
        expired_state = secrets.token_urlsafe(32)
        expired_data = {
            'user_id': 'test_user_expired',
            'provider': 'test_provider',
            'state': expired_state,
            'code_verifier': None,
            'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            'expires_at': (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }
        
        supabase.table('oauth_states').insert(expired_data).execute()
        print("     Inserted expired state for cleanup test")
        
        # Clean up expired states
        current_time = datetime.utcnow().isoformat()
        cleanup_result = supabase.table('oauth_states').delete().lt('expires_at', current_time).execute()
        
        if cleanup_result.data:
            print(f"  ✅ Cleaned up {len(cleanup_result.data)} expired state(s)")
        else:
            print("  ℹ️  No expired states to clean up")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing OAuth states table: {e}")
        return False

def test_table_structure():
    """Verify the OAuth states table structure"""
    print("\n🏗️  Verifying Table Structure...")
    
    try:
        # Try to select with all expected columns
        result = supabase.table('oauth_states').select(
            'id, user_id, provider, state, code_verifier, created_at, expires_at'
        ).limit(1).execute()
        
        print("  ✅ Table structure verified - all columns exist")
        
        # Check for indexes (this is informational only)
        print("  ℹ️  Expected indexes:")
        print("     - Primary key on 'id'")
        print("     - Unique constraint on 'state'")
        print("     - Unique constraint on (state, provider)")
        print("     - Index on 'state' for faster lookups")
        print("     - Index on (user_id, provider) for user queries")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error verifying table structure: {e}")
        print("     Please ensure the table was created with the correct schema")
        return False

def test_database_connection():
    """Test basic database connectivity"""
    print("\n🔌 Testing Database Connection...")
    
    try:
        # Try a simple count query
        result = supabase.table('oauth_states').select('id', count='exact').limit(1).execute()
        
        print("  ✅ Successfully connected to Supabase")
        
        if hasattr(result, 'count'):
            print(f"  ℹ️  Current OAuth states in table: {result.count}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to connect to database: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 OAuth Database Integration Test Suite")
    print("=" * 60)
    
    print(f"\n📍 Supabase URL: {SUPABASE_URL}")
    print(f"🔑 API Key: {'*' * 10}...{SUPABASE_KEY[-4:] if SUPABASE_KEY else 'Not set'}")
    
    # Run tests
    tests_passed = 0
    tests_total = 3
    
    if test_database_connection():
        tests_passed += 1
    
    if test_table_structure():
        tests_passed += 1
    
    if test_oauth_states_table():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    if tests_passed == tests_total:
        print(f"✅ All tests passed! ({tests_passed}/{tests_total})")
        print("\n🎉 OAuth database integration is working correctly!")
        print("\nNext steps:")
        print("  1. Test the OAuth flow in your application")
        print("  2. Monitor the /oauth/health endpoint")
        print("  3. Set up periodic cleanup via /oauth/cleanup")
    else:
        print(f"⚠️  Some tests failed ({tests_passed}/{tests_total} passed)")
        print("\nPlease check:")
        print("  1. Database connection settings")
        print("  2. Table creation SQL was executed")
        print("  3. Supabase permissions are correct")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()