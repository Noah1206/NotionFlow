from flask import Blueprint, redirect, request, session, jsonify, url_for
import os
import secrets
import base64
import hashlib
import requests
import sys
import jwt
import time
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from supabase import create_client
from dotenv import load_dotenv

# Add parent directory to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_tracking_service import sync_tracker, EventType, ActivityType

# Load environment variables
load_dotenv()

oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')

# Supabase setup
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise Exception("SUPABASE_API_KEY environment variable is required")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# OAuth Configuration
OAUTH_CONFIG = {
    'google': {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'scope': 'https://www.googleapis.com/auth/calendar openid email profile',
        'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo'
    },
    'notion': {
        'client_id': os.environ.get('NOTION_CLIENT_ID'),
        'client_secret': os.environ.get('NOTION_CLIENT_SECRET'),
        'authorize_url': 'https://api.notion.com/v1/oauth/authorize',
        'token_url': 'https://api.notion.com/v1/oauth/token',
        'scope': '',
        'user_info_url': 'https://api.notion.com/v1/users/me'
    },
    'slack': {
        'client_id': os.environ.get('SLACK_CLIENT_ID'),
        'client_secret': os.environ.get('SLACK_CLIENT_SECRET'),
        'authorize_url': 'https://slack.com/oauth/v2/authorize',
        'token_url': 'https://slack.com/api/oauth.v2.access',
        'scope': 'channels:read,channels:write,chat:write,users:read,team:read',
        'user_scope': 'channels:read,channels:write,chat:write'
    },
    'outlook': {
        'client_id': os.environ.get('MICROSOFT_CLIENT_ID') or os.environ.get('OUTLOOK_CLIENT_ID'),
        'client_secret': os.environ.get('MICROSOFT_CLIENT_SECRET') or os.environ.get('OUTLOOK_CLIENT_SECRET'),
        'tenant_id': os.environ.get('MICROSOFT_TENANT_ID') or os.environ.get('OUTLOOK_TENANT_ID', 'common'),
        'authorize_url': 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize',
        'token_url': 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',
        'scope': 'https://graph.microsoft.com/Calendars.ReadWrite offline_access',
        'user_info_url': 'https://graph.microsoft.com/v1.0/me'
    },
    'apple': {
        'client_id': os.environ.get('APPLE_CLIENT_ID'),
        'client_secret': None,  # Apple uses private key JWT
        'team_id': os.environ.get('APPLE_TEAM_ID'),
        'key_id': os.environ.get('APPLE_KEY_ID'),
        'private_key': os.environ.get('APPLE_PRIVATE_KEY'),
        'authorize_url': 'https://appleid.apple.com/auth/authorize',
        'token_url': 'https://appleid.apple.com/auth/token',
        'scope': 'name email',
        'user_info_url': None  # Apple doesn't provide user info endpoint
    }
}

