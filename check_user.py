#!/usr/bin/env python3
"""
Check if user exists in Supabase
"""
import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('/Users/johyeon-ung/Desktop/NotionFlow/.env')

def check_user_exists(email):
    """Check if user exists in Supabase Auth"""
    print(f"🔍 Checking if user exists: {email}")
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_API_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created")
        
        # Try to check users table
        try:
            result = supabase.table('user_api_keys').select('*').eq('user_email', email).execute()
            if result.data:
                print(f"✅ User found in user_api_keys table: {len(result.data)} records")
                for record in result.data:
                    print(f"   - ID: {record.get('id')}")
                    print(f"   - Email: {record.get('user_email')}")
                    print(f"   - Created: {record.get('created_at', 'Unknown')}")
            else:
                print("❌ User not found in user_api_keys table")
        except Exception as e:
            print(f"⚠️  Error checking user_api_keys: {e}")
        
        # Try auth.users if we have service role key  
        if service_key:
            try:
                admin_client = create_client(supabase_url, service_key)
                # Note: Admin operations require service role key
                print("ℹ️  Service role key available - could check auth.users table")
            except Exception as e:
                print(f"⚠️  Service role error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_signup(email, password):
    """Test signup functionality"""
    print(f"\n🆕 Testing signup for: {email}")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_API_KEY')
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            print("✅ Signup successful!")
            print(f"   User ID: {response.user.id}")
            print(f"   Email: {response.user.email}")
            print(f"   Email confirmed: {response.user.email_confirmed_at is not None}")
            
            if not response.user.email_confirmed_at:
                print("ℹ️  Email confirmation may be required")
            
            return True
        else:
            print("❌ Signup failed - no user returned")
            return False
            
    except Exception as e:
        print(f"❌ Signup failed: {str(e)}")
        return False

if __name__ == "__main__":
    email = "ab40905045@gmail.com"
    password = "testpassword123"  # 11 character test password
    
    # Check if user exists
    check_user_exists(email)
    
    # Try signup
    test_signup(email, password)