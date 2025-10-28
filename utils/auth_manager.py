"""
🔐 Authentication & Session Manager
Real user authentication with Supabase integration
"""

import os
import jwt
import hashlib
import base64
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from flask import session, request, g
from supabase import create_client
from functools import wraps

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY', os.getenv('SUPABASE_ANON_KEY'))
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Check for required environment variables with detailed error messages
if not SUPABASE_URL:
    print("❌ SUPABASE_URL environment variable is missing!")
    print("Please set the following environment variables:")
    print("- SUPABASE_URL=https://your-project.supabase.co")
    print("- SUPABASE_API_KEY=your-anon-key-here")
    print("- SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here (optional)")
    
    # Try to load from .env file if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_API_KEY', os.getenv('SUPABASE_ANON_KEY'))
        SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if SUPABASE_URL and SUPABASE_KEY:
            print("✅ Loaded environment variables from .env file")
        else:
            print("⚠️ No Supabase credentials found, using mock mode")
            SUPABASE_URL = None
            SUPABASE_KEY = None
    except ImportError:
        print("💡 Consider installing python-dotenv: pip install python-dotenv")
        print("⚠️ Running without Supabase, using mock mode")
        SUPABASE_URL = None
        SUPABASE_KEY = None
    except Exception:
        print("⚠️ Environment loading failed, using mock mode")
        SUPABASE_URL = None
        SUPABASE_KEY = None

# Set mock mode if no credentials
MOCK_MODE = not (SUPABASE_URL and SUPABASE_KEY)
if MOCK_MODE:
    print("🚨 Running in MOCK MODE - authentication disabled")
    supabase_key = None
    supabase = None
else:
    print("✅ Supabase credentials found, initializing client")

# Initialize Supabase client with error handling
if not MOCK_MODE:
    # Use service key if available for admin operations, otherwise use anon key
    supabase_key = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_KEY
    
    try:
        supabase = create_client(SUPABASE_URL, supabase_key)
        print(f"✅ Supabase initialized successfully with {SUPABASE_URL}")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase: {e}")
        print("⚠️ Falling back to mock mode")
        MOCK_MODE = True
        supabase = None

