#!/usr/bin/env python3
"""
Fix user authentication - handle email confirmation
"""
import os
import sys
sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('/Users/johyeon-ung/Desktop/NotionFlow/.env')

def fix_user_auth():
    """Fix user authentication by confirming email or checking settings"""
    email = "ab40905045@gmail.com"
    
    print(f"🔧 Fixing authentication for: {email}")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_API_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not service_key:
        print("❌ Service role key not found - cannot admin operations")
        return False
    
    try:
        # Use admin client with service role key
        admin_client = create_client(supabase_url, service_key)
        print("✅ Admin client created with service role key")
        
        # Try to get user by email using admin API
        try:
            # Get user from auth.users (admin only)
            result = admin_client.auth.admin.list_users()
            
            user_found = None
            for user in result:
                if user.email == email:
                    user_found = user
                    break
            
            if user_found:
                print(f"✅ User found in auth.users:")
                print(f"   ID: {user_found.id}")
                print(f"   Email: {user_found.email}")
                print(f"   Email confirmed: {user_found.email_confirmed_at is not None}")
                print(f"   Created: {user_found.created_at}")
                
                # If email is not confirmed, try to confirm it
                if not user_found.email_confirmed_at:
                    print("🔄 Attempting to confirm email...")
                    try:
                        confirm_result = admin_client.auth.admin.update_user_by_id(
                            user_found.id,
                            {"email_confirm": True}
                        )
                        print("✅ Email confirmed successfully!")
                        
                        # Now try login
                        print("🔐 Testing login after email confirmation...")
                        regular_client = create_client(supabase_url, supabase_key)
                        login_response = regular_client.auth.sign_in_with_password({
                            "email": email,
                            "password": "testpassword123"
                        })
                        
                        if login_response.user:
                            print("✅ LOGIN SUCCESSFUL after email confirmation!")
                            return True
                        else:
                            print("❌ Login still failed after email confirmation")
                            
                    except Exception as confirm_error:
                        print(f"❌ Error confirming email: {confirm_error}")
                
            else:
                print("❌ User not found in auth.users")
                return False
                
        except Exception as e:
            print(f"❌ Error accessing admin API: {e}")
            
            # Try alternative approach - delete and recreate with no confirmation
            print("\n🔄 Trying alternative approach - recreate account with no email confirmation...")
            try:
                # Create new user with admin API (bypasses email confirmation)
                new_user_response = admin_client.auth.admin.create_user({
                    "email": email,
                    "password": "testpassword123",
                    "email_confirm": True  # Skip email confirmation
                })
                
                if new_user_response.user:
                    print("✅ User recreated with confirmed email!")
                    print(f"   User ID: {new_user_response.user.id}")
                    
                    # Test login
                    regular_client = create_client(supabase_url, supabase_key)
                    login_response = regular_client.auth.sign_in_with_password({
                        "email": email,
                        "password": "testpassword123"
                    })
                    
                    if login_response.user:
                        print("✅ LOGIN SUCCESSFUL with recreated account!")
                        return True
                    else:
                        print("❌ Login still failed with recreated account")
                        
            except Exception as create_error:
                print(f"❌ Error recreating user: {create_error}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if fix_user_auth():
        print("\n🎉 SUCCESS! User can now login with:")
        print("   Email: ab40905045@gmail.com")
        print("   Password: testpassword123")
    else:
        print("\n❌ FAILED to fix authentication")
        print("Manual steps needed:")
        print("1. Check Supabase dashboard auth settings")
        print("2. Disable email confirmation if enabled")
        print("3. Or provide different signup/login method")