#!/usr/bin/env python3
"""
Reset password for existing user
"""
import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('/Users/johyeon-ung/Desktop/NotionFlow/.env')

def reset_user_password():
    """Reset password for existing user"""
    email = "ab40905045@gmail.com"
    new_password = "notionflow123"  # 13 chars - user mentioned 11 char password
    
    print(f"🔄 Resetting password for: {email}")
    print(f"   New password length: {len(new_password)} chars")
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not service_key:
        print("❌ Service role key not found")
        return False
    
    try:
        # Use admin client
        admin_client = create_client(supabase_url, service_key)
        print("✅ Admin client created")
        
        # Get user ID
        result = admin_client.auth.admin.list_users()
        user_id = None
        for user in result:
            if user.email == email:
                user_id = user.id
                print(f"✅ Found user ID: {user_id}")
                break
        
        if not user_id:
            print("❌ User not found")
            return False
        
        # Update password using admin API
        update_response = admin_client.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )
        
        print("✅ Password updated successfully!")
        
        # Test login with new password
        print("🔐 Testing login with new password...")
        regular_client = create_client(supabase_url, os.getenv('SUPABASE_API_KEY'))
        
        login_response = regular_client.auth.sign_in_with_password({
            "email": email,
            "password": new_password
        })
        
        if login_response.user:
            print("✅ LOGIN SUCCESSFUL!")
            print(f"   User ID: {login_response.user.id}")
            print(f"   Email: {login_response.user.email}")
            return True
        else:
            print("❌ Login still failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if reset_user_password():
        print("\n🎉 SUCCESS! User can now login with:")
        print("   Email: ab40905045@gmail.com")
        print("   Password: notionflow123")
        print("\n💡 Tell the user to use this password to login!")
    else:
        print("\n❌ Password reset failed")