class AuthManager:
    """Centralized authentication management"""
    
    @staticmethod
    def get_current_user_id() -> Optional[str]:
        """Get current authenticated user ID from various sources with UUID normalization"""
        # Mock mode fallback
        if MOCK_MODE:
            return 'mock_user_123'  # Always return a mock user in mock mode
        
        # Priority order: JWT token > session > development fallback
        
        # 1. Check JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_id = AuthManager._validate_jwt_token(token)
            if user_id:
                return AuthManager._normalize_uuid(user_id)
        
        # 2. Check Flask session
        user_info = session.get('user_info')
        if user_info:
            # Try different session formats for compatibility
            if isinstance(user_info, dict):
                user_id = user_info.get('id') or user_info.get('user_id')
                if user_id:
                    return AuthManager._normalize_uuid(user_id)
                # If no UUID found, convert email to UUID
                email = user_info.get('email')
                if email:
                    return AuthManager._email_to_uuid(email)
            return AuthManager._normalize_uuid(str(user_info))
        
        # 3. Check g.current_user (set by decorators)
        if hasattr(g, 'current_user') and g.current_user:
            if hasattr(g.current_user, 'id'):
                return AuthManager._normalize_uuid(g.current_user.id)
            return AuthManager._normalize_uuid(str(g.current_user))
        
        # 4. Development fallback - check if we're in dev mode
        if os.environ.get('FLASK_ENV') == 'development':
            # Look for any session data that indicates a user
            if session.get('authenticated') or session.get('user_id'):
                user_id = session.get('user_id', 'dev_user')
                return AuthManager._normalize_uuid(user_id)
        
        return None
    
    @staticmethod
    def _validate_jwt_token(token: str) -> Optional[str]:
        """Validate JWT token and extract user ID"""
        try:
            # For Supabase JWT tokens
            # Note: In production, you should verify the signature
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded.get('sub')  # Supabase user ID
        except:
            return None
    
    @staticmethod
    def _normalize_uuid(uuid_str: str) -> str:
        """UUID를 DB 저장 형식으로 정규화 (하이픈 없는 형식) - 통일된 형식 사용"""
        if not uuid_str:
            return None
            
        # 이메일인 경우 UUID로 변환
        if '@' in uuid_str:
            return AuthManager._email_to_uuid(uuid_str)
        
        # 하이픈 제거 후 길이 체크
        clean_uuid = uuid_str.replace('-', '').lower()
        
        # 32자리 16진수인지 확인
        if len(clean_uuid) == 32 and all(c in '0123456789abcdef' for c in clean_uuid):
            # DB 저장 형식으로 반환 (하이픈 없음)
            return clean_uuid
        
        # UUID가 아닌 경우 원본 반환
        return uuid_str
    
    @staticmethod 
    def _email_to_uuid(email: str) -> str:
        """이메일을 DB 저장 형식(하이픈 없음)으로 변환"""
        # 이메일을 해시화하여 하이픈 없는 형식으로 변환
        email_hash = hashlib.md5(email.encode()).hexdigest()
        return email_hash
    
    @staticmethod
    def require_auth(f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = AuthManager.get_current_user_id()
            if not user_id:
                from flask import jsonify
                return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
            
            # Store user in g for use in the request
            g.current_user_id = user_id
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict]:
        """Get user profile from database"""
        # Mock mode fallback
        if MOCK_MODE or not supabase:
            return {
                'user_id': user_id,
                'username': 'mockuser',
                'display_name': 'Mock User',
                'email': 'mock@example.com',
                'bio': 'Mock user profile for testing',
                'avatar_url': None,
                'is_public': True,
                'created_at': '2024-01-01T00:00:00Z'
            }
        
        try:
            result = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            if result.data and len(result.data) > 0:
                profile = result.data[0]
                
                # Extract birthdate from bio field if it exists
                if profile.get('bio') and 'birthdate:' in profile['bio']:
                    try:
                        # Parse birthdate from bio field (format: "birthdate:YYYY-MM-DD")
                        bio_parts = profile['bio'].split('birthdate:')
                        if len(bio_parts) > 1:
                            birthdate = bio_parts[1].strip()
                            profile['birthdate'] = birthdate
                            # Remove birthdate from bio for display
                            profile['bio'] = bio_parts[0].strip() if bio_parts[0].strip() else None
                    except Exception as e:
                        print(f"Error parsing birthdate from bio: {e}")
                
                # Fix avatar URL if it's a local path in production
                if profile.get('avatar_url'):
                    avatar_url = profile['avatar_url']
                    # Check if it's a local path that needs fixing
                    if avatar_url.startswith('/static/uploads/avatars/'):
                        # Extract filename from local path
                        filename = avatar_url.split('/')[-1]
                        # Check if we're in production and should use Supabase URL
                        import os
                        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT'):
                            # Generate Supabase Storage public URL
                            try:
                                public_url = supabase.storage.from_('avatars').get_public_url(filename)
                                if public_url:
                                    profile['avatar_url'] = public_url
                                    # Optionally update the database with the correct URL
                                    supabase.table('user_profiles').update({
                                        'avatar_url': public_url
                                    }).eq('user_id', user_id).execute()
                            except Exception as e:
                                print(f"Failed to fix avatar URL: {e}")
                
                return profile
            else:
                print(f"No user profile found for user_id: {user_id}")
                # 프로필이 없으면 기본 프로필 생성
                from flask import session
                user_info = session.get('user_info', {})
                email = user_info.get('email', '')
                AuthManager._create_user_profile(user_id, None, None, email)
                
                # 다시 조회해서 반환
                result = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
                if result.data and len(result.data) > 0:
                    profile = result.data[0]
                    
                    # Extract birthdate from bio field if it exists
                    if profile.get('bio') and 'birthdate:' in profile['bio']:
                        try:
                            bio_parts = profile['bio'].split('birthdate:')
                            if len(bio_parts) > 1:
                                birthdate = bio_parts[1].strip()
                                profile['birthdate'] = birthdate
                                # Remove birthdate from bio for display
                                profile['bio'] = bio_parts[0].strip() if bio_parts[0].strip() else None
                        except Exception as e:
                            print(f"Error parsing birthdate from bio: {e}")
                    
                    return profile
                return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Get user information by user ID"""
        # Mock mode fallback
        if MOCK_MODE or not supabase:
            return {
                'id': user_id,
                'name': 'Mock User',
                'email': 'mock@example.com',
                'avatar': '/static/images/default-avatar.png'
            }
        
        try:
            # Get user profile from user_profiles table
            result = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            if result.data and len(result.data) > 0:
                profile = result.data[0]
                return {
                    'id': profile.get('user_id'),
                    'name': profile.get('username') or profile.get('full_name') or 'Unknown User',
                    'email': profile.get('email', ''),
                    'avatar': profile.get('avatar_url', '/static/images/default-avatar.png')
                }
            
            # Fallback: try auth.users table if profile not found
            result = supabase.auth.admin.get_user_by_id(user_id)
            if result.user:
                user = result.user
                return {
                    'id': user.id,
                    'name': user.user_metadata.get('full_name') or user.email.split('@')[0],
                    'email': user.email,
                    'avatar': user.user_metadata.get('avatar_url', '/static/images/default-avatar.png')
                }
            
            return None
        except Exception as e:
            print(f"Error getting user by ID {user_id}: {e}")
            return None

    @staticmethod
    def update_user_profile(user_id: str, update_data: Dict) -> bool:
        """Update user profile in database"""
        # Mock mode fallback
        if MOCK_MODE or not supabase:
            print(f"Mock mode: Would update profile for user {user_id} with data {update_data}")
            return True
            
        try:
            # Update the profile
            result = supabase.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
            
            if result.data:
                print(f"Successfully updated profile for user {user_id}")
                return True
            else:
                print(f"Failed to update profile for user {user_id}")
                return False
                
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    @staticmethod
    def create_session(user_data: Dict) -> bool:
        """Create user session with cached user ID and unique dashboard URL"""
        try:
            user_id = user_data.get('id')
            email = user_data.get('email')
            
            # Cache user information
            session['user_info'] = {
                'id': user_id,
                'email': email,
                'username': user_data.get('username'),
                'display_name': user_data.get('display_name')
            }
            
            # Cache user ID for quick access
            session['cached_user_id'] = user_id
            
            # Generate and cache unique dashboard URLs
            if user_id:
                session['user_dashboard_url'] = AuthManager.get_user_dashboard_url(user_id)
                session['encrypted_user_id'] = AuthManager.encrypt_user_id(user_id)
            
            if email:
                session['email_dashboard_url'] = AuthManager.get_dashboard_url(email)
                session['encrypted_email'] = AuthManager.encrypt_email(email)
            
            session['authenticated'] = True
            session['login_time'] = datetime.now().isoformat()
            
            # Session created for user
            
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    @staticmethod
    def clear_session():
        """Clear user session"""
        session.clear()
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return AuthManager.get_current_user_id() is not None
    
    @staticmethod
    def get_cached_user_id() -> Optional[str]:
        """Get cached user ID from session"""
        return session.get('cached_user_id')
    
    @staticmethod
    def get_cached_dashboard_url() -> Optional[str]:
        """Get cached user dashboard URL from session"""
        return session.get('user_dashboard_url')
    
    @staticmethod
    def get_cached_encrypted_user_id() -> Optional[str]:
        """Get cached encrypted user ID from session"""
        return session.get('encrypted_user_id')
    
    @staticmethod
    def get_user_dashboard_url_from_session() -> Optional[str]:
        """Get user dashboard URL from session or generate if not cached"""
        cached_url = session.get('user_dashboard_url')
        if cached_url:
            return cached_url
        
        # Generate if not cached
        user_id = AuthManager.get_current_user_id()
        if user_id:
            url = AuthManager.get_user_dashboard_url(user_id)
            session['user_dashboard_url'] = url  # Cache it
            return url
        
        return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        """Get user by username from user_profiles table"""
        try:
            result = supabase.table('user_profiles').select('*').eq('username', username).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    @staticmethod
    def authenticate_with_supabase(login_identifier: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Authenticate user with Supabase using email or username"""
        try:
            # Check if login_identifier is email or username
            is_email = validate_email(login_identifier)
            
            if is_email:
                # Direct email login
                email = login_identifier
            else:
                # Username login - need to find email first
                user_profile = AuthManager.get_user_by_username(login_identifier)
                if not user_profile or not user_profile.get('email'):
                    return False, None, "Invalid username or password"
                email = user_profile['email']
            
            # Sign in with Supabase Auth using email
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                user_data = {
                    'id': auth_response.user.id,
                    'email': auth_response.user.email,
                    'username': auth_response.user.user_metadata.get('username'),
                    'display_name': auth_response.user.user_metadata.get('display_name')
                }
                
                # Check if user profile exists, create if not
                existing_profile = AuthManager.get_user_profile(auth_response.user.id)
                if not existing_profile:
                    # Creating missing user profile
                    AuthManager._create_user_profile(
                        auth_response.user.id, 
                        None, 
                        None, 
                        auth_response.user.email
                    )
                
                return True, user_data, auth_response.session.access_token
            else:
                return False, None, "Invalid credentials"
                
        except Exception as e:
            # Supabase authentication error
            return False, None, str(e)
    
    @staticmethod
    def register_with_supabase(email: str, password: str, username: str = None, display_name: str = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Register new user with Supabase"""
        try:
            # Prepare user metadata
            user_metadata = {}
            if username:
                user_metadata['username'] = username
            if display_name:
                user_metadata['display_name'] = display_name
            
            # Sign up with Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            
            if auth_response.user:
                user_data = {
                    'id': auth_response.user.id,
                    'email': auth_response.user.email,
                    'username': username,
                    'display_name': display_name
                }
                
                # Create user profile
                AuthManager._create_user_profile(auth_response.user.id, username, display_name, email)
                
                return True, user_data, auth_response.session.access_token if auth_response.session else None
            else:
                return False, None, "Registration failed"
                
        except Exception as e:
            return False, None, str(e)
    
    @staticmethod
    def encrypt_email(email: str) -> str:
        """Encrypt email to create unique dashboard URL path"""
        try:
            # Create a hash of the email for URL-safe identifier
            email_hash = hashlib.sha256(email.encode()).hexdigest()[:12]
            # Use base64 encoding for additional obfuscation
            encoded = base64.urlsafe_b64encode(email_hash.encode()).decode().rstrip('=')
            return encoded[:8]  # Use first 8 characters for clean URLs
        except Exception as e:
            print(f"Error encrypting email: {e}")
            # Fallback to simple hash
            return hashlib.md5(email.encode()).hexdigest()[:8]
    
    @staticmethod
    def encrypt_user_id(user_id: str) -> str:
        """Encrypt user ID to create unique dashboard URL path"""
        try:
            # Create a hash of the user ID for URL-safe identifier
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]
            # Use base64 encoding for additional obfuscation
            encoded = base64.urlsafe_b64encode(user_hash.encode()).decode().rstrip('=')
            return encoded[:10]  # Use first 10 characters for clean URLs
        except Exception as e:
            print(f"Error encrypting user ID: {e}")
            # Fallback to simple hash
            return hashlib.md5(user_id.encode()).hexdigest()[:10]
    
    @staticmethod
    def get_dashboard_url(email: str) -> str:
        """Generate dashboard URL - simplified"""
        return "/dashboard"
    
    @staticmethod
    def get_user_dashboard_url(user_id: str) -> str:
        """Generate dashboard URL - simplified version"""
        # 일단 간단하게 /dashboard로 통일
        return "/dashboard"
    
    @staticmethod
    def _create_user_profile(user_id: str, username: str = None, display_name: str = None, email: str = None):
        """Create user profile in database"""
        profile_data = {}
        try:
            # Check if profile already exists
            try:
                existing_profile = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
                if existing_profile.data:
                    print(f"User profile already exists for {user_id}")
                    return
            except Exception as check_error:
                print(f"Error checking existing profile: {check_error}")
            
            # Try using RPC function first (if SQL function exists)
            try:
                supabase.rpc('create_user_with_profile', {
                    'p_user_id': user_id,
                    'p_email': email,
                    'p_username': username,
                    'p_display_name': display_name
                }).execute()
                print(f"Created user and profile via RPC for {user_id}")
                return
            except Exception as rpc_error:
                print(f"RPC function not available, using direct insert: {rpc_error}")
            
            # Direct insert approach with better error handling
            # First, check if user exists in auth.users (Supabase Auth managed)
            # The users table might not be needed if using Supabase Auth
            try:
                # Try to create users record, but don't fail if it errors
                # (user might already exist in auth.users)
                user_data = {
                    'id': user_id,
                    'email': email or '',
                    'name': display_name or (email.split('@')[0] if email else f"User {user_id[:8]}"),
                    'created_at': datetime.now().isoformat()
                }
                supabase.table('users').insert(user_data).execute()
                print(f"Created user record for {user_id}")
            except Exception as user_error:
                # This is expected if user already exists or RLS blocks it
                print(f"User record creation skipped (may already exist): {user_error}")
            
            # Generate username from email if not provided
            if not username and email:
                username = email.split('@')[0][:20]  # Limit to 20 chars
            elif not username:
                username = f"user_{user_id[:8]}"
            
            # Create profile data
            profile_data = {
                'user_id': user_id,
                'username': username,
                'display_name': display_name or (email.split('@')[0] if email else f"User {user_id[:8]}"),
                'birthdate': '1990-01-01',  # Default birthdate to avoid initial-setup redirect
                'bio': 'New user account',
                'is_public': False,
                'avatar_url': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Try to insert profile
            try:
                supabase.table('user_profiles').insert(profile_data).execute()
                print(f"Created user profile for {user_id}")
            except Exception as profile_error:
                # This might fail due to RLS or if profile already exists
                print(f"Profile creation failed (may already exist): {profile_error}")
                # Don't raise - allow user to continue even without profile
                
        except Exception as e:
            # Log error but don't fail authentication
            print(f"Non-critical error in profile creation for {user_id}: {e}")
            if profile_data:
                print(f"Profile data attempted: {profile_data}")
            import traceback
            traceback.print_exc()

class SessionManager:
    """Session management utilities"""
    
    @staticmethod
    def extend_session():
        """Extend current session"""
        if AuthManager.is_authenticated():
            session['last_activity'] = datetime.now().isoformat()
            session.permanent = True
    
    @staticmethod
    def is_session_expired() -> bool:
        """Check if session is expired"""
        last_activity = session.get('last_activity')
        if not last_activity:
            return True
        
        try:
            last_activity_dt = datetime.fromisoformat(last_activity)
            return datetime.now() - last_activity_dt > timedelta(hours=24)
        except:
            return True
    
    @staticmethod
    def get_session_info() -> Dict:
        """Get current session information"""
        return {
            'authenticated': AuthManager.is_authenticated(),
            'user_id': AuthManager.get_current_user_id(),
            'login_time': session.get('login_time'),
            'last_activity': session.get('last_activity'),
            'expires_in': '24h' if AuthManager.is_authenticated() else None
        }
    
    @staticmethod
    def search_users(query: str, current_user_id: str, limit: int = 10) -> list:
        """Search users by name, email, or username"""
        try:
            query_lower = query.lower().strip()
            
            # Search in user_profiles table
            result = supabase.table('user_profiles').select(
                'user_id, username, display_name, email, avatar_url'
            ).or_(
                f'username.ilike.%{query_lower}%,'
                f'display_name.ilike.%{query_lower}%,'
                f'email.ilike.%{query_lower}%'
            ).neq('user_id', current_user_id).limit(limit).execute()
            
            users = []
            for user in result.data:
                # Check if already friends
                is_friend = AuthManager._check_friendship(current_user_id, user['user_id'])
                
                users.append({
                    'id': user['user_id'],
                    'name': user.get('display_name') or user.get('username', 'Unknown'),
                    'email': user.get('email', ''),
                    'username': user.get('username', ''),
                    'avatar': user.get('avatar_url'),
                    'is_friend': is_friend
                })
            
            return users
            
        except Exception as e:
            print(f"Error searching users: {e}")
            return []
    
    @staticmethod
    def _check_friendship(user1_id: str, user2_id: str) -> bool:
        """Check if two users are friends"""
        try:
            # Check friends table for existing friendship
            result = supabase.table('friendships').select('*').or_(
                f'and(user_id.eq.{user1_id},friend_id.eq.{user2_id}),'
                f'and(user_id.eq.{user2_id},friend_id.eq.{user1_id})'
            ).eq('status', 'accepted').execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"Error checking friendship: {e}")
            return False
    
    @staticmethod
    def send_friend_request(from_user_id: str, to_user_id: str) -> Tuple[bool, str]:
        """Send friend request"""
        try:
            # Check if friendship already exists (any status)
            existing_friendship = supabase.table('friendships').select('*').or_(
                f'and(user_id.eq.{from_user_id},friend_id.eq.{to_user_id}),'
                f'and(user_id.eq.{to_user_id},friend_id.eq.{from_user_id})'
            ).execute()
            
            if existing_friendship.data:
                status = existing_friendship.data[0]['status']
                if status == 'accepted':
                    return False, "You are already friends"
                elif status == 'pending':
                    return False, "Friend request already exists"
                elif status == 'blocked':
                    return False, "Cannot send friend request"
            
            # Create friend request (pending status in friendships table)
            request_data = {
                'user_id': from_user_id,
                'friend_id': to_user_id,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase.table('friendships').insert(request_data).execute()
            
            if result.data:
                return True, "Friend request sent successfully"
            else:
                return False, "Failed to send friend request"
                
        except Exception as e:
            print(f"Error sending friend request: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_friend_requests(user_id: str) -> list:
        """Get pending friend requests for a user"""
        try:
            result = supabase.table('friendships').select(
                '''
                *,
                requester:user_profiles!friendships_user_id_fkey(
                    user_id, username, display_name, email, avatar_url
                )
                '''
            ).eq('friend_id', user_id).eq('status', 'pending').execute()
            
            requests = []
            for req in result.data:
                from_user = req.get('requester')
                if from_user:
                    requests.append({
                        'request_id': req['id'],
                        'from_user': {
                            'id': from_user['user_id'],
                            'name': from_user.get('display_name') or from_user.get('username', 'Unknown'),
                            'email': from_user.get('email', ''),
                            'avatar': from_user.get('avatar_url')
                        },
                        'created_at': req['created_at']
                    })
            
            return requests
            
        except Exception as e:
            print(f"Error getting friend requests: {e}")
            return []
    
    @staticmethod
    def respond_to_friend_request(request_id: str, action: str, user_id: str) -> Tuple[bool, str]:
        """Accept or decline friend request"""
        try:
            if action not in ['accept', 'decline']:
                return False, "Invalid action"
            
            # Get the friendship record
            friendship_result = supabase.table('friendships').select('*').eq('id', request_id).eq('friend_id', user_id).execute()
            
            if not friendship_result.data:
                return False, "Friend request not found"
            
            friendship = friendship_result.data[0]
            
            if action == 'accept':
                # Update the existing friendship to accepted
                supabase.table('friendships').update({
                    'status': 'accepted',
                    'accepted_at': datetime.now().isoformat()
                }).eq('id', request_id).execute()
                
                # Create the reverse friendship for bidirectional relationship
                reverse_friendship = {
                    'user_id': user_id,
                    'friend_id': friendship['user_id'],
                    'status': 'accepted',
                    'created_at': datetime.now().isoformat(),
                    'accepted_at': datetime.now().isoformat()
                }
                
                supabase.table('friendships').insert(reverse_friendship).execute()
                
                return True, "Friend request accepted"
            else:
                # Delete the friendship request
                supabase.table('friendships').delete().eq('id', request_id).execute()
                
                return True, "Friend request declined"
                
        except Exception as e:
            print(f"Error responding to friend request: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_friends_list(user_id: str) -> list:
        """Get user's friends list"""
        # Mock mode fallback
        if MOCK_MODE or not supabase:
            return [
                {
                    'id': 'friend1',
                    'name': 'Mock Friend 1',
                    'email': 'friend1@example.com',
                    'avatar': None,
                    'friendship_date': '2024-01-01T00:00:00Z'
                },
                {
                    'id': 'friend2', 
                    'name': 'Mock Friend 2',
                    'email': 'friend2@example.com',
                    'avatar': None,
                    'friendship_date': '2024-01-01T00:00:00Z'
                }
            ]
        
        try:
            result = supabase.table('friendships').select(
                '''
                *,
                friend:user_profiles!friendships_friend_id_fkey(
                    user_id, username, display_name, email, avatar_url
                )
                '''
            ).eq('user_id', user_id).eq('status', 'accepted').execute()
            
            friends = []
            for friendship in result.data:
                friend = friendship.get('friend')
                if friend:
                    friends.append({
                        'id': friend['user_id'],
                        'name': friend.get('display_name') or friend.get('username', 'Unknown'),
                        'email': friend.get('email', ''),
                        'avatar': friend.get('avatar_url'),
                        'friendship_date': friendship['created_at']
                    })
            
            return friends
            
        except Exception as e:
            print(f"Error getting friends list: {e}")
            return []

# Convenience functions for backward compatibility
def get_current_user_id() -> Optional[str]:
    """Get current user ID - convenience function with UUID normalization"""
    return AuthManager.get_current_user_id()

def require_auth(f):
    """Authentication decorator - convenience function"""
    return AuthManager.require_auth(f)

def is_authenticated() -> bool:
    """Check authentication - convenience function"""
    return AuthManager.is_authenticated()