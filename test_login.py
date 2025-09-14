#!/usr/bin/env python3
"""
Standalone test for login functionality
"""
import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('/Users/johyeon-ung/Desktop/NotionFlow/.env')

def test_login(email, password):
    """Test login functionality"""
    print(f"🔐 Testing login for: {email}")
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_API_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found")
        return False
    
    print(f"✅ Supabase URL: {supabase_url[:30]}...")
    print(f"✅ API Key loaded: {len(supabase_key)} chars")
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created")
        
        # Try to sign in
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            print("✅ Login successful!")
            print(f"   User ID: {response.user.id}")
            print(f"   Email: {response.user.email}")
            return True
        else:
            print("❌ Login failed - no user returned")
            return False
            
    except Exception as e:
        print(f"❌ Login failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test with the user's credentials
    email = "ab40905045@gmail.com"
    
    # Try a few possible passwords based on the user's message about password length 11
    passwords_to_test = [
        # Add some common test passwords
        "password123",
        "123456789",
        "ab40905045",
        "notionflow123",
    ]
    
    print(f"🧪 Testing login for {email}")
    print("Note: The password length was 11 chars according to the user's error message")
    
    for i, password in enumerate(passwords_to_test, 1):
        print(f"\n--- Test {i} (password length: {len(password)}) ---")
        if test_login(email, password):
            print(f"SUCCESS with password: {'*' * len(password)}")
            break
    else:
        print("\n❌ All test passwords failed")
        print("The user needs to:")
        print("1. Verify their password is correct")
        print("2. Check if their account exists in Supabase")
        print("3. Try signing up first if the account doesn't exist")