def generate_pkce_codes():
    """Generate PKCE code verifier and challenge for OAuth 2.0"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

def generate_apple_client_secret():
    """Generate Apple Sign In client secret using JWT"""
    try:
        config = OAUTH_CONFIG['apple']
        team_id = config.get('team_id')
        key_id = config.get('key_id')
        client_id = config.get('client_id')
        private_key = config.get('private_key')
        
        if not all([team_id, key_id, client_id, private_key]):
            print("Missing Apple OAuth configuration")
            return None
        
        # Clean private key format
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
        
        # JWT headers
        headers = {
            'kid': key_id,
            'alg': 'ES256'
        }
        
        # JWT payload
        now = int(time.time())
        payload = {
            'iss': team_id,
            'iat': now,
            'exp': now + 3600,  # 1 hour expiration
            'aud': 'https://appleid.apple.com',
            'sub': client_id
        }
        
        # Generate JWT
        client_secret = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
        return client_secret
        
    except Exception as e:
        print(f"Error generating Apple client secret: {e}")
        return None

def store_oauth_state(user_id, provider, state, code_verifier=None):
    """Store OAuth state in database or session for security"""
    try:
        # OAuth state 데이터 준비
        state_data = {
            'user_id': user_id or 'anonymous',
            'provider': provider,
            'state': state,
            'code_verifier': code_verifier,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }
        
        # 세션 저장 방식 사용 (RLS 정책 문제 우회)
        session[f'oauth_state_{state}'] = state_data
        session.permanent = True  # Make session persistent
        
        # 추가로 database에도 저장 시도 (fallback용)
        try:
            supabase.table('oauth_states').upsert(
                state_data,
                on_conflict='state'
            ).execute()
            print(f"OAuth state stored in both session and database for {provider}: {state[:8]}...")
        except Exception as db_error:
            print(f"Database storage failed, using session only: {db_error}")
        
        print(f"OAuth state stored for {provider}: {state[:8]}...")
        return True
            
    except Exception as e:
        print(f"Error storing OAuth state for {provider}: {e}")
        print(f"User ID: {user_id}, Provider: {provider}")
        return False

def verify_oauth_state(state, provider):
    """Verify OAuth state from database"""
    try:
        # First, clean up any expired states
        cleanup_expired_oauth_states()
        
        # Try to get state from database
        result = supabase.table('oauth_states').select('*').eq('state', state).eq('provider', provider).single().execute()
        
        if result.data:
            state_data = result.data
            # Check if state is not expired
            expires_at = datetime.fromisoformat(state_data['expires_at'])
            if datetime.utcnow() <= expires_at:
                # Delete the state after successful verification (one-time use)
                supabase.table('oauth_states').delete().eq('state', state).execute()
                print(f"OAuth state verified and cleaned from database for {provider}")
                return state_data
            else:
                # Clean up expired state
                supabase.table('oauth_states').delete().eq('state', state).execute()
                print(f"OAuth state expired for {provider}: {state[:8]}...")
                return None
        
        # Fallback: check session storage if database lookup fails
        session_key = f'oauth_state_{state}'
        if session_key in session:
            state_data = session[session_key]
            if state_data['provider'] == provider:
                # Check if not expired (30 minute timeout)
                created_at = datetime.fromisoformat(state_data['created_at'])
                if datetime.utcnow() - created_at < timedelta(minutes=30):
                    # Clean up after use
                    del session[session_key]
                    print(f"OAuth state verified from session fallback for {provider}")
                    return state_data
                else:
                    # Clean up expired session state
                    del session[session_key]
        
        print(f"OAuth state not found for {provider}: {state[:8]}...")
        return None
        
    except Exception as e:
        print(f"Error verifying OAuth state from database: {e}")
        
        # Fallback to session verification on database error
        try:
            session_key = f'oauth_state_{state}'
            if session_key in session:
                state_data = session[session_key]
                if state_data['provider'] == provider:
                    created_at = datetime.fromisoformat(state_data['created_at'])
                    if datetime.utcnow() - created_at < timedelta(minutes=30):
                        del session[session_key]
                        print(f"OAuth state verified from session after database error")
                        return state_data
                    else:
                        del session[session_key]
        except Exception as session_error:
            print(f"Session verification also failed: {session_error}")
        
        return None

def cleanup_expired_oauth_states():
    """Clean up expired OAuth states from database"""
    try:
        # Delete states older than 10 minutes
        current_time = datetime.utcnow().isoformat()
        result = supabase.table('oauth_states').delete().lt('expires_at', current_time).execute()
        if result.data:
            print(f"Cleaned up {len(result.data)} expired OAuth states")
    except Exception as e:
        print(f"Error cleaning up expired OAuth states: {e}")
        # Non-critical error, continue execution

def get_user_info_from_provider(platform, access_token):
    """Get user information from OAuth provider"""
    try:
        config = OAUTH_CONFIG[platform]
        headers = {'Authorization': f'Bearer {access_token}'}
        
        if platform == 'notion':
            headers['Notion-Version'] = '2022-06-28'
        
        user_info_url = config.get('user_info_url')
        if not user_info_url:
            return None
            
        response = requests.get(user_info_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting user info from {platform}: {e}")
        return None

def create_or_find_user_from_oauth(platform, user_info, token_data):
    """OAuth를 통해 사용자를 생성하거나 찾기 - 일반 로그인과 동일한 방식"""
    try:
        if not user_info:
            print(f"No user info available for {platform} OAuth")
            return None
            
        # 플랫폼별 이메일 추출
        email = get_platform_user_email(platform, user_info)
        name = get_platform_user_name(platform, user_info)
        
        if not email:
            print(f"No email found in {platform} user info")
            return None
        
        # Supabase Auth 테이블에서 사용자 찾기 (일반 로그인과 동일한 방식)
        try:
            # auth.users 테이블에서 확인
            existing_user = supabase.auth.get_user_by_email(email)
            if existing_user and existing_user.user:
                user_id = existing_user.user.id
                print(f"Found existing auth user for {email}: {user_id}")
                
                # Check if user profile exists, create if missing
                try:
                    profile_check = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
                    
                    if not profile_check.data:
                        print(f"No profile found for existing user {user_id}, creating one...")
                        # Generate username from email
                        username = email.split('@')[0]
                        
                        # Insert user profile with basic OAuth info
                        profile_data = {
                            'user_id': user_id,
                            'username': username,
                            'display_name': name or username,
                            'birthdate': '1990-01-01',  # Default birthdate to avoid initial-setup
                            'avatar_url': None,
                            'bio': f'OAuth user from {platform}',
                            'is_public': False,
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        
                        supabase.table('user_profiles').insert(profile_data).execute()
                        print(f"Created missing profile for existing OAuth user: {user_id}")
                        
                except Exception as profile_check_e:
                    print(f"Warning: Could not check/create profile for existing user: {profile_check_e}")
                
                return user_id
        except Exception as auth_e:
            print(f"Error checking auth user: {auth_e}")
        
        # 기존 사용자가 없으면 새로 생성 (Supabase Auth 사용)
        try:
            # 임시 비밀번호로 사용자 생성 (OAuth이므로 비밀번호는 사용되지 않음)
            import secrets
            temp_password = secrets.token_urlsafe(32)
            
            # Supabase Auth로 사용자 생성
            signup_result = supabase.auth.sign_up({
                "email": email, 
                "password": temp_password,
                "options": {
                    "data": {
                        "display_name": name,
                        "auth_provider": platform,
                        "oauth_signup": True
                    }
                }
            })
            
            if signup_result.user:
                user_id = signup_result.user.id
                print(f"Created new OAuth user for {email}: {user_id}")
                
                # Create user profile to avoid initial-setup redirect
                try:
                    # Generate username from email
                    username = email.split('@')[0]
                    
                    # Insert user profile with basic OAuth info
                    profile_data = {
                        'user_id': user_id,
                        'username': username,
                        'display_name': name or username,
                        'birthdate': '1990-01-01',  # Default birthdate to avoid initial-setup
                        'avatar_url': None,
                        'bio': f'OAuth user from {platform}',
                        'is_public': False,
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    
                    profile_result = supabase.table('user_profiles').insert(profile_data).execute()
                    print(f"Created user profile for OAuth user: {user_id}")
                    
                except Exception as profile_e:
                    print(f"Warning: Could not create user profile for OAuth user: {profile_e}")
                    # Continue without profile - user can complete setup later
                
                return user_id
            else:
                print(f"Failed to create OAuth user for {email}")
                return None
                
        except Exception as signup_e:
            print(f"Error creating OAuth user: {signup_e}")
            return None
                
    except Exception as e:
        print(f"Error in OAuth user creation/finding: {e}")
        return None

def store_platform_registration(user_id, platform, token_data, user_info=None):
    """Store platform registration in registered_platforms table"""
    try:
        # Get user info if not provided
        if not user_info and token_data.get('access_token'):
            user_info = get_user_info_from_provider(platform, token_data['access_token'])
        
        # Calculate token expiration
        expires_at = None
        if token_data.get('expires_in'):
            expires_at = (datetime.utcnow() + timedelta(seconds=int(token_data['expires_in']))).isoformat()
        
        # Prepare registration data
        registration_data = {
            'user_id': user_id,
            'platform': platform,
            'platform_name': platform.title(),
            'encrypted_credentials': json.dumps({
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'scope': token_data.get('scope'),
                'expires_at': expires_at
            }),
            'platform_user_id': get_platform_user_id(platform, user_info) if user_info else None,
            'platform_user_email': get_platform_user_email(platform, user_info) if user_info else None,
            'platform_user_name': get_platform_user_name(platform, user_info) if user_info else None,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at
        }
        
        # Upsert registration
        result = supabase.table('registered_platforms').upsert(
            registration_data,
            on_conflict='user_id,platform'
        ).execute()
        
        return bool(result.data)
    except Exception as e:
        print(f"Error storing platform registration: {e}")
        return False

def get_platform_user_id(platform, user_info):
    """Extract user ID from platform-specific user info"""
    if not user_info:
        return None
    if platform == 'google':
        return user_info.get('id')
    elif platform == 'notion':
        return user_info.get('id')
    elif platform == 'slack':
        return user_info.get('authed_user', {}).get('id')
    elif platform == 'outlook':
        return user_info.get('id')
    elif platform == 'apple':
        return user_info.get('sub')  # Apple uses 'sub' field
    return None

def get_platform_user_email(platform, user_info):
    """Extract user email from platform-specific user info"""
    if not user_info:
        return None
    if platform == 'google':
        return user_info.get('email')
    elif platform == 'notion':
        person = user_info.get('person', {})
        return person.get('email') if person else user_info.get('email')
    elif platform == 'slack':
        return user_info.get('authed_user', {}).get('email')
    elif platform == 'outlook':
        return user_info.get('mail') or user_info.get('userPrincipalName')
    elif platform == 'apple':
        return user_info.get('email')
    return None

def get_platform_user_name(platform, user_info):
    """Extract user name from platform-specific user info"""
    if not user_info:
        return None
    if platform == 'google':
        return user_info.get('name')
    elif platform == 'notion':
        return user_info.get('name')
    elif platform == 'slack':
        return user_info.get('authed_user', {}).get('name')
    elif platform == 'outlook':
        return user_info.get('displayName')
    elif platform == 'apple':
        # Apple provides name in a different structure
        name_obj = user_info.get('name', {})
        if isinstance(name_obj, dict):
            first_name = name_obj.get('firstName', '')
            last_name = name_obj.get('lastName', '')
            return f"{first_name} {last_name}".strip() if first_name or last_name else None
        return None
    return None

@oauth_bp.route('/<platform>/authorize')
def generic_oauth_authorize(platform):
    """Generic OAuth authorization for supported platforms"""
    if platform not in OAUTH_CONFIG:
        print(f"Unsupported platform requested: {platform}")
        return jsonify({'error': f'Unsupported platform: {platform}'}), 400
    
    # OAuth는 자체적으로 인증 수단이므로 사전 로그인을 요구하지 않음
    user_id = session.get('user_id')
    if not user_id:
        print(f"OAuth authorization initiated without existing session for {platform}")
        # OAuth 플로우를 계속 진행 - 콜백에서 사용자를 생성/로그인 처리
    
    config = OAUTH_CONFIG[platform]
    
    # Check if OAuth is properly configured (skip for Apple which uses JWT)
    if platform != 'apple':
        if not config.get('client_id') or not config.get('client_secret'):
            print(f"OAuth not configured for {platform}")
            print(f"Client ID: {config.get('client_id')[:10]}..." if config.get('client_id') else "Missing")
            print(f"Client Secret: {'Set' if config.get('client_secret') else 'Missing'}")
            error_msg = f'OAuth not configured for {platform}. Client ID: {"Set" if config.get("client_id") else "Missing"}, Secret: {"Set" if config.get("client_secret") else "Missing"}'
            return jsonify({'error': error_msg}), 500
    
    state = secrets.token_urlsafe(32)
    
    # Generate PKCE for platforms that support it
    code_verifier = None
    code_challenge = None
    if platform in ['google', 'notion', 'apple', 'outlook']:
        code_verifier, code_challenge = generate_pkce_codes()
        success = store_oauth_state(user_id, platform, state, code_verifier)
    else:
        success = store_oauth_state(user_id, platform, state)
    
    if not success:
        print(f"Failed to store OAuth state for {platform}")
        return jsonify({'error': 'Failed to initiate OAuth flow - Database connection issue'}), 500
    
    # Build authorization parameters
    # Railway 환경에서는 명시적으로 redirect_uri 설정
    base_url = os.getenv('BASE_URL')
    if base_url:
        redirect_uri = f"{base_url}/oauth/{platform}/callback"
    else:
        redirect_uri = url_for('oauth.generic_oauth_callback', platform=platform, _external=True)
        # Production 환경에서 HTTP로 생성되면 HTTPS로 변경
        if redirect_uri.startswith('http://') and os.getenv('FLASK_ENV') == 'production':
            redirect_uri = redirect_uri.replace('http://', 'https://', 1)
    
    params = {
        'client_id': config['client_id'],
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'state': state,
        'scope': config['scope']
    }
    
    print(f"[OAUTH DEBUG] {platform} redirect_uri: {redirect_uri}")
    
    # Platform-specific parameters
    if platform == 'google':
        params['access_type'] = 'offline'
        params['prompt'] = 'consent'
        if code_verifier:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'
    elif platform == 'notion':
        params['response_type'] = 'code'
        # Notion doesn't use PKCE in practice, but we'll include it
    elif platform == 'slack':
        params['user_scope'] = config.get('user_scope', '')
    elif platform == 'outlook':
        auth_url = config['authorize_url'].format(tenant=config['tenant_id'])
        params['response_mode'] = 'query'
        if code_verifier:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'
    elif platform == 'apple':
        params['response_mode'] = 'form_post'
        params['response_type'] = 'code id_token'
        if code_verifier:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'
    
    # Build final URL
    if platform == 'outlook':
        auth_url = config['authorize_url'].format(tenant=config['tenant_id'])
    else:
        auth_url = config['authorize_url']
    
    final_url = f"{auth_url}?{urlencode(params)}"
    
    # Return popup-friendly HTML
    popup_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connect {platform.title()}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: #f9fafb;
                color: #374151;
            }}
            .loading {{
                text-align: center;
                max-width: 400px;
                padding: 40px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .spinner {{
                width: 40px;
                height: 40px;
                border: 3px solid #e5e7eb;
                border-top: 3px solid #3b82f6;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .platform-name {{
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 8px;
                color: #111827;
            }}
            .redirect-info {{
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            .manual-link {{
                display: inline-block;
                padding: 10px 20px;
                background: #3b82f6;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 500;
                transition: background 0.2s;
            }}
            .manual-link:hover {{
                background: #2563eb;
            }}
        </style>
        <script>
            // Redirect to OAuth provider
            setTimeout(function() {{
                window.location.href = '{final_url}';
            }}, 1000);
        </script>
    </head>
    <body>
        <div class="loading">
            <div class="spinner"></div>
            <div class="platform-name">Connecting to {platform.title()}</div>
            <div class="redirect-info">Redirecting to {platform.title()} for authorization...</div>
            <a href="{final_url}" class="manual-link">Continue manually if not redirected</a>
        </div>
    </body>
    </html>
    """
    return popup_html

