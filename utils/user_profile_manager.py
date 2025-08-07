"""User Profile Management Functions"""

class UserProfileManager:
    @staticmethod
    def get_user_by_username(username):
        """Get user profile by username"""
        try:
            from utils.config import config
            client = config.supabase_client
            result = client.table('user_profiles').select('*').eq('username', username.lower()).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user profile by user_id"""
        try:
            from utils.config import config
            client = config.supabase_client
            result = client.table('user_profiles').select('*').eq('user_id', user_id).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting user by id: {e}")
            return None
    
    @staticmethod
    def create_user_profile(user_id, username, display_name=None):
        """Create new user profile"""
        try:
            from utils.config import config
            client = config.supabase_client
            profile_data = {
                'user_id': user_id,
                'username': username.lower(),
                'display_name': display_name or username
            }
            result = client.table('user_profiles').insert(profile_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return None
    
    @staticmethod
    def is_username_available(username):
        """Check if username is available with security validation"""
        try:
            from utils.auth_utils import security_validator
            
            # Security validation first
            is_valid, message = security_validator.validate_username_format(username)
            if not is_valid:
                return False, message
            
            # Sanitize input
            clean_username = security_validator.sanitize_input(username, max_length=20)
            if clean_username != username:
                return False, "사용자명에 허용되지 않는 문자가 포함되어 있습니다"
        except ImportError:
            # If auth_utils not available, skip validation
            pass
        
        try:
            from utils.config import config
            client = config.supabase_client
            result = client.table('user_profiles').select('username').eq('username', username.lower()).execute()
            if len(result.data) == 0:
                return True, "사용 가능한 사용자명입니다"
            else:
                return False, "이미 사용 중인 사용자명입니다"
        except Exception as e:
            print(f"Error checking username availability: {e}")
            return False, "사용자명 확인 중 오류가 발생했습니다"