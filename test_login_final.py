#!/usr/bin/env python3
"""
Final login test with the created account
"""
import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('/Users/johyeon-ung/Desktop/NotionFlow/.env')

def test_login_final():
    """Test login with the account we just created"""
    email = "ab40905045@gmail.com"
    password = "testpassword123"  # The password used in signup
    
    print(f"🔐 Testing login for: {email}")
    print(f"   Password length: {len(password)} chars")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_API_KEY')
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            print("✅ LOGIN SUCCESSFUL!")
            print(f"   User ID: {response.user.id}")
            print(f"   Email: {response.user.email}")
            print(f"   Email confirmed: {response.user.email_confirmed_at is not None}")
            print("\n🎉 The user can now login with these credentials:")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            return True
        else:
            print("❌ Login failed - no user returned")
            return False
            
    except Exception as e:
        print(f"❌ Login failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_login_final()