@oauth_bp.route('/<platform>/callback')
def generic_oauth_callback(platform):
    """Generic OAuth callback handler"""
    if platform not in OAUTH_CONFIG:
        return handle_callback_error('Unsupported platform', platform)
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return handle_callback_error(f'OAuth error: {error}', platform)
    
    if not code or not state:
        return handle_callback_error('Missing authorization code or state', platform)
    
    # Verify state
    state_data = verify_oauth_state(state, platform)
    if not state_data:
        return handle_callback_error('Invalid or expired state', platform)
    
    try:
        # Exchange code for tokens
        token_data = exchange_code_for_tokens(platform, code, state_data)
        if not token_data:
            return handle_callback_error('Failed to exchange authorization code for tokens', platform)
        
        # Get user info
        user_info = None
        if platform == 'apple':
            # Apple provides user info in ID token
            id_token = token_data.get('id_token')
            if id_token:
                try:
                    # Decode JWT (Apple ID token is signed, but we can extract payload for basic info)
                    # Note: In production, you should verify the signature
                    import base64
                    payload = id_token.split('.')[1]
                    # Add padding if needed
                    payload += '=' * (4 - len(payload) % 4)
                    decoded = base64.urlsafe_b64decode(payload)
                    user_info = json.loads(decoded.decode('utf-8'))
                except Exception as e:
                    print(f"Error decoding Apple ID token: {e}")
                    user_info = {'sub': 'apple_user', 'email': 'unknown@apple.com'}
        elif token_data.get('access_token'):
            user_info = get_user_info_from_provider(platform, token_data['access_token'])
        
        # 사용자 생성 또는 로그인 처리
        actual_user_id = state_data.get('user_id')
        if actual_user_id == 'anonymous' or not actual_user_id:
            # OAuth를 통해 새 사용자 생성 또는 기존 사용자 찾기
            actual_user_id = create_or_find_user_from_oauth(platform, user_info, token_data)
            if not actual_user_id:
                return handle_callback_error('Failed to create or find user account')
            
            # 일반 로그인과 동일한 세션 생성 방식
            user_email = get_platform_user_email(platform, user_info)
            user_name = get_platform_user_name(platform, user_info)
            
            # 세션 데이터 구조를 일반 로그인과 동일하게 설정
            session['user_id'] = actual_user_id
            session['user_info'] = {
                'id': actual_user_id,
                'email': user_email,
                'username': None,  # OAuth에서는 username이 없을 수 있음
                'display_name': user_name
            }
            session['authenticated'] = True
            session.permanent = True
            
            # AuthManager와 SessionManager 사용 (일반 로그인과 동일)
            try:
                from utils.auth_manager import AuthManager, SessionManager
                # 가상 user_data 생성
                oauth_user_data = {
                    'id': actual_user_id,
                    'email': user_email,
                    'username': None,
                    'display_name': user_name
                }
                AuthManager.create_session(oauth_user_data)
                SessionManager.extend_session()
                print(f"OAuth Session created for user: {actual_user_id}")
            except Exception as session_e:
                print(f"Error creating OAuth session with AuthManager: {session_e}")
                # 기본 세션은 이미 생성되었으므로 계속 진행
        
        # Store platform connection and OAuth tokens
        try:
            from utils.config import config
            from utils.uuid_helper import normalize_uuid, ensure_auth_user_exists
            
            # UUID 정규화
            normalized_user_id = normalize_uuid(actual_user_id)
            if not normalized_user_id:
                return handle_callback_error('Invalid user ID format', platform)
            
            # auth.users에 사용자 존재 확인 및 생성
            user_email = get_platform_user_email(platform, user_info)
            user_name = get_platform_user_name(platform, user_info)
            ensure_auth_user_exists(normalized_user_id, user_email, user_name)
            
            # 서비스 역할 클라이언트 사용 (외래키 문제 해결됨)
            supabase = config.supabase_admin
            
            if supabase:
                # 1. Store OAuth tokens in oauth_tokens table
                if token_data.get('access_token'):
                    oauth_token_data = {
                        'user_id': normalized_user_id,
                        'platform': platform,
                        'access_token': token_data.get('access_token'),
                        'refresh_token': token_data.get('refresh_token'),
                        'token_type': token_data.get('token_type', 'Bearer'),
                        'scope': token_data.get('scope', ''),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # Calculate token expiration if provided
                    if token_data.get('expires_in'):
                        from datetime import timedelta
                        expires_at = datetime.now() + timedelta(seconds=int(token_data['expires_in']))
                        oauth_token_data['expires_at'] = expires_at.isoformat()
                    
                    # Use admin/service role client to bypass RLS policies for OAuth token storage
                    service_supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else supabase
                    
                    # 🔧 NEW APPROACH: Store tokens in calendar_sync_configs instead
                    # This table doesn't have foreign key constraints and works for all users
                    try:
                        # Check if config already exists
                        existing_config = supabase.table('calendar_sync_configs').select('*').eq('user_id', normalized_user_id).eq('platform', platform).execute()
                        
                        # Prepare credentials data
                        credentials_data = {
                            'access_token': token_data['access_token'],
                            'refresh_token': token_data.get('refresh_token'),
                            'expires_at': oauth_token_data.get('expires_at'),
                            'token_type': token_data.get('token_type', 'Bearer'),
                            'scope': token_data.get('scope'),
                            'stored_at': datetime.now().isoformat()
                        }
                        
                        if existing_config.data:
                            # Update existing config with new token (only use existing columns)
                            update_data = {
                                'credentials': credentials_data,
                                'is_enabled': True,
                                'last_sync_at': datetime.now().isoformat(),
                                'updated_at': datetime.now().isoformat()
                            }
                            supabase.table('calendar_sync_configs').update(update_data).eq('user_id', normalized_user_id).eq('platform', platform).execute()
                            print(f"✅ Updated {platform} token in calendar_sync_configs for user {normalized_user_id}")
                        else:
                            # Create new config with token (only use existing columns)
                            new_config = {
                                'user_id': normalized_user_id,
                                'platform': platform,
                                'credentials': credentials_data,
                                'is_enabled': True,
                                'sync_frequency_minutes': 15,
                                'last_sync_at': datetime.now().isoformat(),
                                'created_at': datetime.now().isoformat(),
                                'updated_at': datetime.now().isoformat()
                            }
                            supabase.table('calendar_sync_configs').insert(new_config).execute()
                            print(f"✅ Created {platform} token in calendar_sync_configs for user {normalized_user_id}")
                            
                    except Exception as token_error:
                        print(f"⚠️ Could not store token in calendar_sync_configs: {token_error}")
                        # Store token in session as final fallback
                        if not session.get('platform_tokens'):
                            session['platform_tokens'] = {}
                        session['platform_tokens'][platform] = {
                            'access_token': token_data['access_token'],
                            'refresh_token': token_data.get('refresh_token'),
                            'expires_at': oauth_token_data.get('expires_at'),
                            'stored_at': datetime.now().isoformat()
                        }
                        print(f"💾 Stored {platform} token in session as final fallback")
                
                # 2. Store platform connection status (without tokens)
                platform_connection_data = {
                    'user_id': normalized_user_id,
                    'platform': platform,
                    'is_connected': True,
                    'connection_status': 'active',
                    'last_sync_at': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat()
                }
                
                # Calculate token expiration if provided  
                if token_data.get('expires_in'):
                    from datetime import timedelta
                    expires_at = datetime.now() + timedelta(seconds=int(token_data['expires_in']))
                    platform_connection_data['token_expires_at'] = expires_at.isoformat()
                
                # Check if platform connection already exists
                existing_result = supabase.table('platform_connections').select('*').eq('user_id', normalized_user_id).eq('platform', platform).execute()
                
                if existing_result.data:
                    # Update existing connection
                    del platform_connection_data['created_at']  # Don't update created_at
                    supabase.table('platform_connections').update(platform_connection_data).eq('user_id', normalized_user_id).eq('platform', platform).execute()
                    print(f"✅ Updated existing {platform} platform connection for user {normalized_user_id}")
                else:
                    # Create new connection - RLS 정책 우회를 위해 서비스 역할 사용
                    try:
                        supabase.table('platform_connections').insert(platform_connection_data).execute()
                        print(f"✅ Created new {platform} platform connection for user {normalized_user_id}")
                    except Exception as rls_error:
                        # RLS 정책 오류 시 서비스 역할로 재시도
                        print(f"⚠️ RLS policy blocked, retrying with service role: {rls_error}")
                        if config.supabase_admin:
                            config.supabase_admin.table('platform_connections').insert(platform_connection_data).execute()
                            print(f"✅ Created new {platform} platform connection with admin client")
                    
        except Exception as platform_store_error:
            print(f"Failed to store platform connection/tokens: {platform_store_error}")
            import traceback
            traceback.print_exc()
            # Continue with OAuth flow even if platform storage fails
        
        # Track the connection event
        sync_tracker.track_sync_event(
            user_id=actual_user_id,
            event_type=EventType.PLATFORM_CONNECTED,
            platform=platform,
            status='success',
            metadata={
                'user_email': get_platform_user_email(platform, user_info),
                'user_name': get_platform_user_name(platform, user_info),
                'connection_method': 'oauth'
            }
        )
        
        # Clean up OAuth state
        supabase.table('oauth_states').delete().eq('state', state).execute()
        
        return handle_callback_success(platform, user_info)
        
    except Exception as e:
        print(f"OAuth callback error for {platform}: {e}")
        return handle_callback_error(f'OAuth processing failed: {str(e)}')

def exchange_code_for_tokens(platform, code, state_data):
    """Exchange authorization code for access tokens"""
    config = OAUTH_CONFIG[platform]
    
    # Railway 환경에서는 명시적으로 redirect_uri 설정 (authorize와 동일해야 함)
    base_url = os.getenv('BASE_URL')
    if base_url:
        redirect_uri = f"{base_url}/oauth/{platform}/callback"
    else:
        redirect_uri = url_for('oauth.generic_oauth_callback', platform=platform, _external=True)
        # Production 환경에서 HTTP로 생성되면 HTTPS로 변경
        if redirect_uri.startswith('http://') and os.getenv('FLASK_ENV') == 'production':
            redirect_uri = redirect_uri.replace('http://', 'https://', 1)
    
    # Prepare token request data
    token_data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    
    print(f"[OAUTH DEBUG] Token exchange redirect_uri: {redirect_uri}")
    
    # Platform-specific modifications
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    if platform == 'google':
        # Google supports PKCE
        if state_data.get('code_verifier'):
            token_data['code_verifier'] = state_data['code_verifier']
    elif platform == 'notion':
        # Notion uses JSON format and requires specific headers
        headers = {
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        # Notion doesn't use PKCE and has different token request format
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        # Add basic auth for Notion (client_id:client_secret)
        import base64
        credentials = f"{config['client_id']}:{config['client_secret']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers['Authorization'] = f'Basic {encoded_credentials}'
    elif platform == 'outlook':
        # Outlook with PKCE
        token_url = config['token_url'].format(tenant=config['tenant_id'])
        if state_data.get('code_verifier'):
            token_data['code_verifier'] = state_data['code_verifier']
        config = {**config, 'token_url': token_url}
    elif platform == 'apple':
        # Apple uses client secret JWT
        client_secret = generate_apple_client_secret()
        if not client_secret:
            return None
        token_data['client_secret'] = client_secret
        if state_data.get('code_verifier'):
            token_data['code_verifier'] = state_data['code_verifier']
    
    # Make token request
    if platform == 'notion':
        # Notion expects JSON data
        response = requests.post(config['token_url'], json=token_data, headers=headers)
        print(f"[NOTION DEBUG] Token request - JSON: {token_data}")
        print(f"[NOTION DEBUG] Headers: {headers}")
    else:
        # Other platforms expect form data  
        response = requests.post(config['token_url'], data=token_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Token exchange failed for {platform}: {response.status_code}")
        print(f"Request URL: {config['token_url']}")
        print(f"Request Headers: {headers}")
        if platform == 'notion':
            print(f"Request Data (JSON): {token_data}")
        else:
            print(f"Request Data (Form): {token_data}")
        print(f"Response: {response.text}")
        return None
    
    result = response.json()
    
    # Check for errors in response
    if platform == 'slack' and not result.get('ok'):
        print(f"Slack token exchange error: {result.get('error')}")
        return None
    elif 'error' in result:
        print(f"Token exchange error for {platform}: {result.get('error')}")
        return None
    
    return result

def handle_callback_success(platform, user_info):
    """Handle successful OAuth callback"""
    from flask import redirect, render_template_string
    
    # 사용자 정보를 세션에 저장 (로그인이 되어있지 않은 경우)
    if not session.get('user_info') and user_info:
        session['user_info'] = {
            'email': user_info.get('email'),
            'name': user_info.get('name', user_info.get('display_name')),
            'platform': platform,
            'connected_at': datetime.utcnow().isoformat()
        }
    
    # 팝업 창에서 부모 창에 성공 메시지를 보내고 닫기
    popup_close_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Success</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                margin: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .success-message {
                text-align: center;
                padding: 40px;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }
            .checkmark {
                font-size: 48px;
                margin-bottom: 16px;
                animation: bounce 0.5s ease;
            }
            @keyframes bounce {
                0%, 20%, 60%, 100% { transform: translateY(0); }
                40% { transform: translateY(-10px); }
                80% { transform: translateY(-5px); }
            }
        </style>
    </head>
    <body>
        <div class="success-message">
            <div class="checkmark">✅</div>
            <h2>{{ platform.title() }} 연결 완료!</h2>
            <p>창이 자동으로 닫힙니다...</p>
        </div>
        <script>
            // 부모 창에 성공 메시지 전송
            if (window.opener) {
                window.opener.postMessage({
                    type: 'oauth_success',
                    platform: '{{ platform }}',
                    message: '{{ platform.title() }} 계정이 성공적으로 연결되었습니다!'
                }, window.location.origin);
            }
            
            // 2초 후 창 닫기
            setTimeout(() => {
                window.close();
            }, 2000);
        </script>
    </body>
    </html>
    """
    
    return render_template_string(popup_close_html, platform=platform)

def handle_callback_error(error_message, platform=None):
    """Handle OAuth callback error"""
    from flask import render_template_string
    
    # 더 자세한 에러 로깅
    if platform:
        print(f"OAuth Error for {platform}: {error_message}")
    else:
        print(f"OAuth Error: {error_message}")
    
    error_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connection Failed</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: #f9fafb;
            }}
            .error {{
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                max-width: 400px;
                width: 90%;
            }}
            .error-icon {{
                width: 64px;
                height: 64px;
                margin: 0 auto 24px;
                background: linear-gradient(135deg, #ef4444, #dc2626);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 28px;
                font-weight: bold;
            }}
            .error-title {{
                margin: 0 0 8px;
                color: #111827;
                font-size: 24px;
                font-weight: 600;
            }}
            .error-subtitle {{
                margin: 0 0 16px;
                color: #6b7280;
                font-size: 16px;
            }}
            .error-details {{
                margin: 20px 0;
                padding: 16px;
                background: #fef2f2;
                border-radius: 8px;
                font-size: 14px;
                color: #991b1b;
                border: 1px solid #fecaca;
                word-break: break-word;
            }}
            .close-info {{
                margin-top: 24px;
                font-size: 14px;
                color: #6b7280;
            }}
        </style>
        <script>
            // Notify parent window of error
            if (window.opener && !window.opener.closed) {{
                window.opener.postMessage({{
                    type: 'oauth_error',
                    platform: '{platform}',
                    error: '{error_message}',
                    timestamp: new Date().toISOString()
                }}, '*');
            }}
            
            // Auto-close after delay
            setTimeout(() => {{
                window.close();
            }}, 5000);
        </script>
    </head>
    <body>
        <div class="error">
            <div class="error-icon">✗</div>
            <h1 class="error-title">Connection Failed</h1>
            <p class="error-subtitle">Unable to connect your account.</p>
            <div class="error-details">
                {{ error_message }}
            </div>
            <div class="close-info">
                This window will close automatically in 5 seconds.
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(error_html, error_message=error_message, platform=platform or 'unknown')

@oauth_bp.route('/<platform>/check')
def check_oauth_config(platform):
    """Check if OAuth is configured for a platform"""
    if platform not in OAUTH_CONFIG:
        return jsonify({'configured': False, 'error': 'Unsupported platform'})
    
    config = OAUTH_CONFIG[platform]
    
    # Check required configuration
    if platform == 'apple':
        required_fields = ['client_id', 'team_id', 'key_id', 'private_key']
        configured = all(config.get(field) and config[field] != f'your_{platform}_{field}_here' for field in required_fields)
    else:
        required_fields = ['client_id', 'client_secret']
        configured = all(config.get(field) and config[field] != f'your_{platform}_{field}_here' for field in required_fields)
    
    return jsonify({
        'configured': configured,
        'platform': platform,
        'missing_fields': [field for field in required_fields if not config.get(field) or config[field] == f'your_{platform}_{field}_here']
    })

@oauth_bp.route('/slack/authorize')
def slack_authorize():
    """Initiate Slack OAuth flow"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    config = OAUTH_CONFIG['slack']
    state = secrets.token_urlsafe(32)
    
    # Store state for verification
    if not store_oauth_state(user_id, 'slack', state):
        return jsonify({'error': 'Failed to initiate OAuth flow'}), 500
    
    params = {
        'client_id': config['client_id'],
        'scope': config['scope'],
        'user_scope': config['user_scope'],
        'state': state,
        'redirect_uri': url_for('oauth.slack_callback', _external=True)
    }
    
    auth_url = f"{config['authorize_url']}?{urlencode(params)}"
    return redirect(auth_url)

@oauth_bp.route('/slack/callback')
def slack_callback():
    """Handle Slack OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return redirect(f'/setup/slack?error={error}')
    
    if not code or not state:
        return redirect('/setup/slack?error=missing_params')
    
    # Verify state
    state_data = verify_oauth_state(state, 'slack')
    if not state_data:
        return redirect('/setup/slack?error=invalid_state')
    
    config = OAUTH_CONFIG['slack']
    
    # Exchange code for tokens
    try:
        response = requests.post(config['token_url'], data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': url_for('oauth.slack_callback', _external=True)
        })
        
        token_data = response.json()
        
        if not token_data.get('ok'):
            return redirect(f'/dashboard?oauth_error={token_data.get("error", "token_exchange_failed")}')
        
        # Skip platform registration to match regular login behavior
        print(f"Skipping Slack platform registration to match regular login flow")
        success = True
        
        if success:
            # Track platform connection event
            sync_tracker.track_sync_event(
                user_id=state_data['user_id'],
                event_type=EventType.PLATFORM_CONNECTED,
                platform='slack',
                status='success',
                metadata={
                    'team_name': token_data.get('team', {}).get('name'),
                    'team_id': token_data.get('team', {}).get('id'),
                    'connection_method': 'oauth'
                }
            )
            
            # Clean up OAuth state
            supabase.table('oauth_states').delete().eq('state', state).execute()
            return redirect('/dashboard?oauth_success=slack')
        else:
            return redirect('/dashboard?oauth_error=registration_failed')
        
    except Exception as e:
        print(f"Slack OAuth error: {e}")
        return redirect('/dashboard?oauth_error=token_exchange_error')

@oauth_bp.route('/outlook/authorize')
def outlook_authorize():
    """Initiate Outlook OAuth flow with PKCE"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    config = OAUTH_CONFIG['outlook']
    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce_codes()
    
    # Store state and code verifier
    if not store_oauth_state(user_id, 'outlook', state, code_verifier):
        return jsonify({'error': 'Failed to initiate OAuth flow'}), 500
    
    auth_url = config['authorize_url'].format(tenant=config['tenant_id'])
    params = {
        'client_id': config['client_id'],
        'response_type': 'code',
        'redirect_uri': url_for('oauth.outlook_callback', _external=True),
        'response_mode': 'query',
        'scope': config['scope'],
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    return redirect(f"{auth_url}?{urlencode(params)}")

@oauth_bp.route('/outlook/callback')
def outlook_callback():
    """Handle Outlook OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return redirect(f'/setup/outlook?error={error}')
    
    if not code or not state:
        return redirect('/setup/outlook?error=missing_params')
    
    # Verify state and get code verifier
    state_data = verify_oauth_state(state, 'outlook')
    if not state_data:
        return redirect('/setup/outlook?error=invalid_state')
    
    config = OAUTH_CONFIG['outlook']
    token_url = config['token_url'].format(tenant=config['tenant_id'])
    
    # Exchange code for tokens
    try:
        response = requests.post(token_url, data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': url_for('oauth.outlook_callback', _external=True),
            'grant_type': 'authorization_code',
            'code_verifier': state_data['code_verifier']
        })
        
        token_data = response.json()
        
        if 'error' in token_data:
            return redirect(f'/dashboard?oauth_error={token_data.get("error")}')
        
        # Skip platform registration to match regular login behavior
        print(f"Skipping Outlook platform registration to match regular login flow")
        success = True
        
        if success:
            # Track platform connection event
            sync_tracker.track_sync_event(
                user_id=state_data['user_id'],
                event_type=EventType.PLATFORM_CONNECTED,
                platform='outlook',
                status='success',
                metadata={
                    'user_email': get_platform_user_email('outlook', user_info),
                    'user_name': get_platform_user_name('outlook', user_info),
                    'connection_method': 'oauth'
                }
            )
            
            # Clean up OAuth state
            supabase.table('oauth_states').delete().eq('state', state).execute()
            return redirect('/dashboard?oauth_success=outlook')
        else:
            return redirect('/dashboard?oauth_error=registration_failed')
        
    except Exception as e:
        print(f"Outlook OAuth error: {e}")
        return redirect('/dashboard?oauth_error=token_exchange_error')

@oauth_bp.route('/refresh/<platform>')
def refresh_token(platform):
    """Refresh OAuth tokens for a platform"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if platform not in OAUTH_CONFIG:
        return jsonify({'error': 'Invalid platform'}), 400
    
    # Slack tokens don't expire, skip refresh
    if platform == 'slack':
        return jsonify({'success': True, 'message': 'Slack tokens do not expire'})
    
    try:
        # Get current registration
        result = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('platform', platform).single().execute()
        if not result.data:
            return jsonify({'error': 'No platform registration found'}), 404
        
        # Decrypt credentials
        credentials = json.loads(result.data['encrypted_credentials'])
        refresh_token_value = credentials.get('refresh_token')
        
        if not refresh_token_value:
            return jsonify({'error': 'No refresh token available'}), 400
        
        config = OAUTH_CONFIG[platform]
        token_url = config['token_url']
        
        if platform == 'outlook':
            token_url = token_url.format(tenant=config.get('tenant_id', 'common'))
        
        # Request new tokens
        response = requests.post(token_url, data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'refresh_token': refresh_token_value,
            'grant_type': 'refresh_token'
        })
        
        token_data = response.json()
        
        if 'error' in token_data:
            return jsonify({'error': token_data.get('error_description', 'Token refresh failed')}), 400
        
        # Update credentials
        expires_in = token_data.get('expires_in', 3600)
        expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        
        updated_credentials = {
            **credentials,
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token', refresh_token_value),
            'expires_at': expires_at
        }
        
        # Update registration
        supabase.table('registered_platforms').update({
            'encrypted_credentials': json.dumps(updated_credentials),
            'expires_at': expires_at,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).eq('platform', platform).execute()
        
        return jsonify({'success': True, 'expires_at': expires_at})
        
    except Exception as e:
        print(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500

@oauth_bp.route('/disconnect/<platform>')
def disconnect_platform(platform):
    """Disconnect a platform OAuth connection"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Delete platform registration
        supabase.table('registered_platforms').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Delete platform connections
        supabase.table('platform_connections').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Clean up calendar connections
        supabase.table('calendar_connections').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Clean up sync settings
        supabase.table('sync_settings').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        return jsonify({'success': True, 'message': f'{platform.title()} disconnected successfully'})
        
    except Exception as e:
        print(f"Disconnect error: {e}")
        return jsonify({'error': 'Failed to disconnect'}), 500

@oauth_bp.route('/status')
def oauth_status():
    """Get OAuth status for all platforms"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200
    
    try:
        # Get all platform registrations for user
        result = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('is_active', True).execute()
        
        platforms = {}
        for registration in result.data:
            platform = registration['platform']
            platforms[platform] = {
                'registered': True,
                'platform_name': registration.get('platform_name'),
                'user_name': registration.get('platform_user_name'),
                'user_email': registration.get('platform_user_email'),
                'expires_at': registration.get('expires_at'),
                'created_at': registration.get('created_at')
            }
        
        return jsonify({
            'authenticated': True,
            'user_id': user_id,
            'platforms': platforms,
            'total_registered': len(platforms)
        })
        
    except Exception as e:
        print(f"OAuth status error: {e}")
        return jsonify({'authenticated': False, 'error': str(e)}), 500

@oauth_bp.route('/cleanup')
def cleanup_oauth_states_route():
    """Endpoint to manually trigger cleanup of expired OAuth states"""
    try:
        # Clean up expired states
        current_time = datetime.utcnow().isoformat()
        result = supabase.table('oauth_states').delete().lt('expires_at', current_time).execute()
        
        cleaned_count = len(result.data) if result.data else 0
        
        # Also clean up states older than 1 hour regardless of expires_at
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        old_result = supabase.table('oauth_states').delete().lt('created_at', one_hour_ago).execute()
        
        old_cleaned_count = len(old_result.data) if old_result.data else 0
        total_cleaned = cleaned_count + old_cleaned_count
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {total_cleaned} expired OAuth states',
            'expired_states_cleaned': cleaned_count,
            'old_states_cleaned': old_cleaned_count,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error in OAuth cleanup: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/health')
def oauth_health_check():
    """Health check endpoint to verify OAuth system and database connectivity"""
    try:
        health_status = {
            'oauth_system': 'healthy',
            'database_connection': 'unknown',
            'oauth_states_table': 'unknown',
            'registered_platforms_table': 'unknown',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Test database connection by querying oauth_states table
        try:
            # Count states in the table (limit 1 for performance)
            states_result = supabase.table('oauth_states').select('id', count='exact').limit(1).execute()
            health_status['database_connection'] = 'connected'
            health_status['oauth_states_table'] = 'accessible'
            
            # Get count of current states
            if hasattr(states_result, 'count'):
                health_status['current_oauth_states'] = states_result.count
            
        except Exception as db_error:
            health_status['database_connection'] = 'error'
            health_status['oauth_states_table'] = f'error: {str(db_error)}'
        
        # Test registered_platforms table
        try:
            platforms_result = supabase.table('registered_platforms').select('id', count='exact').limit(1).execute()
            health_status['registered_platforms_table'] = 'accessible'
            
            if hasattr(platforms_result, 'count'):
                health_status['registered_platforms_count'] = platforms_result.count
                
        except Exception as platform_error:
            health_status['registered_platforms_table'] = f'error: {str(platform_error)}'
        
        # Check OAuth provider configurations
        configured_providers = []
        for provider, config in OAUTH_CONFIG.items():
            if provider == 'apple':
                # Apple uses JWT, check for team_id and key_id
                if config.get('team_id') and config.get('key_id'):
                    configured_providers.append(provider)
            else:
                # Other providers need client_id and client_secret
                if config.get('client_id') and config.get('client_secret'):
                    configured_providers.append(provider)
        
        health_status['configured_providers'] = configured_providers
        health_status['total_providers_configured'] = len(configured_providers)
        
        # Determine overall health
        is_healthy = (
            health_status['database_connection'] == 'connected' and
            health_status['oauth_states_table'] == 'accessible' and
            len(configured_providers) > 0
        )
        
        status_code = 200 if is_healthy else 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        print(f"Error in OAuth health check: {e}")
        return jsonify({
            'oauth_system': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500